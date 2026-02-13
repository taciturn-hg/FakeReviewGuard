import re
from urllib.parse import urlparse

def is_valid_url(url: str) -> bool:
    """
    验证是否为有效的 URL
    """
    if not url:
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def is_supported_platform(url: str) -> str:
    """
    检查 URL 是否属于支持的电商平台，返回平台代码 (jd, taobao 等)
    返回 None 表示不支持
    """
    domain = urlparse(url).netloc
    
    if "jd.com" in domain:
        return "jd"
    elif "taobao.com" in domain or "tmall.com" in domain:
        return "taobao"
    elif "pinduoduo.com" in domain or "yangkeduo.com" in domain:
        return "pdd"
    
    return None
