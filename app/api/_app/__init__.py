# TODO: 更换WEB框架 fastapi

from flask import Flask, g
from flask_bootstrap import Bootstrap


bootstrap = Bootstrap()


def create_flask_app():
    """ flask 应用创建初始化。"""
    app = Flask(__name__)
    bootstrap.init_app(app)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)
    return app



