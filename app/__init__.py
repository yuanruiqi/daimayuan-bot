from flask import Flask, render_template
import logging
from logging.handlers import RotatingFileHandler
import os
import signal
import sys

from app.config import CONFIG,config
from app.manager import restart_task,init_shared_state
import app.services.standing

def setup_logger():
    """
    配置全局日志记录器，支持文件轮转和控制台输出。
    """
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
    """
    创建数据和日志目录（如不存在）。
    """
    if not os.path.exists('./databuf'):
        os.mkdir('./databuf')
    if not os.path.exists(config.log.folder):
        os.mkdir(config.log.folder)


def create_app():
    """
    Flask应用工厂，初始化应用、日志、蓝图和全局状态。
    """
    app = Flask(__name__)
    app.secret_key = config.general.secretkey
    
    mkdir()

    logger = setup_logger()
    # app.logger.handlers = logger.handlers
    # app.logger.setLevel(logger.level)

    @app.errorhandler(404)
    def global_404(e):
        """全局404错误处理。"""
        return render_template('404.html'), 404
    
    # 注册蓝图
    from app.routes import register_routes
    register_routes(app)
    init_shared_state(app)

    restart_task(app)

    # 注册全局 graceful shutdown
    import signal
    from app.manager import tasks,html,stop_cleanup_thread
    from app.services.standing import standing_task_manager
    _shutdown_called = {'flag': False}
    def _global_shutdown(signum, frame):
        if _shutdown_called['flag']:
            return
        _shutdown_called['flag'] = True
        print('Global graceful shutdown: closing all SaveDicts...')
        try:
            stop_cleanup_thread()
        except Exception as e:
            print(f'Error stopping cleanup thread: {e}')
        for d, name in [(tasks, 'tasks'), (html, 'html')]:
            try:
                d.close()
                print(f'{name} closed.')
            except Exception as e:
                print(f'Error closing {name}: {e}')
        # 关闭阶段可能 logger 已不可用，降级为 print
        try:
            standing_task_manager.handle_exit(signum, frame)
        except Exception as e:
            print(f'Error closing standing_task_manager: {e}')
        print('Global graceful shutdown finished.')
        sys.exit(0)
    signal.signal(signal.SIGTERM, _global_shutdown)
    signal.signal(signal.SIGINT, _global_shutdown)
    return app
