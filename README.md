# daimayuan-bot

## 简介 | Introduction

**daimayuan-bot** 是一个用于自动抓取、分析并可视化比赛提交记录的网页应用。支持多用户并发任务、任务持久化、暂停/恢复/取消、排行榜与提交历史可视化、统计分析、历史记录等功能。适用于 OJ 比赛成绩统计、数据分析和展示。

**daimayuan-bot** is a web application for automatically fetching, analyzing, and visualizing contest submission records. It supports concurrent multi-user tasks, persistent task management, pause/resume/cancel, ranking board, submission history, statistical analysis, historical records and so on. Suitable for OJ contest result statistics, data analysis, and visualization.

## 特性 | Features

- 支持多用户并发任务 | Multi-user concurrent task support
- 任务列表与持久化管理 | Task list and persistence management
- 实时进度、暂停、恢复、取消任务 | Real-time progress, pause, resume, cancel
- 提交历史可视化，分数分布统计 | Submission history visualization, score distribution statistics
- 响应式网页前端，交互友好 | Responsive web frontend, user-friendly interaction

## 快速开始 | Quick Start

1. **安装依赖 | Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **配置 | Configure**

   - 修改 `config.yaml`，填写 `down.cookies.UOJSESSID`。
   - 如需设置 secret key，请在 `app/config.py` 中修改。

3. **运行 | Run**

   ```bash
   python3 wsgi.py
   ```

4. **访问 | Access**

   打开浏览器访问 [http://localhost:5000](http://localhost:5000)
   Open [http://localhost:5000](http://localhost:5000) in your browser.

## 文件结构 | Directory Structure

- `wsgi.py`：主程序入口 | Main entry point
- `app/templates/`：前端页面模板 | Frontend templates
- `app/services/`：核心后端逻辑 | Core backend logic
- `config.yaml`：配置文件 | Configuration file
- `README.md`：项目说明 | Project documentation

## 主要页面 | Main Pages

- `/`：输入比赛参数，发起新任务 | Input contest parameters, start new task
- `/tasklist`：任务列表与管理 | Task list and management
- `/waiting`：任务进度与控制 | Task progress and control
- `/result`：排行榜与统计分析展示 | Ranking and statistics

## 注意事项 | Notes

- 请确保配置文件填写正确，尤其是 OJ Cookie 等敏感信息。
- 任务数据默认保存 10 分钟，超时自动清理。可以配置。
- Make sure to fill in the config file correctly, especially OJ cookies and sensitive info.
- Task data is kept for 10 minutes by default, and will be cleaned up after timeout. It can be configured.

## 许可证 | License

MIT License
