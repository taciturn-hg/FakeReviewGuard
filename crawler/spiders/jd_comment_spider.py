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
from shared.utils.timer import ExecutionTimer

# 尝试导入数据库配置
try:
    from shared.config.database import get_db
except ImportError:
    get_db = None

class JDCommentSpider:
    def __init__(self, product_url, db=None, task_id=None):
        """
        初始化京东评论爬虫
        :param product_url: 商品详情页URL
        :param db: 数据库会话对象（可选，用于依赖注入）
        :param task_id: 关联的任务ID，如果不传则自动使用当前时间戳生成
        """
        self.product_url = product_url
        # 如果没有传入task_id，则使用当前时间戳（秒级整数）
        self.task_id = task_id if task_id else int(time.time())
        self.page = ChromiumPage()
        
        # 状态初始化
        self.status = 1 # 1: 进行中, 0: 报错, 2: 已完成
        self.db_generator = None
        self.db = None
        self.product_title = ""
        self.keep_browser_open = False

        # 数据库连接逻辑：优先使用传入的 db，否则尝试自动连接
        if db:
            self.db = db
            logger.info("使用传入的数据库连接")
        else:
            self._connect_to_db()
        
        logger.info(f"爬虫初始化完成，当前状态: {self.status}")

    def _connect_to_db(self):
        """初始化数据库连接（备用方案）"""
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

    def _handle_login_redirect(self):
        """处理登录跳转逻辑"""
        if "passport.jd.com" in self.page.url or "登录" in self.page.title:
            logger.warning("检测到需要登录，暂停运行。")
            logger.warning("请在浏览器中手动完成登录。")
            
            # 更新任务状态为 4 (未登录)，并重置 resume_signal 为 0
            self._update_task_status(4)
            if self.db:
                try:
                    self.db.execute(
                        text("UPDATE 00_crawler_tasks SET resume_signal = 0 WHERE task_id = :task_id"),
                        {"task_id": self.task_id}
                    )
                    self.db.commit()
                except Exception as e:
                    logger.error(f"重置 resume_signal 失败: {e}")
            
            # 阻塞等待数据库 resume_signal 变为 1 或用户控制台输入
            logger.info(f"等待用户登录... (当前任务状态: 4, 等待 resume_signal=1)")
            
            while True:
                time.sleep(2) # 轮询间隔
                
                # 1. 检查数据库 resume_signal 字段
                if self.db:
                    try:
                        # 每次查询前需要提交一次事务以获取最新数据
                        self.db.commit() 
                        result = self.db.execute(
                            text("SELECT resume_signal FROM 00_crawler_tasks WHERE task_id = :task_id"),
                            {"task_id": self.task_id}
                        ).fetchone()
                        
                        if result:
                            signal_val = result[0]
                            if signal_val == 2:
                                logger.info("检测到 resume_signal=2，停止爬虫任务...")
                                return 2
                            elif signal_val == 1:
                                logger.info("检测到 resume_signal=1，准备检查登录状态...")
                                
                                # 再次检测是否还在登录页面
                                if "passport.jd.com" in self.page.url:
                                    logger.warning("检测到 resume_signal=1，但页面仍处于登录页。重置 resume_signal=0 并继续等待...")
                                    # 重置 resume_signal 为 0，防止重复触发，并继续循环等待下一次信号
                                    try:
                                        self.db.execute(
                                            text("UPDATE 00_crawler_tasks SET resume_signal = 0 WHERE task_id = :task_id"),
                                            {"task_id": self.task_id}
                                        )
                                        self.db.commit()
                                    except Exception as e:
                                        logger.error(f"重置 resume_signal 失败: {e}")
                                    continue # 继续循环
                                else:
                                    logger.info("登录状态校验通过，准备恢复爬取...")
                                    # 将 resume_signal 重置为 0
                                    try:
                                        self.db.execute(
                                            text("UPDATE 00_crawler_tasks SET resume_signal = 0 WHERE task_id = :task_id"),
                                            {"task_id": self.task_id}
                                        )
                                        self.db.commit()
                                    except Exception as e:
                                        logger.error(f"恢复后重置 resume_signal 失败: {e}")
                                    break # 跳出循环，恢复爬虫
                                
                    except Exception as e:
                        logger.warning(f"轮询 resume_signal 失败: {e}")
                                
                    except Exception as e:
                        logger.warning(f"轮询 resume_signal 失败: {e}")

                # 2. 保留控制台输入作为备用方案
                # 注意：由于 input 是阻塞的，如果这里启用 input，上面的数据库轮询将无法工作。
                # 为了同时支持，这里仅使用数据库轮询。
                # 如果需要控制台支持，可以使用非阻塞输入库，但通常后端控制更为重要。
                # print("Waiting for resume_signal...", end='\r')
            
            # 恢复任务状态为 1 (进行中)
            self._update_task_status(1)
            
            # 恢复爬取流程
            logger.info("重启爬取流程...")
            self.page.get(self.product_url)
            self.start()
            return 1
        return 0

    def start(self):
        """开始爬取流程"""
        with ExecutionTimer(f"爬虫任务(TaskID: {self.task_id})"):
            try:
                # 1. 状态打点：开始 (Running)
                self._update_task_status(1)
                logger.info(f"开始爬取: {self.product_url}, Task ID: {self.task_id}")
                
                # 2. 访问页面 (先访问才能检测)
                self.page.get(self.product_url)
                
                # 3. 最早的登录检测点：页面加载完成后立即检查
                login_check = self._handle_login_redirect()
                if login_check == 2: # 停止爬虫
                    self._update_task_status(2)
                    return
                elif login_check == 1: # 恢复登录，不需要return，继续往下走
                    pass
                elif login_check == 0: # 无需登录，继续
                    pass
                    
                # 4. 开启监听，并刷新页面以触发数据包
                self.page.listen.start('functionId=pc_detailpage_wareBusiness')
                self.page.refresh() # 刷新以重新触发请求
                
                # 尝试获取商品标题
                for i in range(3):
                    try:
                        res = self.page.listen.wait(timeout=10)
                        if res:
                            data = res.response.body
                            self.product_title = data.get('skuHeadVO', {}).get('skuTitle', '')
                            logger.info(f"获取到商品标题: {self.product_title}")
                            break # 成功获取到标题，跳出循环
                        else:
                            logger.warning(f"未获取到商品标题数据包, 第{i+1}次尝试")
                    except Exception as e:
                        logger.warning(f"获取商品标题失败: {e}")
                
                # 2. 切换监听目标到评论数据包
                self.page.listen.start('client.action')

                # 打开评论弹窗
                # 优先检查是否跳转到了登录页面 (因为点击按钮可能会触发跳转)
                login_check = self._handle_login_redirect()
                if login_check == 2:
                    self._update_task_status(2)
                    return
                elif login_check == 1:
                    pass # 继续尝试打开评论


                # 尝试打开评论弹窗，如果失败且检测到登录页，立即进入等待
                is_dialog_opened = False
                try:
                    if self.page.ele('css:.all-btn'):
                        self.page.ele('css:.all-btn').click()
                        # 再次检测登录跳转
                        login_check = self._handle_login_redirect()
                        if login_check == 2:
                            self._update_task_status(2)
                            return
                        elif login_check == 1:
                            pass # 登录后继续等待弹窗
                            
                        self.page.wait.ele_displayed('text:商品评价', timeout=3)
                        is_dialog_opened = True
                except Exception:
                    pass

                # 再次检查是否跳转到了登录页面
                login_check = self._handle_login_redirect()
                if login_check == 2:
                    self._update_task_status(2)
                    return
                elif login_check == 1:
                    # 如果登录后弹窗没开，可能需要重新尝试打开
                    # 这里简单处理：如果恢复了，继续往下走，如果没有弹窗会触发后面的警告
                    pass

                if not is_dialog_opened:
                    logger.warning("未找到'查看全部评价'按钮或打开失败")
                    # 再次确认不是反爬拦截
                    if self.page.url.startswith("https://www.jd.com") or self.page.title == "京东(JD.COM)-正品低价、品质保障、配送及时、轻松购物！":
                        logger.warning("检测到被反爬拦截跳转至京东首页，尝试重启爬虫...")
                        self.page.quit()
                        time.sleep(random.uniform(5, 10)) # 等待一段时间
                        self.page = ChromiumPage() # 重启浏览器
                        # 递归调用自身重启
                        self.start()
                        return

                    logger.error("无法打开评论弹窗，爬取终止")
                    # 状态打点：失败 (Failed)
                    self._update_task_status(3)
                    logger.info(f"状态更新为: {self.status} (报错)")
                    return

                self._crawl_loop()
                # 正常结束
                # 状态打点：完成 (Success)
                self._update_task_status(2)
                logger.info(f"爬取任务完成，状态更新为: {self.status} (已完成)")

            except Exception as e:
                logger.error(f"爬虫运行异常: {e}")
                # 状态打点：失败 (Failed)
                self._update_task_status(3)
                logger.info(f"状态更新为: {self.status} (报错)")
            finally:
                self._close()

    def _update_task_status(self, status_code):
        """
        更新任务状态到数据库
        :param status_code: 0-等待, 1-进行中, 2-已完成, 3-失败
        """
        self.status = status_code
        if self.db:
            try:
                self.db.execute(
                    text("UPDATE 00_crawler_tasks SET status = :status WHERE task_id = :task_id"),
                    {"status": status_code, "task_id": self.task_id}
                )
                self.db.commit()
                logger.info(f"状态更新为: {self.status}")
            except Exception as e:
                logger.error(f"更新任务状态失败: {e}")
                self.db.rollback()

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
        consecutive_empty_pages = 0
        
        while has_next:
            logger.info(f"正在获取第 {page_num} 页数据...")
            
            # 重新实现 _fetch_page_data 的逻辑以包含循环等待和状态判断
            got_data, has_next_page = self._process_page_data()
            
            if page_num >= 20:
                logger.warning("已获取 20 页数据，停止继续获取")
                has_next = False
                break

            if not got_data:
                consecutive_empty_pages += 1
                logger.warning(f"第 {page_num} 页未获取到数据 (连续空页数: {consecutive_empty_pages})")
                if consecutive_empty_pages > 2:
                    logger.warning("连续超过 3 页未获取到数据，判定为爬取结束")
                    has_next = False
                    break
            else:
                consecutive_empty_pages = 0
            
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
            except Exception as e:
                logger.error(f"解析评论数据异常: {e}")

        if comments_to_insert and self.db:
            try:
                self.db.execute(
                    text("""
                        INSERT INTO 01_raw_comment 
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
                logger.info("数据库连接已关闭")
            except Exception as e:
                logger.error(f"关闭数据库连接异常: {e}")
        
        try:
            self.page.quit()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.warning(f"关闭浏览器失败: {e}")

if __name__ == "__main__":
    # 示例运行
    url = 'https://item.jd.com/100205107536.html?extension_id=eyJhZCI6IjY3OTQwIiwiY2giOiIyIiwic2t1IjoiMTAwMjA1MTA3NTM2IiwidHMiOiIxNzcxMDg1MzU0IiwidW5pcWlkIjoie1wiY2xpY2tfaWRcIjpcIjVmODY4YjIzLWU1YjgtNGNmNC1hMGM3LTY5NTE1OTgwNTUyOFwiLFwibWF0ZXJpYWxfaWRcIjpcIjkxNzg2MzA1NTc5MDM0NTkzODdcIixcInBvc19pZFwiOlwiNjc5NDBcIixcInNpZFwiOlwiNzI0YjA3ODYtNTIxYi00YTM3LWIyNzMtNGRiMDljYWQ4NGZkXCJ9In0%3D&jd_pop=5f868b23-e5b8-4cf4-a0c7-695159805528&abt=0'
    spider = JDCommentSpider(url)
    spider.start()
