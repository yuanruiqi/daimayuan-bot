# app.py

from flask import Flask, request, render_template, render_template_string, redirect, url_for, session
from run import run
import os
import threading
import json
import time
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16) # 生成随机密钥
# 用于存储所有任务的进度
task_progress = {}

def run_in_background(a, b, c, task_id):
    try:
        # 初始化进度
        task_progress[task_id] = {
            "progress": 0,
            "status": "running",
            "current": a,
            "start": a,
            "end": b
        }
        
        # 运行爬取任务
        run(a, b, c, update_progress_callback(task_id))
        
        # 标记任务完成
        task_progress[task_id]["status"] = "completed"
        task_progress[task_id]["progress"] = 100
        
    except Exception as e:
        print(f"后台任务出错: {e}")
        task_progress[task_id]["status"] = "error"
        task_progress[task_id]["error"] = str(e)
    finally:
        # 清理lock文件
        if os.path.exists('lock'):
            os.remove('lock')
        # 10分钟后清理进度数据
        threading.Timer(600, lambda: task_progress.pop(task_id, None)).start()

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
            a = int(request.form["a"])
            b = int(request.form["b"])
            c = int(request.form["c"])
            
            if os.path.exists('lock'):
                return render_template("index.html", error=True)
                
            # 创建锁文件
            with open('lock', 'w') as f:
                f.write('working')
            
            # 生成唯一任务ID
            task_id = f"{a}-{b}-{c}-{int(time.time())}"
            session['task_id'] = task_id
            
            # 启动后台线程
            threading.Thread(
                target=run_in_background,
                args=(a, b, c, task_id),
                daemon=True
            ).start()
            
            # 重定向到等待页面
            return redirect(url_for("waiting"))
            
        except ValueError:
            return "请输入三个整数！"
    return render_template("index.html", error=False)

@app.route("/waiting")
def waiting():
    return render_template("waiting.html")

@app.route("/progress")
def progress():
    task_id = session.get('task_id')
    if task_id and task_id in task_progress:
        return json.dumps(task_progress[task_id])
    return json.dumps({"progress": 0, "status": "not_started"})

@app.route("/result")
def result():
    # 直接读取生成的 out.html
    with open("templates/out.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return render_template_string(html_content)

if __name__ == "__main__":
    app.run(debug=False)