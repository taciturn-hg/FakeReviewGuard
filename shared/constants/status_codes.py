
from enum import IntEnum

class HTTPStatus(IntEnum):
    """
    常用 HTTP 状态码
    """
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500

class BusinessCode(IntEnum):
    """
    业务状态码 (自定义)
    """
    SUCCESS = 0
    UNKNOWN_ERROR = 1000
    PARAM_ERROR = 1001
    DB_ERROR = 1002
    AUTH_ERROR = 1003
    DATA_NOT_FOUND = 1004
    ANALYSIS_FAILED = 2001
    MODEL_LOAD_ERROR = 2002
