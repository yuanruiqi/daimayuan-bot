# 榜单任务API接口
from flask import Blueprint, request, jsonify, render_template
from app.services.standing import StandingTask, standing_task_manager, standing_get, standing_valid, standing_push
from app.services.down import create_session, get_contest_problems, get_cache, process_single_submission
# from app.services.anal import anal, ren
import app.services.anal as anal
import app.services.ren as ren
import uuid

standing_bp = Blueprint('standing', __name__)
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

@standing_bp.route('/standing/create', methods=['POST'])
def create_task():
    data = request.json
    try:
        start_id = int(data['start_id'])
        end_id = int(data['end_id'])
        contest_id = int(data['contest_id'])
    except (KeyError, ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    task_id = f"{contest_id}_{start_id}_{end_id}_{str(uuid.uuid4().replace('-','_'))}"
    if task_id in task_manager.tasks:
        return jsonify({'success': False, 'message': '任务已存在'}), 400
    task = StandingTask(task_id, start_id, end_id, contest_id)
    task_manager.add_task(task)
    return jsonify({'success': True, 'task_id': task_id, 'status': task.status})

@standing_bp.route('/standing/start/<task_id>', methods=['POST'])
def start_task(task_id):
    task_manager.start_task(task_id)
    return jsonify({'task_id': task_id, 'status': task_manager.tasks[task_id].status})

@standing_bp.route('/standing/pause/<task_id>', methods=['POST'])
def pause_task(task_id):
    task_manager.pause_task(task_id)
    return jsonify({'task_id': task_id, 'status': task_manager.tasks[task_id].status})

@standing_bp.route('/standing/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    task_manager.cancel_task(task_id)
    return jsonify({'task_id': task_id, 'status': task_manager.tasks[task_id].status})

@standing_bp.route('/standing/delete/<task_id>', methods=['POST'])
def delete_task(task_id):
    task_manager.delete_task(task_id)
    return jsonify({'task_id': task_id, 'status': 'deleted'})

@standing_bp.route('/standing/list', methods=['GET'])
def list_tasks():
    return jsonify([
        {'task_id': t.task_id, 'status': t.status, 'progress': t.current_id, 'end_id': t.end_id, 'contest_id': t.contest_id}
        for t in task_manager.tasks.values()
    ])

@standing_bp.route('/standing/data/<task_id>', methods=['GET'])
def get_task_data(task_id):
    task = task_manager.tasks.get(task_id)
    if not task:
        return "任务不存在", 404
    # 用anal分析榜单结果，得到df, name_list, submission_history
    try:
        df, name_list, submission_history = anal.run(task.results)
        problem_map = get_problem_map(task.contest_id)
        context = ren.run(
            df, task.start_id, task.end_id, task.contest_id, name_list, submission_history, problem_map
        )
    except Exception as e:
        context = {
            'table_html': f'<div>分析失败{e}</div>',
            'startid': task.start_id,
            'endid': task.end_id,
            'cid': task.contest_id,
            'timeline_data': []
        }
    return render_template(
        'standing.html',
        **context
    )
