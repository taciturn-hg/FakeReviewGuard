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
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # 3. 去除多余空白 (换行、Tab 变为空格，且合并多个空格)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def truncate_text(text: str, max_length: int = 500) -> str:
    """
    截断文本，防止过长
    """
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text
