import yaml
from flask import Flask
import logging
from logging.handlers import RotatingFileHandler
import os
from app.config import CONFIG
from app.manager import restart_task,init_shared_state

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(CONFIG['log']['level'])
    file_handler = RotatingFileHandler(
        CONFIG['log']['file'],
        maxBytes=CONFIG['log']['max_bytes'],
        backupCount=CONFIG['log']['backup_count']
    )
    file_handler.setFormatter(logging.Formatter(CONFIG['log']['format']))
    
    # 添加到logger
    logger.addHandler(file_handler)
    return logger

def mkdir():
    if not os.path.exists('./databuf'):
        os.mkdir('./databuf')
    if not os.path.exists(CONFIG['log']['folder']):
        os.mkdir(CONFIG['log']['folder'])


def create_app():
    app = Flask(__name__)
    app.secret_key = CONFIG['general']['secretkey']
    
    mkdir()

    logger = setup_logger()
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)

    
    # 注册蓝图
    from app.routes import register_routes
    register_routes(app)
    init_shared_state(app)

    restart_task(app)

    return app
