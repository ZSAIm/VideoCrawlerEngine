# -*- coding: UTF-8 -*-

from app import create_flask_app
from webdriver import create_wx_app
from downloader import download_mgr
from script import init_scripts
from utils import run_forever
from crawler import init_crawler_workers, CrawlerWorker
import config


def main():
    """ 主程序。 """
    # 加载程序配置
    config.load_config()
    # 创建GUI
    wx_app = create_wx_app()
    # 创建后台服务器
    flask_app = create_flask_app()
    run_forever(flask_app, port=5999)
    # 初始化脚本
    init_scripts()
    # 初始化爬虫工作线程。
    init_crawler_workers()
    # 测试脚本解析。
    crawler = CrawlerWorker(['https://www.bilibili.com/video/av91721893'])
    crawler.run()
    # 启动下载管理器
    download_mgr.start()

    # 加载WebUI
    wx_app.frame.browser.LoadURL('http://127.0.0.1:{port}'.format(port=5999))

    # GUI主循环
    wx_app.MainLoop()


def destroy():
    """ 销毁程序。"""
    # 关闭下载管理器。
    download_mgr.close()


from threading import local, current_thread
tls = local()

def aaa():
    print(tls.__dict__)
    try:
        print(tls.test)
    except Exception as e:
        print(e)
    tls.__dict__.update({
        'test': current_thread()
    })
    try:
        print(tls.test)
    except Exception as e:
        print(e)
    print(tls.__dict__)
    print(tls.__dict__)


if __name__ == '__main__':
    # Thread(target=aaa).start()
    # Thread(target=aaa).start()
    # Thread(target=aaa).start()
    main()
    destroy()


