
class DateFormat:
    DATETIME_STANDARD = "%Y-%m-%d %H:%M:%S"
    DATE_STANDARD = "%Y-%m-%d"
    TIME_STANDARD = "%H:%M:%S"
    
    # 紧凑格式，常用于文件名
    DATETIME_COMPACT = "%Y%m%d%H%M%S"

class FileFormat:
    JSON = ".json"
    CSV = ".csv"
    TXT = ".txt"
    MODEL = ".pkl"

class Platform:
    """电商平台标识"""
    TAOBAO = "taobao"
    JD = "jd"
    PDD = "pdd"
    UNKNOWN = "unknown"
