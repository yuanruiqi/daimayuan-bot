# app.py

from flask import Flask, request, render_template, render_template_string, redirect, url_for, session, abort,jsonify
from run import run
import os
import threading
import json
import time
import secrets
import config
import uuid
import pandas

app = Flask(__name__)
app.secret_key = config.general.secretkey
# 用于存储所有任务的进度
task_progress = {}
html = {}
task_cancel_flags = {}
task_pause_flags = {}
task_pause_events = {}

def pop(id):
    if id in task_progress:
        task_progress.pop(id, None)
    if id in html:
        html.pop(id, None)
    if id in task_cancel_flags:
        task_cancel_flags.pop(id, None)

def run_in_background(start_id, end_id, cid, task_id):
    try:
        print(task_id)
        # 初始化进度
        task_progress[task_id] = {
            "progress": 0,
            "status": "running",
            "current": start_id,
            "start": start_id,
            "end": end_id,
            "contest_id": cid,
            "createtime":time.time(),
            "donetime":1e18
        }
        task_cancel_flags[task_id] = False

        # 初始化暂停事件
        task_pause_events[task_id] = threading.Event()
        task_pause_events[task_id].set()  # 初始设置为运行状态

        # 运行爬取任务
        res = run(start_id, end_id, cid, task_id, update_progress_callback(task_id),should_cancel,should_pause,task_pause_events[task_id])
        if task_cancel_flags.get(task_id,False):
            # 标记任务取消
            task_progress[task_id]["status"] = "cancelled"
            task_progress[task_id]["progress"] = 0
        else:
            # 标记任务完成
            html[task_id] = res
            task_progress[task_id]["status"] = "completed"
            task_progress[task_id]["progress"] = 100
        task_progress[task_id]["donetime"] = time.time()
    except Exception as e:
        print(f"后台任务出错: {e}")
        task_progress[task_id]["status"] = "error"
        task_progress[task_id]["error"] = str(e)
    finally:
        # 先清理暂停数据
        if task_id in task_pause_events:
            task_pause_events.pop(task_id, None)
        if task_id in task_pause_flags:
            task_pause_flags.pop(task_id, None)
        # 10 分钟后清理进度数据
        threading.Timer(config.task.savetime, lambda: pop(task_id)).start()

def update_progress_callback(task_id):
    def callback(current, total, current_id):
        if task_id in task_progress:
            progress = int(current / total * 100)
            task_progress[task_id].update({
                "progress": progress,
                "current": current_id
            })
    return callback

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            start_id = int(request.form["start_id"])
            end_id = int(request.form["end_id"])
            cid = int(request.form["cid"])
            return start_task(start_id,end_id,cid)
        except ValueError:
            return "请输入三个整数！"
    return render_template("index.html", error=False)

@app.route("/retry", methods=["POST"])
def retry():
    try:
        start_id = int(request.form["start_id"])
        end_id = int(request.form["end_id"])
        cid = int(request.form["cid"])
    except ValueError:
        abort(404) #意味着试图hack
    else:
        return start_task(start_id,end_id,cid)

@app.route("/waiting")
def waiting():
    return render_template(config.general.waitingfile)

@app.route("/progress")
def progress():
    task_id = session.get('task_id')
    if task_id and task_id in task_progress:
        return json.dumps(task_progress[task_id])
    return json.dumps({"progress": 0, "status": "not_started"})

@app.route("/result")
def result():
    # 直接读取生成的 out.html
    task_id = session.get('task_id')
    if task_id and task_id in html:
        return render_template_string(html[task_id])
    else:
        abort(404)

# 在已有路由后添加新路由
@app.route("/tasklist")
def task_list():
    """显示所有存在的任务列表"""
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
            "remaining": round(config.task.savetime - (time.time() - progress["donetime"]), 2)
        })
    tasks.sort(key=lambda x: x["remaining"], reverse=True)
    return render_template("tasklist.html", tasks=tasks, tottime=config.task.savetime)

# 添加API路由获取任务数据
@app.route("/api/tasks")
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
            "remaining": round(config.task.savetime - (time.time() - progress["donetime"]), 2)
        })
    tasks.sort(key=lambda x: x["remaining"], reverse=True)
    return jsonify(tasks=tasks, tottime=config.task.savetime)

@app.route("/selecttask", methods=["POST"])
def select_task():
    """选择任务并设置session"""
    task_id = request.form.get("task_id")
    if task_id not in task_progress:
        abort(404)
    
    session['task_id'] = task_id
    return redirect(url_for("waiting"))

@app.errorhandler(404)
def show_404_page(e):
    return render_template('404.html'), 404

@app.route("/cancel", methods=["POST"])
def cancel_task():
    """取消当前用户的任务"""
    task_id = session.get('task_id')
    if not task_id:
        return jsonify(success=False, message="未找到任务ID")
    
    # 设置取消标志
    task_cancel_flags[task_id] = True
    return jsonify(success=True, message="任务取消请求已发送")

# 添加暂停和恢复路由
@app.route("/pause", methods=["POST"])
def pause_task_session():
    """暂停当前用户的任务"""
    task_id = session.get('task_id')
    if not task_id:
        return jsonify(success=False, message="未找到任务ID")
    return pause_task(task_id)

@app.route("/resume", methods=["POST"])
def resume_task_session():
    """恢复当前用户的任务"""
    task_id = session.get('task_id')
    if not task_id:
        return jsonify(success=False, message="未找到任务ID")
    return resume_task(task_id)

# 添加任务操作路由
@app.route("/api/task/<task_id>/resume", methods=["POST"])
def resume_task(task_id):
    # 如果已经取消，新设置任务
    if not task_id or task_id not in task_progress:
        return jsonify(success=False, message="任务不存在")
    if task_progress[task_id]["status"] == "cancelled":
        start,end,cid=task_progress[task_id]["start"],task_progress[task_id]["end"],task_progress[task_id]["contest_id"]
        start_task(start,end,cid,task_id)
        return jsonify(success=True, message="任务已重启")
    if task_progress[task_id]["status"] == 'paused':
        # 清除暂停标志并设置事件
        task_pause_flags[task_id] = False
        if task_id in task_pause_events:
            task_pause_events[task_id].set()
        task_progress[task_id]["status"] = "running"
        return jsonify(success=True, message="任务已恢复")
    return jsonify(success=False, message="非可恢复状态"+str(task_progress[task_id]["status"]))

@app.route("/api/task/<task_id>/pause", methods=["POST"])
def pause_task(task_id):
    # 设置暂停标志
    task_pause_flags[task_id] = True
    task_progress[task_id]["status"] = "paused"
    return jsonify(success=True, message="任务已暂停")
    

def should_cancel(task_id):
    print(task_cancel_flags.get(task_id,False))
    return task_cancel_flags.get(task_id,False)

def should_pause(task_id):
    return task_pause_flags.get(task_id, False)

def start_task(start_id,end_id,cid,task_id=None):
    # 生成唯一任务ID
    if not task_id:
        task_id = f"{start_id}-{end_id}-{cid}-{str(uuid.uuid4())}"
    session['task_id'] = task_id
    
    # 启动后台线程
    threading.Thread(
        target=run_in_background,
        args=(start_id, end_id, cid, task_id),
        daemon=True
    ).start()
    
    # 重定向到等待页面
    return redirect(url_for("waiting"))

if __name__ == "__main__":
    app.run(debug=False)