from flask import Flask, render_template
import logging
from logging.handlers import RotatingFileHandler
import os

from app.config import CONFIG,config
from app.manager import restart_task,init_shared_state

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(config.log.level)
    file_handler = RotatingFileHandler(
        config.log.file,
        maxBytes=config.log.max_bytes,
        backupCount=config.log.backup_count,
        encoding='utf-8'  # 添加UTF-8编码
    )
    file_handler.setFormatter(logging.Formatter(config.log.format))
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.log.format))
    console_handler.setLevel(config.log.level)
    
    # 添加到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

def mkdir():
    if not os.path.exists('./databuf'):
        os.mkdir('./databuf')
    if not os.path.exists(config.log.folder):
        os.mkdir(config.log.folder)


def create_app():
    app = Flask(__name__)
    app.secret_key = config.general.secretkey
    
    mkdir()

    logger = setup_logger()
    # app.logger.handlers = logger.handlers
    # app.logger.setLevel(logger.level)

    @app.errorhandler(404)
    def global_404(e):
        return render_template('404.html'), 404
    
    # 注册蓝图
    from app.routes import register_routes
    register_routes(app)
    init_shared_state(app)

    restart_task(app)

    return app
