

class APIException(Exception):
    code: int
    msg: str
    data: []

    def __init__(self, msg, data=None):
        self.msg = msg
        self.data = data or []


class DataExistedError(APIException):
    code = 1



