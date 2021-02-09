

VALIDATE_ERROR = -1
SUCCESS = 0
DATA_EXISTS = 2
DATA_NOT_FOUND = 3
PAGE_OUT_OF_RANGE = 4
UNAUTHORIZED_ERROR = 5
TOKEN_EXPIRED = 6
ACCESS_EXPIRED = 7
CONNECT_TIMEOUT = 8


class NodeState:
    READY = 'ready'
    QUEUING = 'queuing'
    RUNNING = 'running'
    STOPPED = 'stopped'
    WARNING = 'warning'
    ERROR = 'error'
    DONE = 'done'

