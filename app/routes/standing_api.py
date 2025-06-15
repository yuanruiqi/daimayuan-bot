from flask import Blueprint, jsonify
from app.services.standing import standing_task_manager
import time
from app.config import config
standing_api_bp = Blueprint('standing_api', __name__)
task_manager = standing_task_manager

@standing_api_bp.route('/api/standing_tasks')
def get_standing_tasks():
    tasks = []
    for task in task_manager.tasks.values():
        total = max(1, task.end_id - task.start_id + 1)
        progress = min(100, round((task.current_id - task.start_id) / total * 100))
        remaining_time = task.remaining_time() if hasattr(task, 'remaining_time') else 0
        tasks.append({
            'id': task.task_id,
            'status': task.status,
            'progress': progress,
            'start': task.start_id,
            'end': task.end_id,
            'current': task.current_id,
            'contest_id': task.contest_id,
            'remaining': max(0,config.task.savetime-(time.time()-task.done_time))
        })
        
    return jsonify(tasks=tasks)
