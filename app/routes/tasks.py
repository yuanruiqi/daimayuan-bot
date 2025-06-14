from flask import Blueprint, render_template, session, request, redirect, url_for, jsonify, abort
import time
import logging

import app.manager
from app.config import CONFIG,config

# 创建任务相关蓝图
tasks_bp = Blueprint('tasks', __name__)
logger = logging.getLogger(__name__)

# 任务列表页面，展示所有任务
@tasks_bp.route("/tasklist")
def task_list():
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
            "remaining": round(config.task.savetime - (time.time() - task.donetime), 2)
        })
    # 按剩余保存时间降序排序
    tasks.sort(key=lambda x: x["remaining"], reverse=True)
    logger.info(f"有用户试图访问tasklist，共{len(tasks)} 个数据")
    return render_template("tasklist.html", tasks=tasks, tottime=config.task.savetime)

# 选择任务，设置session
@tasks_bp.route("/selecttask", methods=["POST"])
def select_task():
    task_id = request.form.get("task_id")
    if task_id not in app.manager.tasks:
        abort(404)
    session['task_id'] = task_id
    return redirect(url_for("main.waiting"))

# 取消任务接口
@tasks_bp.route("/cancel", methods=["POST"])
def cancel_task_session():
    task_id = session.get('task_id')
    if not task_id:
        logger.warning(f"用户试图取消任务但失败: {task_id}")
        return jsonify(success=False, message="未找到任务ID")
    return app.manager.cancel_task(task_id)

# 暂停任务接口
@tasks_bp.route("/pause", methods=["POST"])
def pause_task_session():
    task_id = session.get('task_id')
    if not task_id:
        logger.warning(f"用户试图暂停任务但是无session")
        return jsonify(success=False, message="未找到任务ID")
    return app.manager.pause_task(task_id)

# 恢复任务接口
@tasks_bp.route("/resume", methods=["POST"])
def resume_task_session():
    task_id = session.get('task_id')
    if not task_id:
        logger.warning(f"用户试图恢复任务但是无session")
        return jsonify(success=False, message="未找到任务ID")
    return app.manager.resume_task(task_id)
