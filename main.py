from app import create_flask_app
from script import init_scripts
from worker import init_workers
import config
import worker
import task
import threading
import time


if __name__ == '__main__':
    config.load_config()
    flask_app = create_flask_app()
    flask_app.config['SECRET_KEY'] = '66666666666'
    init_scripts()
    init_workers()
    flask_app.run(port=2333, debug=False)
    task.stop_all()
    worker.shutdown()

