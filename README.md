# FakeReviewGuard - 电商评论可信度分析工具

## 🎯 项目简介

FakeReviewGuard 是一款专为电商平台设计的智能评论可信度分析工具。它通过规则与轻量AI模型，对商品评论进行真实性分析，并生成可解释的商品信誉评分，帮助消费者识别虚假评论，提升购物决策质量。

## ✨ 核心功能

- **📊 评论数据采集与处理** - 自动爬取电商平台商品评论
- **😊 评论情绪分析** - 智能判断评论情感倾向（正/中/负）
- **🔍 虚假评论识别** - 识别可疑的虚假评论
- **⭐ 商品信誉评分体系** - 独创的信誉评分算法
- **📈 图形化可视化展示** - 直观的数据图表展示

## 🛠️ 技术架构

### 后端技术栈
- **核心框架**: FastAPI
- **Python版本**: 3.10
- **数据处理**: pandas, numpy
- **NLP处理**: jieba, snownlp, scikit-learn
- **机器学习**: scikit-learn (朴素贝叶斯/SVM)
- **深度学习**: transformers
- **数据存储**: MySQL 5.7
- **ORM**: SQLAlchemy

### 前端技术栈
- **基础**: HTML + JavaScript + CSS
- **图表库**: ECharts
- **UI框架**: Bootstrap
- **HTTP客户端**: Fetch API

### 爬虫技术栈
- **爬虫框架**: Scrapy / requests + BeautifulSoup
- **数据解析**: parsel / lxml
- **反爬处理**: 随机User-Agent / IP代理池

## 🚀 快速开始

### 环境配置

#### 1. 数据库配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置数据库连接
# 格式：mysql+pymysql://user:password@host:port/dbname
# 示例：mysql+pymysql://root:123456@localhost:3306/fake_review_guard
```

#### 2. 创建虚拟环境
```bash
# 创建虚拟环境
python -3.10 venv .venv
source venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 安装依赖
python -m pip install -r requirements.txt
```

#### 3. 数据库初始化
```bash
cd backend
python init_db.py
```

### 启动服务
```bash
# 启动后端服务
cd backend
python main.py

# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 查看应用。

## 📁 项目结构

```
FakeReviewGuard/
├── backend/                 # 后端服务
│   ├── app/                # FastAPI应用
│   ├── models/             # 数据库模型
│   ├── services/           # 业务逻辑
│   ├── routers/            # API路由
│   └── main.py             # 启动文件
├── frontend/                # 前端界面
│   ├── static/             # 静态资源
│   ├── templates/          # HTML模板
│   ├── js/                 # JavaScript文件
│   └── css/                # 样式文件
├── crawler/                 # 爬虫模块
│   ├── spiders/            # 爬虫脚本
│   ├── pipelines/          # 数据处理管道
│   └── items/              # 数据模型
├── ml_models/              # 机器学习模型
│   ├── training/           # 模型训练脚本
│   ├── evaluation/         # 模型评估
│   └── models/             # 预训练模型文件
├── shared/                  # 共享工具
│   ├── config/             # 配置
│   ├── constants/          # 常量
│   └── utils/              # 工具函数
├── docs/                    # 文档目录
├── tests/                   # 测试代码
└── requirements.txt         # Python依赖
```

## � 数据格式

### 评论数据格式
```json
{
    "id": "1",
    "task_id": "1001",
    "original_comment_id": "123",
    "product": "商品名",
    "extract": "评论内容",
    "score": 5,
    "source": "评论来源",
    "comment_time": "2025-01-01 10:00:00"
}
```

### 分析结果格式
```json
{
    "sentiment": "正面",
    "sentiment_score": 0.85,
    "is_fake": false,
    "fake_score": 0.15,
    "analysis_time": "2025-01-01 10:01:00"
}
```

## 🧪 性能指标

- **情绪分析准确率**: > 80%
- **虚假评论识别准确率**: > 75%
- **API响应时间**: < 500ms
- **并发处理能力**: 支持10个并发请求
- **内存使用**: < 500MB
- **可视化加载时间**: < 2秒

## �️ 安全特性

- 输入数据验证与清洗
- SQL注入防护
- XSS攻击防护
- 敏感信息脱敏
- 日志安全记录

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## � 团队成员

- **项目负责人**: zgj6017
- **后端&可视化负责人**: taciturn-hg
- **模型训练负责人**: zgj6017、chen-zi-4
- **爬虫负责人**: xiaodengyou
- **文档&PPT负责人**: slt

## 📞 联系方式

如有问题或建议，请通过 GitHub Issues 提交。

---

**⭐ 如果这个项目对你有帮助，请给它一个星标！**