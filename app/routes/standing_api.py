from flask import Blueprint, jsonify
from app.services.standing import StandingTaskManager

# 实例化榜单任务管理器（与 standing.py 保持一致）
standing_api_bp = Blueprint('standing_api', __name__)
task_manager = StandingTaskManager()

@standing_api_bp.route('/api/standing_tasks')
def get_standing_tasks():
    tasks = []
    for task in task_manager.tasks.values():
        tasks.append({
            'id': task.task_id,
            'status': task.status,
            'progress': task.current_id - task.start_id,
            'start': task.start_id,
            'end': task.end_id,
            'current': task.current_id,
            'contest_id': task.contest_id
        })
    return jsonify(tasks=tasks)
