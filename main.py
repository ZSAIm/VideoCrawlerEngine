
from subprocess import Popen
from start import run_app
from helper.conf import get_conf
import os
import sys

if __name__ == '__main__':
    procs = []
    # python 解析器路径
    pypath = sys.executable
    for name in [
        'script',
        'taskflow',
    ]:
        procs.append(Popen([pypath, 'start.py', name]))

    # API 作为守卫进程
    run_app('api')
    # Beta: 强杀进程
    # TODO: 待日志系统完成，以持久化进度后进行正常的关闭进程
    for proc in procs:
        proc.terminate()