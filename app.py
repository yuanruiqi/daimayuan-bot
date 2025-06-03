# app.py

from flask import Flask, request, render_template, render_template_string, redirect, url_for
from run import run
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            a = int(request.form["a"])
            b = int(request.form["b"])
            c = int(request.form["c"])
            if os.path.exists('lock'):
                return render_template("index.html", error = True)
            with open('lock', 'w') as f:
                f.write('working')
            run(a, b, c)  # 生成 out.html
            os.remove('lock')
            return redirect(url_for("result"))
        except ValueError:
            return "请输入三个整数！小概率未知错误。"
    return render_template("index.html", error = False)

@app.route("/result")
def result():
    # 直接读取生成的 out.html
    with open("templates/out.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return render_template_string(html_content)

if __name__ == "__main__":
    app.run(debug=False)
