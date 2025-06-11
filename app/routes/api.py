from flask import Blueprint, jsonify
import time

import app.manager
from app.config import CONFIG,config

api_bp = Blueprint('api', __name__)

@api_bp.route("/api/tasks")
def get_tasks():
    tasks = []
    for task_id in app.manager.tasks.keys():
        task = app.manager.tasks[task_id]
        tasks.append({
            "id": task_id,
            "status": task.status,
            "progress": task.progress,
            "start": task.start,
            "end": task.end,
            "current": task.current,
            "contest_id": task.contest_id,
            "remaining": round(config.task.savetime - (time.time() - task.donetime), 2)
        })
    tasks.sort(key=lambda x: x["remaining"], reverse=True)
    return jsonify(tasks=tasks, tottime=config.task.savetime)

@api_bp.route("/api/task/<task_id>/resume", methods=["POST"])
def api_resume_task(task_id):
    return app.manager.resume_task(task_id)

@api_bp.route("/api/task/<task_id>/pause", methods=["POST"])
def api_pause_task(task_id):
    return app.manager.pause_task(task_id)