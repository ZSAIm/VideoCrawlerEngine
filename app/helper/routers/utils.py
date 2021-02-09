
from app.model.data import AppRespModel
from exception import ClientResponseError
from helper.conf import get_conf
import time


def client_hook(
    self,
    params: dict,
    headers: dict,
    cookies: dict,
    *,
    name: str = None
):
    # 改hook需要配合raw参数使用
    start = time.time()
    try:
        result = yield params, headers, cookies
    except ClientResponseError as err:
        result = {
            'code': err.code,
            'msg': err.msg
        }
    return AppRespModel(
        name=name,
        latency=(time.time() - start) * 1000,
        gateway=get_conf('app')[name].gateway.geturl(),
        **result
    )
