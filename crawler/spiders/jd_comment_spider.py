import time
import random
import sys
import os

# 添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
# 回退两层: spiders -> crawler -> FakeReviewGuard
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import text
from DrissionPage import ChromiumPage
from shared.utils.init_db import init_tables_from_sql
from shared.utils.logger import logger

# 尝试导入数据库配置
try:
    from shared.config.database import get_db
except ImportError:
    get_db = None

class JDCommentSpider:
    def __init__(self, product_url, task_id=None):
        """
        初始化京东评论爬虫
        :param product_url: 商品详情页URL
        :param task_id: 关联的任务ID，如果不传则自动使用当前时间戳生成
        """
        self.product_url = product_url
        # 如果没有传入task_id，则使用当前时间戳（秒级整数）
        self.task_id = task_id if task_id else int(time.time())
        self.page = ChromiumPage()
        self.db_generator = None
        self.db = None
        self.status = 1 # 1: 进行中, 0: 报错, 2: 已完成
        
        # 初始化数据库连接
        if get_db:
            try:
                self.db_generator = get_db()
                self.db = next(self.db_generator)
                logger.info("数据库连接成功")
            except Exception as e:
                logger.error(f"数据库连接失败: {e}")
                self.status = 0
        else:
            logger.warning("未能导入 get_db，将仅打印数据而不入库")
        
        init_tables_from_sql()

    def start(self):
        """开始爬取流程"""
        try:
            logger.info(f"开始爬取: {self.product_url}, Task ID: {self.task_id}")
            self.page.get(self.product_url)
            self.page.listen.start('client.action')

            # 打开评论弹窗
            if not self._open_comment_dialog():
                logger.error("无法打开评论弹窗，爬取终止")
                self.status = 0
                return

            self._crawl_loop()
            # 正常结束
            self.status = 2

        except Exception as e:
            logger.error(f"爬虫运行异常: {e}")
            self.status = 0
        finally:
            self._close()

    def get_status(self):
        """获取爬虫当前状态"""
        return self.status

    def get_task_id(self):
        """获取任务ID"""
        return self.task_id

    def _open_comment_dialog(self):
        """点击查看全部评论并等待弹窗"""
        if self.page.ele('css:.all-btn'):
            self.page.ele('css:.all-btn').click()
            try:
                self.page.wait.ele_displayed('text:商品评价', timeout=5)
                time.sleep(1)
                return True
            except Exception:
                logger.warning("等待评论弹窗超时")
                return False
        logger.warning("未找到'查看全部评价'按钮")
        return False

    def _crawl_loop(self):
        """主爬取循环"""
        page_num = 1
        has_next = True
        
        while has_next:
            logger.info(f"正在获取第 {page_num} 页数据...")
            
            # 重新实现 _fetch_page_data 的逻辑以包含循环等待和状态判断
            got_data, has_next_page = self._process_page_data()
            
            if not got_data:
                logger.warning(f"第 {page_num} 页未获取到数据")
            
            if not has_next_page:
                logger.info("已达到最后一页")
                has_next = False
            else:
                page_num += 1
                time.sleep(random.uniform(1, 2))

    def _process_page_data(self):
        """
        触发加载并监听数据包
        :return: (bool: 是否获取到数据, bool: 是否有下一页)
        """
        got_data = False
        has_next = True
        timeout = 10
        start_time = time.time()

        # 触发加载
        self._trigger_loading()

        # 监听循环
        while time.time() - start_time < timeout:
            try:
                resp = self.page.listen.wait(timeout=2)
                if not resp:
                    continue

                res_json = resp.response.body
                
                # 解析数据
                comments_found, pagination_found, is_last_page = self._parse_and_save(res_json)
                
                if comments_found:
                    got_data = True
                
                if pagination_found:
                    if is_last_page:
                        has_next = False
                    # 只要找到了分页信息，本页的任务就算完成了一大半
                    # 如果同时也找到了评论，那就可以退出了
                    if comments_found:
                        break
                elif comments_found:
                    # 如果只找到了评论没找到分页信息，可能需要继续等，或者假设有下一页
                    break

            except Exception:
                pass
        
        return got_data, has_next

    def _trigger_loading(self):
        """在弹窗内滚动以触发加载"""
        dialog_title = self.page.ele('text:商品评价')
        if dialog_title:
            try:
                self.page.actions.move_to(dialog_title, offset_y=300).scroll(10000)
                time.sleep(0.5)
                self.page.actions.scroll(10000)
            except Exception:
                pass
        else:
            self.page.scroll.down(1000)

    def _parse_and_save(self, res_json):
        """
        解析JSON并入库
        :return: (found_comments, found_pagination, is_last_page)
        """
        found_comments = False
        found_pagination = False
        is_last_page = False

        if isinstance(res_json, dict) and 'result' in res_json:
            floors = res_json['result'].get('floors', [])
            for floor in floors:
                if not isinstance(floor, dict):
                    continue

                # 1. 提取评论
                if 'data' in floor and isinstance(floor['data'], list):
                    comment_list = floor['data']
                    if len(comment_list) > 0 and 'commentInfo' in comment_list[0]:
                        self._save_comments(comment_list)
                        found_comments = True

                # 2. 提取分页信息
                if 'data' in floor and isinstance(floor['data'], dict):
                    floor_data = floor['data']
                    if 'hasNextPage' in floor_data:
                        found_pagination = True
                        if floor_data['hasNextPage'] is False or str(floor_data['hasNextPage']).lower() == 'false':
                            is_last_page = True

        return found_comments, found_pagination, is_last_page

    def _save_comments(self, comment_list):
        """批量保存评论到数据库"""
        comments_to_insert = []
        for index in comment_list:
            try:
                comment_info = index.get('commentInfo', {})
                # 过滤无效数据：如果没有评论内容，视为无效
                if not comment_info or not comment_info.get('commentData'):
                    continue

                item = {
                    'task_id': self.task_id,
                    'original_comment_id': str(index.get('id', comment_info.get('commentId', ''))),
                    'product': comment_info.get('productSpecifications', ''),
                    'extract': comment_info.get('commentData', ''),
                    'score': int(comment_info.get('commentScore', 0)),
                    'source': '京东网页',
                    'comment_time': comment_info.get('commentDate', time.strftime("%Y-%m-%d %H:%M:%S")),
                }
                comments_to_insert.append(item)
                logger.debug(f"抓取: {item['extract'][:20]}...")
            except Exception:
                pass

        if comments_to_insert and self.db:
            try:
                self.db.execute(
                    text("""
                        INSERT INTO raw_comment 
                        (task_id, original_comment_id, product, extract, score, source, comment_time) 
                        VALUES (:task_id, :original_comment_id, :product, :extract, :score, :source, :comment_time)
                    """),
                    comments_to_insert
                )
                self.db.commit()
                logger.info(f"入库成功: {len(comments_to_insert)} 条")
            except Exception as e:
                self.db.rollback()
                logger.error(f"入库失败: {e}")

    def _close(self):
        """清理资源"""
        logger.info("爬虫结束，清理资源...")
        if self.db_generator:
            try:
                next(self.db_generator)
            except StopIteration:
                pass
        # self.page.quit() # 根据需要决定是否关闭浏览器

if __name__ == "__main__":
    # 示例运行
    url = 'https://item.jd.com/100015097018.html'
    spider = JDCommentSpider(url)
    spider.start()
