# app.py

import logging
from logging.handlers import RotatingFileHandler
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
from models import SaveDict
import signal
import sys
import atexit

app = Flask(__name__)
app.secret_key = config.general.secretkey

# 初始化日志系统
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(config.log.level)
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        config.log.file,
        maxBytes=config.log.max_bytes,
        backupCount=config.log.backup_count
    )
    file_handler.setFormatter(logging.Formatter(config.log.format))
    
    # 添加到logger
    logger.addHandler(file_handler)
    return logger

# 在创建Flask应用后初始化日志
logger = setup_logger()
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)

# 用于存储所有任务的进度
# task_progress = {}
# html = {}
# task_cancel_flags = {}
# task_pause_flags = {}
# task_pause_events = {}
task_progress = SaveDict("task_progress","./databuf/task_progress.pkl")
html = SaveDict("html","./databuf/html.pkl")
task_cancel_flags = SaveDict("cancel_flags","./databuf/cancel_flags.pkl")
task_pause_flags = SaveDict("task_pause_flags","./databuf/task_pause_flags.pkl")

def pop(id):
    if id in task_progress:
        task_progress.pop(id, None)
    if id in html:
        html.pop(id, None)
    if id in task_cancel_flags:
        task_cancel_flags.pop(id, None)
    logger.info(f"任务{id}被删除")

def run_in_background(start_id, end_id, cid, task_id):
    try:
        logger.info(f"启动后台任务: {task_id} | {start_id}-{end_id} | cid={cid}")
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

        # 运行爬取任务
        status,res = run(start_id, end_id, cid, task_id, update_progress_callback(task_id),should_cancel,should_pause)
        if status=='cancelled':
            logger.info(f"任务{task_id}已经被成功取消")
            # 标记任务取消
            task_progress[task_id]["status"] = "cancelled"
            task_progress[task_id]["progress"] = 0
            task_progress[task_id]["donetime"] = time.time()
        elif status=='completed':
            # 标记任务完成
            logger.info(f"任务{task_id}已完成")
            html[task_id] = res
            task_progress[task_id]["status"] = "completed"
            task_progress[task_id]["progress"] = 100
            task_progress[task_id]["donetime"] = time.time()
        else:
            # 标记任务完成
            logger.info(f"任务{task_id}返回状态 {status}")
            task_progress[task_id]["status"] = "paused"
            task_progress[task_id]["progress"] = 0
    except Exception as e:
        # print(f"后台任务出错: {e}")
        logger.error(f"后台任务出错: {e}")
        task_progress[task_id]["status"] = "error"
        task_progress[task_id]["error"] = str(e)
    finally:
        # 先清理暂停数据
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
        logger.info(f"有用户试图访问任务 {task_id}")
        return render_template_string(html[task_id])
    else:
        logger.info(f"有用户试图访问result，但是任务不存在或者没完成")
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
    logger.info(f"有用户试图访问tasklist，共{len(tasks)} 个数据")
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
        logger.waring(f"用户试图取消任务但失败: {task_id}")
        return jsonify(success=False, message="未找到任务ID")
    logger.info(f"用户取消任务: {task_id}")
    
    # 设置取消标志
    task_cancel_flags[task_id] = True
    return jsonify(success=True, message="任务取消请求已发送")

# 添加暂停和恢复路由
@app.route("/pause", methods=["POST"])
def pause_task_session():
    """暂停当前用户的任务"""
    task_id = session.get('task_id')
    if not task_id:
        logger.waring(f"用户试图暂停任务但是无session")
        return jsonify(success=False, message="未找到任务ID")
    return pause_task(task_id)

@app.route("/resume", methods=["POST"])
def resume_task_session():
    """恢复当前用户的任务"""
    task_id = session.get('task_id')
    if not task_id:
        logger.waring(f"用户试图恢复任务但是无session")
        return jsonify(success=False, message="未找到任务ID")
    return resume_task(task_id)

# 添加任务操作路由
@app.route("/api/task/<task_id>/resume", methods=["POST"])
def resume_task(task_id):
    # 如果已经取消，新设置任务
    if not task_id or task_id not in task_progress:
        logger.warning(f"用户试图重启任务，但task_id不存在")
        return jsonify(success=False, message="任务不存在")
    if task_progress[task_id]["status"] == "cancelled":
        logger.info(f"用户试图重启被取消的任务{task_id}")
        return jsonify(success=False, message="任务因为被取消不可被重启")
    if task_progress[task_id]["status"] == 'paused':
        logger.info(f"用户重启被暂停的任务{task_id}")
        # 清除暂停标志并设置事件
        task_pause_flags[task_id] = False
        task_progress[task_id]["status"] = "running"
        return jsonify(success=True, message="任务已恢复")
    logger.warning(f"用户试图重启{task_id}，但是状态是{str(task_progress[task_id]["status"])}，不可恢复")
    return jsonify(success=False, message="非可恢复状态"+str(task_progress[task_id]["status"]))

@app.route("/api/task/<task_id>/pause", methods=["POST"])
def pause_task(task_id):
    # 设置暂停标志
    if not task_id:
        logger.warning(f"用户试图暂停任务，但task_id不存在")
        return jsonify(success=False, message="task id不存在")
    logger.info(f"用户暂停任务: {task_id}")
    task_pause_flags[task_id] = True
    task_progress[task_id]["status"] = "paused"
    return jsonify(success=True, message="任务已暂停")
    
def should_cancel(task_id):
    return task_cancel_flags.get(task_id,False)

def should_pause(task_id):
    return task_pause_flags.get(task_id, False)

def start_task(start_id,end_id,cid,task_id=None,working_outside=False):
    # 生成唯一任务ID
    if not task_id:
        task_id = f"{start_id}-{end_id}-{cid}-{str(uuid.uuid4())}"
        logger.info(f"生成新的{task_id}")
    else:
        logger.info(f"复用task id{task_id}")
    if not working_outside:
        session['task_id'] = task_id
    
    # 启动后台线程
    threading.Thread(
        target=run_in_background,
        args=(start_id, end_id, cid, task_id),
        daemon=True
    ).start()
    if not working_outside:
        # 重定向到等待页面
        return redirect(url_for("waiting"))
    else:
        return None
    
timers_outside=[]#在app.run被调用前的 timers 应当被单独存储
def restart_task():
    deleted_tasks=[]
    for task_id in task_progress.keys():
        try:
            progress = task_progress[task_id]
            if progress["status"] == 'running' or progress["status"] == 'paused':
                start_task(progress["start"],progress["end"],progress["contest_id"],task_id,working_outside=True)
            if progress["status"] == 'completed' or progress["status"] == 'cancelled':
                t=threading.Timer(max(0,config.task.savetime-max(0,time.time()-progress["donetime"])), lambda: pop(task_id))
                t.start()
                timers_outside.append(t)
        except Exception as e:
            logging.error(f"恢复任务{task_id}出错，{e}")
            deleted_tasks.append(task_id)
    for task_id in deleted_tasks:
        pop(task_id)

def shutdown(signum=None, frame=None):
    print("收到退出信号，正在清理...")
    # 取消所有定时器
    for t in timers_outside:
        try:
            t.cancel()
        except:
            pass
    # 关闭 SaveDict，避免析构时 join 卡死
    for store in (task_progress, html, task_cancel_flags, task_pause_flags):
        try:
            store.close()
        except:
            pass
    print("清理完毕，程序退出")
    sys.exit()

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

if __name__ == "__main__":
    logger.info("qidong")
    restart_task()
    app.run(debug=False)
