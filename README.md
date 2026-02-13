# FakeReviewGuard 开发规范文档

## 📋 文档信息
- **项目名称**: FakeReviewGuard - 电商评论可信度分析工具
- **文档版本**: v1.0
- **创建日期**: 2025-02-12
- **适用阶段**: 三创赛开发全流程

## 🎯 项目概述

FakeReviewGuard 是一个面向电商场景的智能评论可信度分析工具，定位为可嵌入式插件系统。项目核心在于通过规则与轻量AI模型，对商品评论进行真实性分析，并生成可解释的商品信誉评分。

### 核心功能模块
1. 评论数据采集与处理
2. 评论情绪分析（正/中/负）
3. 虚假评论识别（正常/疑似虚假）
4. 商品信誉评分体系（原创）
5. 图形化可视化展示

## 🛠️ 技术栈规范

### 后端技术栈
```
核心框架: FastAPI
Python版本: 3.10
数据处理: pandas, numpy
NLP处理: jieba, snownlp, scikit-learn
机器学习: scikit-learn (朴素贝叶斯/SVM)
深度学习: transformers (BERT, 可选)
数据存储: CSV (阶段1-2) / MySQL (阶段3+)
数据库: MySQL 5.7
ORM: SQLAlchemy
```

### 前端技术栈
```
基础: HTML + JavaScript + CSS
图表库: ECharts
UI框架: Bootstrap (可选)
HTTP客户端: Axios / Fetch API
包管理: npm (package.json)
```

### 爬虫技术栈
```
爬虫框架: Scrapy / requests + BeautifulSoup
数据解析: parsel / lxml
反爬处理: 随机User-Agent / IP代理池
数据存储: MySQL / CSV
```

### 工具链
```
包管理: pip (requirements.txt)
版本控制: Git
代码规范: PEP 8
接口测试: Postman
开发环境: pycharm
数据库工具: Navicat
```

## 📁 项目结构规范

```
FakeReviewGuard/
├── backend/                 # 后端服务（系统实现&可视化负责）
│   ├── app/                # FastAPI应用
│   ├── models/             # 数据库模型
│   ├── services/           # 业务逻辑
│   ├── routers/            # API路由
│   ├── utils/              # 工具函数
│   └── main.py             # 启动文件
├── frontend/                # 前端界面（系统实现&可视化负责）
│   ├── static/             # 静态资源
│   ├── templates/          # HTML模板
│   ├── js/                 # JavaScript文件
│   └── css/                # 样式文件
├── crawler/                 # 爬虫模块（爬虫组负责）
│   ├── spiders/            # 爬虫脚本
│   ├── pipelines/          # 数据处理管道
│   ├── items/              # 数据模型
│   └── settings.py         # 爬虫配置
├── ml_models/              # 机器学习模型（模型训练组负责）
│   ├── training/           # 模型训练脚本
│   ├── evaluation/         # 模型评估
│   ├── models/             # 预训练模型文件
│   └── features/           # 特征工程
├── data/                    # 数据目录（数据工程负责）
│   ├── raw/                # 原始数据
│   ├── processed/          # 清洗后数据
│   └── output/             # 分析结果输出
├── shared/                  # 共享工具（公共模块）
│   ├── config/             # 数据库、API、模型路径等配置
│   ├── constants/          # 数据格式、状态码、错误信息等常量
│   └── utils/              # 通用的文本处理、数据验证、日志等工具函数
├── docs/                    # 文档目录
│   └── database/               # 数据库文档
│       ├── schema.sql         # 建表SQL
│       └── ERD.png 
├── tests/                   # 测试代码
├── requirements.txt         # Python依赖
├── README.md               # 项目说明
└── .gitignore              # Git忽略文件
```

## 📝 代码规范

### Python代码规范
1. **命名规范**
   - 模块/包名: `lowercase_with_underscores`
   - 类名: `CapitalizedWords`
   - 函数/变量: `lowercase_with_underscores`
   - 常量: `UPPERCASE_WITH_UNDERSCORES`

2. **代码格式**
   ```python
   # 函数注释
   def analyze_sentiment(text):
       """
       分析评论情感倾向
       
       Args:
           text: 评论文本内容
           
       Returns:
           str: '正面'/'中性'/'负面'
       """
       # 实现代码
       pass
   ```

3. **异常处理**
   ```python
   try:
       result = analyze_comment(comment)
   except Exception as e:
       logger.error(f"分析失败: {str(e)}")
       result = {"sentiment": "中性", "is_fake": False}
   ```

### JavaScript代码规范
1. **命名规范**
   - 变量/函数: `camelCase`
   - 常量: `UPPER_CASE`
   - 类名: `PascalCase`

2. **异步处理**
   ```javascript
   async function fetchAnalysis(comment) {
       try {
           const response = await fetch('/api/predict', {
               method: 'POST',
               headers: {'Content-Type': 'application/json'},
               body: JSON.stringify({content: comment})
           });
           return await response.json();
       } catch (error) {
           console.error('分析失败:', error);
           return {sentiment: '中性', is_fake: false};
       }
   }
   ```

## 🔄 开发流程规范

### Git分支策略
```
main: 主分支，稳定版本
dev: 开发分支，集成测试
feature/xxx: 功能分支
```

### 开发流程
1. **需求分析**: 明确功能需求和交付标准
2. **分支创建**: 从dev创建feature分支
3. **功能开发**: 按模块开发，保持提交频率
4. **代码审查**: 提交前自查，关键功能交叉审查
5. **测试验证**: 单元测试 + 集成测试
6. **合并上线**: 合并到dev，稳定后合并到main

### 提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具相关
```

## 🧪 测试规范

### 测试分层
1. **单元测试**: 函数/模块级别
2. **集成测试**: API接口级别
3. **端到端测试**: 完整流程测试

### 测试要求
```python
# 示例：情绪分析测试
def test_sentiment_analysis():
    test_cases = [
        ("这个产品真的很好用", "正面"),
        ("质量一般般", "中性"),
        ("太差了，不推荐", "负面")
    ]
    
    for text, expected in test_cases:
        result = analyze_sentiment(text)
        assert result == expected, f"测试失败: {text}"
```

## 📊 数据规范

### 数据格式标准
```python
# 评论数据格式
{
    "id": "12345",
    "product": "商品名",
    "extract": "评论内容",
    "score": 5,
    "source": "评论来源",
    "time": "2025-01-01 10:00:00"
}

# 分析结果格式
{
    "sentiment": "正面",      # 正面/中性/负面
    "sentiment_score": 0.85,  # 情感置信度
    "is_fake": false,         # 是否疑似虚假
    "fake_score": 0.15,      # 虚假置信度
    "analysis_time": "2025-01-01 10:01:00"
}
```

### 数据质量要求
1. **完整性**: 必填字段不能缺失
2. **一致性**: 数据格式统一
3. **准确性**: 清洗后数据准确率 > 95%
4. **时效性**: 分析结果实时更新

## 🚀 部署规范

### 环境配置
```bash
# 创建虚拟环境
python -3.10 venv .venv
source venv/bin/activate  # Linux/Mac
.venv\Scripts\activate       # Windows

# 安装依赖
pip install -r requirements.txt
```

### 服务启动
```bash
# 开发环境
python app.py

# 生产环境
uvicorn main:app --reload
```

### 性能要求
- API响应时间: < 500ms
- 并发处理能力: 支持10个并发请求
- 内存使用: < 500MB
- 可视化加载时间: < 2秒

## 📋 交付标准

### 阶段1交付 (第1-5天)
- ✅ 数据清洗脚本
- ✅ 情绪分析模型
- ✅ 虚假评论识别模型
- ✅ 单条评论分析API
- ✅ 测试用例和结果

### 阶段2交付 (第6-10天)
- ✅ 商品信誉评分公式
- ✅ 批量分析脚本
- ✅ 评分体系文档
- ✅ 结果可视化脚本

### 阶段3交付 (第11-15天)
- ✅ 完整后端服务
- ✅ 可视化界面
- ✅ 演示Demo
- ✅ 部署文档

### 阶段4交付 (第16-20天)
- ✅ 最终PPT
- ✅ 演示脚本
- ✅ 项目文档
- ✅ 代码仓库

## 🎯 质量目标

### 技术指标
- 情绪分析准确率: > 80%
- 虚假评论识别准确率: > 75%
- 系统响应时间: < 1秒
- 可视化兼容性: Chrome/Firefox/Edge

### 演示指标
- Demo流畅度: 无卡顿
- 界面美观度: 简洁清晰
- 功能完整性: 核心功能全覆盖
- 用户体验: 操作简单直观

## 📞 联系与支持

### 团队分工
- **项目负责人**: 周冠杰 (统筹全局，技术路线)
- **后端&可视化负责人**: 王许毅 (FastAPI + ECharts)
- **模型训练负责人**: 周冠杰、陈丽婷 (情绪分析 + 虚假识别)
- **爬虫负责人**: 滕林洋 (数据采集)
- **文档&PPT负责人**: 宋丽婷 (项目文档 + 路演)

### 技术对接
- **API接口**: 后端组统一提供
- **数据格式**: 共享模块定义标准
- **模型调用**: 通过shared模块集成
- **问题反馈**: 通过GitHub Issues提交

---

## 📄 附录

### A. 常用命令速查
```bash
# 环境配置
python -3.10 venv .venv
source venv/bin/activate  # Linux/Mac
.venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 数据库初始化
cd backend && python init_db.py

# 启动后端服务
cd backend && python main.py
# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 运行爬虫（爬虫组）
cd crawler && scrapy crawl product_reviews

# 训练模型（模型组）
cd ml_models && python training/train_sentiment.py

# 运行测试
python -m pytest tests/

# 数据清洗（数据工程）
python shared/utils/data_cleaner.py
```

### B. 常见问题FAQ
1. **Q: 数据量要求多少？**
   A: 阶段1-2建议3000-10000条，阶段3可适当增加

2. **Q: 必须使用BERT吗？**
   A: BERT为加分项，非必需，朴素贝叶斯足够

3. **Q: 前端必须用Vue吗？**
   A: 不需要，HTML+JS+ECharts完全够用

4. **Q: 模型准确率要求多高？**
   A: 情绪分析>80%，虚假识别>75%，重点是可解释性

5. **Q: MySQL数据库怎么配置？**
   A: 见backend/config/database.py，支持自动初始化

6. **Q: 各组之间如何协作？**
   A: 通过shared模块定义标准接口，API文档统一维护

---

**📌 重要提醒**: 本规范文档是项目成功的基石，请所有团队成员严格遵守。如有疑问，及时沟通解决。