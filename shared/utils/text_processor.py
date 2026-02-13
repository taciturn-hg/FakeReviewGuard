import re

def clean_text(text: str) -> str:
    """
    清洗评论文本：去除 HTML 标签、多余空格、特殊符号
    """
    if not text:
        return ""
    
    # 1. 去除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 2. 去除 URL
    # 简化正则，去除不必要的转义
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # 3. 去除多余空白 (换行、Tab 变为空格，且合并多个空格)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def truncate_text(text: str, max_length: int = 500) -> str:
    """
    截断文本，防止过长。确保返回的字符串长度不超过 max_length。
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # 边界情况：如果最大长度连省略号都放不下，直接硬截断
    if max_length <= 3:
        return text[:max_length]
        
    # 正常情况：预留 3 个字符给省略号
    return text[:max_length - 3] + "..."
