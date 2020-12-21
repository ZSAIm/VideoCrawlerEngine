# from conf import get_config
#
#
# if __name__ == '__main__':
#     # parser = ArgumentParser()
#     # parser.add_argument('s', help='服务名称', type=str)
#     # args = parser.parse_args()
#
#     # 启动服务
#     # server = SERVICES_CONFIG['taskflow']
#     server = get_config('taskflow')
#     __import__(server['module']).main.main()


from helper.conf import get_conf
from importlib import import_module
from app.taskflow import main

if __name__ == '__main__':
    # parser = ArgumentParser()
    # parser.add_argument('s', help='服务名称', type=str)
    # args = parser.parse_args()

    # 启动服务
    # server = SERVICES_CONFIG['taskflow']
    # server = get_conf('app')['taskflow']
    # module = import_module(server['module'])
    # getattr(module, server['entrypoint'])()
    # __import__(server['module']).main.main()
    main.main()