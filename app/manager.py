import os
import time
import uuid
import threading
import logging
from flask import jsonify, session, redirect, url_for
from app.models import SaveDict
from app.services import run
from app.config import CONFIG

# 共享状态

task_progress = SaveDict("task_progress","./databuf/task_progress.pkl")
html = SaveDict("html","./databuf/html.pkl")
task_cancel_flags = SaveDict("cancel_flags","./databuf/cancel_flags.pkl")
task_pause_flags = SaveDict("task_pause_flags","./databuf/task_pause_flags.pkl")

timers_outside = []

logger = logging.getLogger(__name__)

def init_shared_state(app):
    global task_progress, html, task_cancel_flags, task_pause_flags
    
    # 创建数据目录
    if not os.path.exists('./databuf'):
        os.mkdir('./databuf')
    
    # 初始化共享字典
    task_progress = SaveDict("task_progress", "./databuf/task_progress.pkl")
    html = SaveDict("html", "./databuf/html.pkl")
    task_cancel_flags = SaveDict("cancel_flags", "./databuf/cancel_flags.pkl")
    task_pause_flags = SaveDict("task_pause_flags", "./databuf/task_pause_flags.pkl")

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
            "createtime": time.time(),
            "donetime": 1e18
        }
        task_cancel_flags[task_id] = False

        # 运行爬取任务
        status, res = run(start_id, end_id, cid, task_id, 
                         update_progress_callback(task_id), 
                         should_cancel, should_pause)
        
        if status == 'cancelled':
            logger.info(f"任务{task_id}已经被成功取消")
            task_progress[task_id]["status"] = "cancelled"
            task_progress[task_id]["progress"] = 0
            task_progress[task_id]["donetime"] = time.time()
        elif status == 'completed':
            logger.info(f"任务{task_id}已完成")
            html[task_id] = res
            task_progress[task_id]["status"] = "completed"
            task_progress[task_id]["progress"] = 100
            task_progress[task_id]["donetime"] = time.time()
        else:
            logger.info(f"任务{task_id}返回状态 {status}")
            task_progress[task_id]["status"] = "paused"
            task_progress[task_id]["progress"] = 0
    except Exception as e:
        logger.error(f"后台任务出错: {e}")
        task_progress[task_id]["status"] = "error"
        task_progress[task_id]["error"] = str(e)
    finally:
        if task_id in task_pause_flags:
            task_pause_flags.pop(task_id, None)
        threading.Timer(CONFIG['task']['savetime'], lambda: pop(task_id)).start()

def update_progress_callback(task_id):
    def callback(current, total, current_id):
        if task_id in task_progress:
            progress = int(current / total * 100)
            task_progress[task_id].update({
                "progress": progress,
                "current": current_id
            })
    return callback

def start_task(start_id, end_id, cid, task_id=None, working_outside=False):
    if not task_id:
        task_id = f"{start_id}-{end_id}-{cid}-{str(uuid.uuid4())}"
        logger.info(f"生成新的{task_id}")
    else:
        logger.info(f"复用task id{task_id}")
    
    if not working_outside:
        session['task_id'] = task_id
    
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
        for task_id in task_progress.keys():
            try:
                progress = task_progress[task_id]
                if progress["status"] in ['running', 'paused']:
                    start_task(progress["start"], progress["end"], 
                              progress["contest_id"], task_id, True)
                elif progress["status"] in ['completed', 'cancelled']:
                    t = threading.Timer(
                        max(0, CONFIG['task']['savetime'] - 
                        max(0, time.time() - progress["donetime"])), 
                        lambda: pop(task_id)
                    )
                    t.start()
                    timers_outside.append(t)
            except Exception as e:
                logging.error(f"恢复任务{task_id}出错，{e}")
                deleted_tasks.append(task_id)
        for task_id in deleted_tasks:
            pop(task_id)

def should_cancel(task_id):
    return task_cancel_flags.get(task_id, False)

def should_pause(task_id):
    return task_pause_flags.get(task_id, False)

def pause_task(task_id):
    if not task_id:
        logger.warning(f"用户试图暂停任务，但task_id不存在")
        return jsonify(success=False, message="task id不存在")
    logger.info(f"用户暂停任务: {task_id}")
    task_pause_flags[task_id] = True
    task_progress[task_id]["status"] = "paused"
    return jsonify(success=True, message="任务已暂停")

def resume_task(task_id):
    if not task_id or task_id not in task_progress:
        logger.warning(f"用户试图重启任务，但task_id不存在")
        return jsonify(success=False, message="任务不存在")
    if task_progress[task_id]["status"] == "cancelled":
        logger.info(f"用户试图重启被取消的任务{task_id}")
        return jsonify(success=False, message="任务因为被取消不可被重启")
    if task_progress[task_id]["status"] == 'paused':
        logger.info(f"用户重启被暂停的任务{task_id}")
        task_pause_flags[task_id] = False
        task_progress[task_id]["status"] = "running"
        return jsonify(success=True, message="任务已恢复")
    logger.warning(f"用户试图重启{task_id}，但是状态是{str(task_progress[task_id]['status'])}，不可恢复")
    return jsonify(success=False, message="非可恢复状态"+str(task_progress[task_id]["status"]))

def cancel_task(task_id):
    if not task_id:
        logger.warning(f"用户试图取消任务但失败: {task_id}")
        return jsonify(success=False, message="未找到任务ID")
    logger.info(f"用户取消任务: {task_id}")
    task_cancel_flags[task_id] = True
    return jsonify(success=True, message="任务取消请求已发送")

def cleanup_on_shutdown():
    # 取消所有定时器
    for t in timers_outside:
        try:
            t.cancel()
        except:
            pass
    # 关闭 SaveDict
    for store in (task_progress, html, task_cancel_flags, task_pause_flags):
        try:
            store.close()
        except:
            pass