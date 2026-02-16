from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.schemas import ReviewRequest, AnalysisResponse, ProductScoreRequest
from shared.config.database import get_db
from backend.services.crawler import CrawlerService
from backend.services.llm import LLMService
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["api"])

@router.post("/predict", response_model=AnalysisResponse)
async def predict(request: ReviewRequest):
    # 调用 LLMService 进行单条分析
    result = LLMService.analyze_single_text(request.content)
    
    return {
        "is_fake": result["is_fake"],
        "label": result["label"],
        "confidence": result["confidence"],
        "sentiment_score": result["sentiment_score"],
        "analysis": result["analysis"]
    }

@router.post("/task/start")
def start_task(request: ProductScoreRequest, db: Session = Depends(get_db)):
    """
    第一步：启动爬虫任务，返回 task_id
    """
    try:
        task_id = CrawlerService.start_crawl_task(request.product_url, db)
        return {"task_id": task_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")

# 新增：模糊搜索商品
@router.get("/stats/search")
def search_products(keyword: str, db: Session = Depends(get_db)):
    if not keyword:
        return []
    
    # 模糊搜索 product 字段
    products = db.query(ProductStats.task_id, ProductStats.product, ProductStats.created_at)\
        .filter(ProductStats.product.like(f"%{keyword}%"))\
        .order_by(ProductStats.created_at.desc())\
        .limit(10)\
        .all()
        
    return [
        {
            "id": p.task_id, # 统一使用 task_id 作为 id
            "name": p.product,
            "date": p.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } 
        for p in products
    ]

# 新增：获取大屏详情数据
@router.get("/stats/detail/{task_id}")
def get_stats_detail(task_id: int, db: Session = Depends(get_db)):
    stats = db.query(ProductStats).filter(ProductStats.task_id == task_id).first()
    if not stats:
        raise HTTPException(status_code=404, detail="未找到该商品统计数据")
        
    return {
        "product_name": stats.product,
        "product_url": stats.product_url,
        "created_at": stats.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "total_reviews": stats.total_reviews,
        "fake_count": stats.fake_count,
        "real_count": stats.total_reviews - stats.fake_count,
        "trust_score": round(float(stats.confidence or 0) * 100, 1),
        "sentiment_score": float(stats.sentiment_score or 0),
        "positive_count": stats.positive_reviews_count,
        "neutral_count": stats.neutral_reviews_count,
        "negative_count": stats.negative_reviews_count
    }

from shared.constants.messages import Messages
from shared.constants.status_codes import BusinessCode

@router.get("/task/status/{task_id}")
def check_status(task_id: int, db: Session = Depends(get_db)):
    """
    第二步：轮询任务状态
    返回: status (0-失败, 1-爬虫进行中, 2-爬虫完成/分析中, 3-分析完成)
    """
    # 1. 检查爬虫状态
    crawler_status = CrawlerService.check_task_status(task_id)
    
    if crawler_status == 0:
        return {"status": 0, "message": Messages.CRAWLER_BUSY} # 这里可能需要更具体的爬虫错误
    
    if crawler_status == 1:
        return {"status": 1, "message": "正在抓取评论数据..."}
    
    # 2. 如果爬虫完成 (status=2)，触发/检查 LLM 分析
    try:
        is_finished = LLMService.analyze_task(task_id, db)
        if is_finished:
            return {"status": 3, "message": Messages.SUCCESS}
        else:
            return {"status": 2, "message": "正在进行 AI 分析..."}
    except Exception as e:
        # 将具体的错误信息返回给前端，而不是笼统的 "Analysis failed"
        error_msg = str(e)
        # 如果是数据库字段错误，给一个更友好的提示
        if "Unknown column" in error_msg:
            error_msg = "数据库结构不匹配，请联系管理员更新数据库表结构"
        
        return {"status": 0, "message": f"{Messages.ANALYSIS_FAILED}: {error_msg}"}

from backend.models.sql_models import ProductStats

from backend.services.stats import StatsService

@router.get("/task/result/{task_id}")
def get_result(task_id: int, db: Session = Depends(get_db)):
    """
    第三步：获取最终结果
    """
    # 1. 尝试从数据库查询统计结果
    stats = db.query(ProductStats).filter(ProductStats.task_id == task_id).first()
    
    # 2. 如果没有统计结果 (可能是首次请求，或者统计逻辑未触发)，尝试实时计算
    if not stats:
        stats = StatsService.calculate_stats(task_id, db)
    
    if not stats:
        # 如果计算后还是没有 (比如该任务根本没有评论数据)
        raise HTTPException(status_code=404, detail=Messages.DATA_NOT_FOUND)
    
    return {
        "task_id": task_id,
        "trust_score": round(float(stats.confidence or 0) * 100, 1),
        "total_reviews": stats.total_reviews,
        "fake_ratio": stats.fake_ratio,
        "fake_count": stats.fake_count,
        "product_name": stats.product,
        "sentiment_score": float(stats.sentiment_score or 0),
        "positive_count": stats.positive_reviews_count,
        "negative_count": stats.negative_reviews_count,
        "neutral_count": stats.neutral_reviews_count
    }

@router.get("/stats", response_model=None)
async def get_stats(product_id: Optional[str] = None, chart_type: str = "all"):
    # 模拟仪表盘数据
    overview_data = [
        {"value": 78, "name": "真实评论"},
        {"value": 22, "name": "疑似虚假"}
    ]
    
    trend_data = {
        "dates": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
        "values": [120, 132, 101, 134, 90, 230, 210]
    }

    if product_id:
        # 如果指定了商品ID，返回特定商品的数据（模拟）
        overview_data = [
            {"value": 90, "name": "真实评论"},
            {"value": 10, "name": "疑似虚假"}
        ]
        trend_data["values"] = [50, 60, 45, 80, 70, 90, 100]

    return {
        "overview": overview_data,
        "trend": trend_data
    }
