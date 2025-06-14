from flask import Blueprint, render_template, request, session, abort, render_template_string,redirect,url_for
import app.manager
from app.manager import start_task
import logging
import json

import app.manager
from app.config import CONFIG,config

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@main_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            start_id = int(request.form["start_id"])
            end_id = int(request.form["end_id"])
            cid = int(request.form["cid"])
            return app.manager.start_task(start_id, end_id, cid)
        except ValueError:
            return "请输入三个整数！"
    return render_template("index.html", error=False)

@main_bp.route("/retry", methods=["POST"])
def retry():
    try:
        start_id = int(request.form["start_id"])
        end_id = int(request.form["end_id"])
        cid = int(request.form["cid"])
    except ValueError:
        abort(404)
    else:
        return app.manager.start_task(start_id, end_id, cid)

@main_bp.route("/waiting")
def waiting():
    return render_template(config.general.waitingfile)

@main_bp.route("/progress")
def progress():
    task_id = session.get('task_id')
    if task_id and task_id in app.manager.tasks:
        task = app.manager.tasks[task_id]
        return json.dumps({
            "progress": task.progress,
            "status": task.status,
            "current": task.current,
            "start": task.start,
            "end": task.end,
            "contest_id": task.contest_id,
            "createtime": task.createtime,
            "donetime": task.donetime
        })
    return json.dumps({"progress": 0, "status": "not_started"})

@main_bp.route("/result")
def result():
    task_id = session.get('task_id')
    if task_id and task_id in app.manager.html:
        logger.info(f"有用户试图访问任务 {task_id}")
        context = app.manager.html[task_id]
        return render_template("standing.html", **context)
    else:
        logger.info(f"有用户试图访问result，但是任务不存在或者没完成")
        abort(404)

@main_bp.errorhandler(404)
def show_404_page(e):
    return render_template('404.html'), 404

@main_bp.route("/task/<task_id>")
def visit_by_taskid(task_id):
    if not app.manager.tasks.get(task_id,None):
        abort(404)
