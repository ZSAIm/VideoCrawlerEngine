
from helper.codetable import (
    PAGE_OUT_OF_RANGE,
    DATA_NOT_FOUND,
    DATA_EXISTS,
    VALIDATE_ERROR,
    UNAUTHORIZED_ERROR,
    TOKEN_EXPIRED,
    ACCESS_EXPIRED,
)


class APIBaseError(Exception):
    code: int

    def __init__(self, msg, data=None):
        self.msg = msg
        self.data = data or []


class PageOutOfRange(APIBaseError):
    code = PAGE_OUT_OF_RANGE


class DataExistsError(APIBaseError):
    code = DATA_EXISTS


class DataNotFound(APIBaseError):
    code = DATA_NOT_FOUND


class ValidateError(APIBaseError):
    code = VALIDATE_ERROR


class UnauthorizedError(APIBaseError):
    code = UNAUTHORIZED_ERROR


class TokenExpired(APIBaseError):
    code = TOKEN_EXPIRED


class AccessExpired(APIBaseError):
    code = ACCESS_EXPIRED


class RemoteApplyException(Exception):
    def __init__(self, key, funcid, context, ret, exc):
        self.key = key
        self.funcid = funcid
        self.context = context
        self.ret = ret
        self.exc = exc
