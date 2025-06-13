# daimayuan-bot

## 简介

**daimayuan-bot** 是一个用于自动抓取、分析并可视化比赛提交记录的网页应用。它支持多用户并发任务、任务持久化、任务暂停/恢复/取消、排行榜与提交历史可视化、统计分析等功能。适用于 OJ 比赛成绩统计、数据分析和展示。

## 特性

- 支持多用户并发任务
- 任务列表与持久化管理
- 实时进度、暂停、恢复、取消任务
- 提交历史可视化，支持分数分布统计
- 响应式网页前端，交互友好
- 支持多种 OJ 平台（如 UOJ 等，具体见配置）

## 快速开始

1. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

2. **配置**

   - 修改 `config.yaml`，填写 `down.UOJSESSID` 以及必要的 secret key。

3. **运行**

   ```bash
   python3 wsgi.py
   ```

4. **访问**

   打开浏览器访问 [http://localhost:5000](http://localhost:5000)

## 文件结构

- `app.py`：主程序入口
- `app/templates/`：前端页面模板（排行榜、任务列表、等待页等）
- `app/services/`：核心后端逻辑（数据抓取、分析、渲染）
- `config.yaml`：配置文件
- `README.md`：项目说明

## 主要页面

- `/`：输入比赛参数，发起新任务
- `/tasklist`：任务列表与管理
- `/waiting`：任务进度与控制
- `/result`：排行榜与统计分析展示

## 注意事项

- 请确保配置文件填写正确，尤其是 OJ Cookie 等敏感信息。
- 任务数据默认保存 10 分钟，超时自动清理。

## 许可证

MIT License

---

# daimayuan-bot

## Introduction

**daimayuan-bot** is a web application for automatically fetching, analyzing, and visualizing contest submission records. It supports concurrent multi-user tasks, persistent task management, pause/resume/cancel, ranking board with submission history, and statistical analysis. Suitable for OJ contest result statistics, data analysis, and visualization.

## Features

- Multi-user concurrent task support
- Task list and persistence management
- Real-time progress, pause, resume, cancel
- Submission history visualization, score distribution statistics
- Responsive web frontend, user-friendly interaction
- Supports multiple OJ platforms (UOJ, etc. — see config)

## Quick Start

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure**

   - Edit `config.yaml`, set `down.UOJSESSID` and secret key as needed.

3. **Run**

   ```bash
   python3 wsgi.py
   ```

4. **Access**

   Open [http://localhost:5000](http://localhost:5000) in your browser.

## Directory Structure

- `app.py`: Main entry point
- `app/templates/`: Frontend templates (ranking, task list, waiting, etc.)
- `app/services/`: Core backend logic (fetch, analysis, render)
- `config.yaml`: Configuration file
- `README.md`: Project documentation

## Main Pages

- `/`: Input contest parameters, start new task
- `/tasklist`: Task list and management
- `/waiting`: Task progress and control
- `/result`: Ranking and statistics

## Notes

- Make sure to fill in the config file correctly, especially OJ cookies and sensitive info.
- Task data is kept for 10 minutes by default, and will be cleaned up after timeout.

## License

MIT License