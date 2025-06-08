from .api import api_bp
from .main import main_bp
from .tasks import tasks_bp

def register_routes(app):
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tasks_bp)