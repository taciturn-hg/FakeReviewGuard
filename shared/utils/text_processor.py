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
    # 使用更简单且通用的 URL 正则，匹配以 http/https 开头直到下一个空白符
    text = re.sub(r'https?://\S+', '', text)
    
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
