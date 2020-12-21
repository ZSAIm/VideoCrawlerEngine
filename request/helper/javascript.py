from contextlib import contextmanager
from helper.conf import get_conf
import jscaller
import os


@contextmanager
def js_session(source, timeout=None, engine=None):
    from request.utils import jsruntime

    worker = get_conf('payload')['jsruntime']

    timeout = timeout or worker.get('timeout', None)
    if not engine:
        engine = jscaller.engine.JSEngine(
            name=worker['name'],
            source=worker['source'],
            shell=worker['shell'],
            version=worker['version'],
            encoding='utf-8',
        )

    if os.path.isfile(source):
        session = jscaller.session
    else:
        session = jscaller.Session
    with session(source, timeout, engine) as sess:
        yield sess
        req = jsruntime(sess)
        task = req.start_request()
        result = task.result()
        return result