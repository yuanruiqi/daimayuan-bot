from flask import Blueprint, render_template, session, request, redirect, url_for, jsonify, abort
from app.manager import task_progress, pause_task, resume_task, cancel_task
import time
import logging
from app.config import CONFIG

tasks_bp = Blueprint('tasks', __name__)
logger = logging.getLogger(__name__)

@tasks_bp.route("/tasklist")
def task_list():
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
            "remaining": round(CONFIG['task']['savetime'] - (time.time() - progress["donetime"]), 2)
        })
    tasks.sort(key=lambda x: x["remaining"], reverse=True)
    logger.info(f"有用户试图访问tasklist，共{len(tasks)} 个数据")
    return render_template("tasklist.html", tasks=tasks, tottime=CONFIG['task']['savetime'])

@tasks_bp.route("/selecttask", methods=["POST"])
def select_task():
    task_id = request.form.get("task_id")
    if task_id not in task_progress:
        abort(404)
    
    session['task_id'] = task_id
    return redirect(url_for("main.waiting"))

@tasks_bp.route("/cancel", methods=["POST"])
def cancel_task_session():
    task_id = session.get('task_id')
    if not task_id:
        logger.warning(f"用户试图取消任务但失败: {task_id}")
        return jsonify(success=False, message="未找到任务ID")
    return cancel_task(task_id)

@tasks_bp.route("/pause", methods=["POST"])
def pause_task_session():
    task_id = session.get('task_id')
    if not task_id:
        logger.warning(f"用户试图暂停任务但是无session")
        return jsonify(success=False, message="未找到任务ID")
    return pause_task(task_id)

@tasks_bp.route("/resume", methods=["POST"])
def resume_task_session():
    task_id = session.get('task_id')
    if not task_id:
        logger.warning(f"用户试图恢复任务但是无session")
        return jsonify(success=False, message="未找到任务ID")
    return resume_task(task_id)