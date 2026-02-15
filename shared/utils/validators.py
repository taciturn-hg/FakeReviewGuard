from urllib.parse import urlparse

from typing import Optional

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

def is_supported_platform(url: str) -> Optional[str]:
    """
    检查 URL 是否属于支持的电商平台，返回平台代码 (jd, taobao 等)
    返回 None 表示不支持
    """
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return None
    
    # 定义平台域名规则 (主域名)
    platforms = {
        "jd": ["jd.com"],
        "taobao": ["taobao.com", "tmall.com"],
        "pdd": ["pinduoduo.com", "yangkeduo.com"]
    }

    for platform, hosts in platforms.items():
        for host in hosts:
            # 严格匹配：要么完全相等，要么是子域名（以 .host 结尾）
            if domain == host or domain.endswith(f".{host}"):
                return platform
    
    return None
