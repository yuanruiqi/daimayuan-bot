import os
import time
import uuid
import threading
import logging
import signal
import sys
from flask import jsonify, session, redirect, url_for

from app.models import SaveDict, Task
from app.services import run
from app.config import CONFIG,config

# 共享状态
tasks = SaveDict("tasks", "./databuf/tasks.pkl")
html = SaveDict("html", "./databuf/html.pkl")

timers = []

logger = logging.getLogger(__name__)

def init_shared_state(app):
    global tasks, html
    
    # 创建数据目录
    if not os.path.exists('./databuf'):
        os.mkdir('./databuf')
    
    # 初始化共享字典
    tasks = SaveDict("tasks", "./databuf/tasks.pkl")
    html = SaveDict("html", "./databuf/html.pkl")

    # 注册关闭的行为
    signal.signal(signal.SIGTERM, cleanup_on_shutdown)
    signal.signal(signal.SIGINT, cleanup_on_shutdown)

def pop(id):
    if id in tasks:
        tasks.pop(id, None)
    if id in html:
        html.pop(id, None)
    logger.info(f"任务{id}被删除")

def run_in_background(start_id, end_id, cid, task_id):
    try:
        logger.info(f"启动后台任务: {task_id} | {start_id}-{end_id} | cid={cid}")
        
        # 运行爬取任务
        status, res = run(start_id, end_id, cid, task_id, 
                         update_progress_callback(task_id), 
                         should_cancel, should_pause)
        
        if status == 'cancelled':
            logger.info(f"任务{task_id}已经被成功取消")
            tasks[task_id].status = "cancelled"
            tasks[task_id].progress = 0
            tasks[task_id].donetime = time.time()
        elif status == 'completed':
            logger.info(f"任务{task_id}已完成")
            html[task_id] = res
            tasks[task_id].status = "completed"
            tasks[task_id].progress = 100
            tasks[task_id].donetime = time.time()
        else:
            logger.info(f"任务{task_id}返回状态 {status}")
            tasks[task_id].status = "paused"
            tasks[task_id].progress = 0
    except Exception as e:
        logger.error(f"后台任务出错: {type(e)}: {e}")
        tasks[task_id].status = "error"
        tasks[task_id].error = str(e)
    finally:
        tasks[task_id].pause_flag = False
        tl = threading.Timer(config.task.savetime, lambda: pop(task_id))
        tl.start()
        timers.append(tl)

def update_progress_callback(task_id):
    def callback(current, total, current_id):
        if task_id in tasks:
            progress = int(current / total * 100)
            tasks[task_id].progress = progress
            tasks[task_id].current = current_id
    return callback

def start_task(start_id, end_id, cid, task_id=None, working_outside=False):
    if not task_id:
        task_id = f"{start_id}-{end_id}-{cid}-{str(uuid.uuid4())}"
        logger.info(f"生成新的{task_id}")
    else:
        logger.info(f"复用task id{task_id}")
    
    if not working_outside:
        session['task_id'] = task_id
    
    # 创建任务对象
    tasks[task_id] = Task(start_id, end_id, cid)
    
    # 启动后台线程
    threading.Thread(
        target=run_in_background,
        args=(start_id, end_id, cid, task_id),
        daemon=True
    ).start()
    
    if not working_outside:
        return redirect(url_for("main.waiting"))

def restart_task(app):
    with app.app_context():
        deleted_tasks = []
        for task_id in tasks.keys():
            try:
                task = tasks[task_id]
                if task.status in ['running', 'paused']:
                    start_task(task.start, task.end, 
                              task.contest_id, task_id, True)
                elif task.status in ['completed', 'cancelled']:
                    t = threading.Timer(
                        max(0, config.task.savetime - 
                        max(0, time.time() - task.donetime)), 
                        lambda: pop(task_id)
                    )
                    t.start()
                    timers.append(t)
            except Exception as e:
                logging.error(f"恢复任务{task_id}出错，{e}")
                deleted_tasks.append(task_id)
        for task_id in deleted_tasks:
            pop(task_id)

def should_cancel(task_id):
    return tasks.get(task_id, None) and tasks[task_id].cancel_flag

def should_pause(task_id):
    return tasks.get(task_id, None) and tasks[task_id].pause_flag

def pause_task(task_id):
    if not task_id or task_id not in tasks:
        logger.warning(f"用户试图暂停任务，但task_id不存在")
        return jsonify(success=False, message="task id不存在")
    logger.info(f"用户暂停任务: {task_id}")
    tasks[task_id].pause_flag = True
    tasks[task_id].status = "paused"
    return jsonify(success=True, message="任务已暂停")

def resume_task(task_id):
    if not task_id or task_id not in tasks:
        logger.warning(f"用户试图重启任务，但task_id不存在")
        return jsonify(success=False, message="任务不存在")
    if tasks[task_id].status == "cancelled":
        logger.info(f"用户试图重启被取消的任务{task_id}")
        return jsonify(success=False, message="任务因为被取消不可被重启")
    if tasks[task_id].status == 'paused':
        logger.info(f"用户重启被暂停的任务{task_id}")
        tasks[task_id].pause_flag = False
        tasks[task_id].status = "running"
        start_task(tasks[task_id].start, tasks[task_id].end, tasks[task_id].contest_id, task_id)
        return jsonify(success=True, message="任务已恢复")
    logger.warning(f"用户试图重启{task_id}，但是状态是{str(tasks[task_id].status)}，不可恢复")
    return jsonify(success=False, message="非可恢复状态"+str(tasks[task_id].status))

def cancel_task(task_id):
    if not task_id or task_id not in tasks:
        logger.warning(f"用户试图取消任务但失败: {task_id}")
        return jsonify(success=False, message="未找到任务ID")
    logger.info(f"用户取消任务: {task_id}")
    tasks[task_id].cancel_flag = True
    return jsonify(success=True, message="任务取消请求已发送")

def cleanup_on_shutdown(signum=None, frame=None):
    # 取消所有定时器
    for t in timers:
        try:
            t.cancel()
        except:
            pass
    # 关闭 SaveDict
    for store in (tasks, html):
        try:
            store.close()
        except:
            pass
    print("Exit called,SystemExit will be throwed")
    sys.exit(0)