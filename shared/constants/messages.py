
# 通用错误信息
class Messages:
    SUCCESS = "操作成功"
    FAILED = "操作失败"
    
    # 参数/请求错误
    PARAM_ERROR = "请求参数错误"
    NOT_FOUND = "资源未找到"
    UNAUTHORIZED = "未授权访问"
    FORBIDDEN = "禁止访问"
    
    # 系统/数据库错误
    DB_CONNECT_ERROR = "数据库连接失败"
    DB_QUERY_ERROR = "数据库查询失败"
    INTERNAL_ERROR = "服务器内部错误"
    
    # 业务错误
    ANALYSIS_FAILED = "评论分析失败，请稍后重试"
    MODEL_NOT_READY = "AI 模型未就绪"
    CRAWLER_BUSY = "爬虫任务繁忙"
    
    @staticmethod
    def get(code: int) -> str:
        """根据业务码获取默认消息"""
        from .status_codes import BusinessCode
        
        mapping = {
            BusinessCode.SUCCESS: Messages.SUCCESS,
            BusinessCode.PARAM_ERROR: Messages.PARAM_ERROR,
            BusinessCode.DB_ERROR: Messages.DB_QUERY_ERROR,
            BusinessCode.AUTH_ERROR: Messages.UNAUTHORIZED,
            BusinessCode.DATA_NOT_FOUND: Messages.NOT_FOUND,
            BusinessCode.ANALYSIS_FAILED: Messages.ANALYSIS_FAILED,
            BusinessCode.MODEL_LOAD_ERROR: Messages.MODEL_NOT_READY,
        }
        try:
            business_code = BusinessCode(code)
        except ValueError:
            return Messages.INTERNAL_ERROR
        return mapping.get(business_code, Messages.INTERNAL_ERROR)
