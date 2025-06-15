from .api import api_bp
from .main import main_bp
from .tasks import tasks_bp
from .standing_api import standing_api_bp  # 新增榜单任务API蓝图

def register_routes(app):
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(standing_api_bp)  # 注册榜单任务API蓝图