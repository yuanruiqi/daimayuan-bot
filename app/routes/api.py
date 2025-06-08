from flask import Blueprint, jsonify
from app.manager import task_progress, pause_task, resume_task
import time
from app.config import CONFIG

api_bp = Blueprint('api', __name__)

@api_bp.route("/api/tasks")
def get_tasks():
    tasks = []
    for task_id in task_progress.keys():
        progress = task_progress[task_id]
        tasks.append({
            "id": task_id,
            "status": progress["status"],
            "progress": progress["progress"],
            "start": progress["start"],
            "end": progress["end"],
            "current": progress["current"],
            "contest_id": progress["contest_id"],
            "remaining": round(CONFIG['task']['savetime'] - (time.time() - progress["donetime"]), 2)
        })
    tasks.sort(key=lambda x: x["remaining"], reverse=True)
    return jsonify(tasks=tasks, tottime=CONFIG['task']['savetime'])

@api_bp.route("/api/task/<task_id>/resume", methods=["POST"])
def api_resume_task(task_id):
    return resume_task(task_id)

@api_bp.route("/api/task/<task_id>/pause", methods=["POST"])
def api_pause_task(task_id):
    return pause_task(task_id)