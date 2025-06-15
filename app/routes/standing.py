# 榜单任务API接口
from flask import Blueprint, request, jsonify
from app.services.standing import StandingTask, StandingTaskManager

bp = Blueprint('standing', __name__)
task_manager = StandingTaskManager(max_running=3)

def dummy_get(id, contest_id):
    # TODO: 实现实际的get逻辑
    return {}

def dummy_valid(result):
    # TODO: 实现实际的valid逻辑
    return True

def dummy_push(results, result):
    results.append(result)

@bp.route('/standing/create', methods=['POST'])
def create_task():
    data = request.json
    start_id = data['start_id']
    end_id = data['end_id']
    contest_id = data['contest_id']
    task_id = f"{contest_id}_{start_id}_{end_id}"
    task = StandingTask(task_id, start_id, end_id, contest_id)
    task_manager.add_task(task)
    return jsonify({'task_id': task_id, 'status': task.status})

@bp.route('/standing/start/<task_id>', methods=['POST'])
def start_task(task_id):
    task_manager.start_task(task_id, dummy_get, dummy_valid, dummy_push)
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
