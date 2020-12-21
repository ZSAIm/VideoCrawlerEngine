from app.script import main

if __name__ == '__main__':
    # parser = ArgumentParser()
    # parser.add_argument('s', help='服务名称', type=str)
    # args = parser.parse_args()

    # 启动服务
    # server = SERVICES_CONFIG['script']
    # server = get_conf('app')['script']
    # module = import_module(server['module'])
    # getattr(module, server['entrypoint'])()
    # __import__(server['module']).main.main()
    main.main()