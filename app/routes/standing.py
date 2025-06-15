# 榜单任务API接口
from flask import Blueprint, request, jsonify
from app.services.standing import StandingTask, standing_task_manager, standing_get, standing_valid, standing_push
from app.services.down import create_session, get_contest_problems, get_cache, process_single_submission

bp = Blueprint('standing', __name__)
task_manager = standing_task_manager

# 全局只初始化一次，避免重复请求
_standing_session = create_session()
_standing_cache = get_cache()

# contest_id -> problem_map 缓存
_problem_map_cache = {}
def get_problem_map(contest_id):
    if contest_id not in _problem_map_cache:
        _problem_map_cache[contest_id] = get_contest_problems(_standing_session, contest_id) or {}
    return _problem_map_cache[contest_id]

def real_get(submission_id, contest_id):
    problem_map = get_problem_map(contest_id)
    result, status = process_single_submission(_standing_session, submission_id, contest_id, _standing_cache, problem_map)
    if status == 'not_found':
        return 404
    if status != 'ok':
        return None
    return result

@bp.route('/standing/create', methods=['POST'])
def create_task():
    data = request.json
    try:
        start_id = int(data['start_id'])
        end_id = int(data['end_id'])
        contest_id = int(data['contest_id'])
    except (KeyError, ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    task_id = f"{contest_id}_{start_id}_{end_id}"
    if task_id in task_manager.tasks:
        return jsonify({'success': False, 'message': '任务已存在'}), 400
    task = StandingTask(task_id, start_id, end_id, contest_id)
    task_manager.add_task(task)
    return jsonify({'success': True, 'task_id': task_id, 'status': task.status})

@bp.route('/standing/start/<task_id>', methods=['POST'])
def start_task(task_id):
    task_manager.start_task(task_id)
    return jsonify({'task_id': task_id, 'status': task_manager.tasks[task_id].status})

@bp.route('/standing/pause/<task_id>', methods=['POST'])
def pause_task(task_id):
    task_manager.pause_task(task_id)
    return jsonify({'task_id': task_id, 'status': task_manager.tasks[task_id].status})

@bp.route('/standing/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    task_manager.cancel_task(task_id)
    return jsonify({'task_id': task_id, 'status': task_manager.tasks[task_id].status})

@bp.route('/standing/delete/<task_id>', methods=['POST'])
def delete_task(task_id):
    task_manager.delete_task(task_id)
    return jsonify({'task_id': task_id, 'status': 'deleted'})

@bp.route('/standing/list', methods=['GET'])
def list_tasks():
    return jsonify([
        {'task_id': t.task_id, 'status': t.status, 'progress': t.current_id, 'end_id': t.end_id, 'contest_id': t.contest_id}
        for t in task_manager.tasks.values()
    ])

@bp.route('/standing/data/<task_id>', methods=['GET'])
def get_task_data(task_id):
    task = task_manager.tasks.get(task_id)
    if not task:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'results': task.results, 'status': task.status})
