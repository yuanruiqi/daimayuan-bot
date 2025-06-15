// 任务列表相关DOM元素
const taskListBody = document.getElementById('task-list-body');
const refreshBtn = document.getElementById('refresh-btn');
const autoRefreshCheckbox = document.getElementById('auto-refresh');
const filterButtons = document.querySelectorAll('.filter-btn');
const searchInput = document.getElementById('search-input');
const noTasksMessage = document.getElementById('no-tasks');
const notification = document.getElementById('notification');
const notificationText = document.getElementById('notification-text');
const tottime = parseFloat(document.getElementById('tottime').value);

// 统计元素
const runningCount = document.getElementById('running-count');
const pausedCount = document.getElementById('paused-count');
const completedCount = document.getElementById('completed-count');
const errorCount = document.getElementById('error-count');

let currentFilter = 'all';
let searchQuery = '';
let autoRefreshInterval;
let countdownInterval;

// 页面初始化，加载任务和事件监听
document.addEventListener('DOMContentLoaded', function() {
    fetchTasks();
    setupEventListeners();
    startAutoRefresh();
});

// 设置事件监听器
function setupEventListeners() {
    // 刷新按钮点击事件
    refreshBtn.addEventListener('click', fetchTasks);
    // 自动刷新开关事件
    autoRefreshCheckbox.addEventListener('change', function() {
        if (this.checked) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });
    // 过滤按钮点击事件
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.dataset.filter;
            fetchTasks();
        });
    });
    // 搜索输入框输入事件
    searchInput.addEventListener('input', function() {
        searchQuery = this.value.toLowerCase();
        fetchTasks();
    });
}

// 启动自动刷新
function startAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    fetchTasks();
    // 每3秒自动刷新一次任务列表
    autoRefreshInterval = setInterval(() => {
        fetchTasks();
    }, 3000);
}

// 停止自动刷新
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// 获取任务数据（合并两类任务）
function fetchTasks() {
    Promise.all([
        fetch('/api/tasks').then(r => r.json()),
        fetch('/api/standing_tasks').then(r => r.json())
    ]).then(([normal, standing]) => {
        // 标记任务类型
        const normalTasks = (normal.tasks || []).map(t => ({...t, task_type: 'normal', remaining: t.remaining ?? 0}));
        const standingTasks = (standing.tasks || []).map(t => ({...t, task_type: 'standing', remaining: 0}));
        // 进度百分比兼容
        normalTasks.forEach(t => { if(typeof t.progress !== 'number') t.progress = 0; });
        standingTasks.forEach(t => {
            t.progress = t.end > t.start ? Math.round((t.current-t.start)/(t.end-t.start)*100) : 100;
        });
        renderTaskList([...normalTasks, ...standingTasks], normal.tottime || 0);
    }).catch(error => {
        console.error('获取任务数据失败:', error);
        showNotification('获取任务数据失败', 'error');
    });
}

// 渲染任务列表
function renderTaskList(tasks, totalTime) {
    let filteredTasks = tasks.filter(task => {
        // 根据当前过滤器过滤任务
        if (currentFilter !== 'all' && task.status !== currentFilter) {
            return false;
        }
        // 根据搜索查询过滤任务
        if (searchQuery && 
            !(String(task.contest_id)).toLowerCase().includes(searchQuery) && 
            !(`${task.start}-${task.end}`.includes(searchQuery))) {
            return false;
        }
        return true;
    });
    // 更新统计信息
    updateStats(tasks);
    taskListBody.innerHTML = '';
    if (filteredTasks.length === 0) {
        noTasksMessage.style.display = 'block';
        return;
    }
    noTasksMessage.style.display = 'none';
    // 渲染每个任务的表格行
    filteredTasks.forEach(task => {
        const row = document.createElement('tr');
        let statusText;
        // 根据任务状态设置状态文本
        switch(task.status) {
            case 'running': statusText = '运行中'; break;
            case 'completed': statusText = '已完成'; break;
            case 'cancelled': statusText = '已取消'; break;
            case 'error': statusText = '错误'; break;
            case 'paused': statusText = '已暂停'; break;
            default: statusText = task.status;
        }
        // 任务类型标记
        let typeBadge = task.task_type === 'standing' ? '<span class="badge bg-info">榜单</span>' : '<span class="badge bg-secondary">普通</span>';
        // 剩余时间小于总时间则显示剩余时间，否则显示"等待"
        const remainingDisplay = task.remaining<totalTime?`${task.remaining}s`:`等待`;
        const remainingPercent = task.remaining > 0 ? 
            Math.min(100, (task.remaining / totalTime) * 100) : 0;
        let actionButton = '';
        // 根据任务状态设置操作按钮
        if (task.status === 'paused') {
            actionButton = `<button class="action-btn resume" data-id="${task.id}" data-type="${task.task_type}">
                <i class="fas fa-play"></i> 继续
            </button>`;
        } else if (task.status === 'running') {
            actionButton = `<button class="action-btn pause" data-id="${task.id}" data-type="${task.task_type}">
                <i class="fas fa-pause"></i> 暂停
            </button>`;
        }
        row.innerHTML = `
            <td class="task-id">${task.contest_id} ${typeBadge}</td>
            <td>
                <span class="status-badge status-${task.status}">
                    ${statusText}
                </span>
            </td>
            <td>${task.start} - ${task.end}</td>
            <td>
                ${task.progress}%
                <div class="progress-container">
                    <div class="progress-bar" style="width: ${task.progress}%"></div>
                </div>
            </td>
            <td>
                ${remainingDisplay}
                <div class="progress-container">
                    <div class="progress-bar" style="width: ${remainingPercent}%"></div>
                </div>
            </td>
            <td>
                <button class="action-btn view" data-id="${task.id}" data-type="${task.task_type}">
                    <i class="fas fa-eye"></i> 查看
                </button>
                ${actionButton}
            </td>
        `;
        taskListBody.appendChild(row);
    });
    // 为暂停和继续按钮设置点击事件
    document.querySelectorAll('.pause').forEach(btn => {
        btn.addEventListener('click', () => pauseTask(btn.dataset.id, btn.dataset.type));
    });
    document.querySelectorAll('.resume').forEach(btn => {
        btn.addEventListener('click', () => resumeTask(btn.dataset.id, btn.dataset.type));
    });
    document.querySelectorAll('.view').forEach(btn => {
        btn.addEventListener('click', () => viewTask(btn.dataset.id, btn.dataset.type));
    });
    // 启动倒计时
    startCountdown(totalTime);
}

// 更新统计信息
function updateStats(tasks) {
    const stats = {
        running: 0,
        paused: 0,
        completed: 0,
        error: 0
    };
    // 统计各个状态的任务数量
    tasks.forEach(task => {
        if (stats.hasOwnProperty(task.status)) {
            stats[task.status]++;
        }
    });
    runningCount.textContent = stats.running;
    pausedCount.textContent = stats.paused;
    completedCount.textContent = stats.completed;
    errorCount.textContent = stats.error;
}

// 暂停任务
function pauseTask(taskId, taskType) {
    if (taskType === 'standing') {
        fetch(`/standing/pause/${taskId}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                showNotification('榜单任务已暂停', 'success');
                setTimeout(fetchTasks, 500);
            })
            .catch(error => {
                showNotification('暂停榜单任务失败', 'error');
            });
    } else {
        fetch(`/api/task/${taskId}/pause`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    setTimeout(fetchTasks, 500);
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('暂停任务失败', 'error');
            });
    }
}

// 恢复任务
function resumeTask(taskId, taskType) {
    if (taskType === 'standing') {
        fetch(`/standing/start/${taskId}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                showNotification('榜单任务已继续', 'success');
                setTimeout(fetchTasks, 500);
            })
            .catch(error => {
                showNotification('继续榜单任务失败', 'error');
            });
    } else {
        fetch(`/api/task/${taskId}/resume`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    setTimeout(fetchTasks, 500);
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('继续任务失败', 'error');
            });
    }
}

// 查看任务
function viewTask(taskId, taskType) {
    if (taskType === 'standing') {
        window.location.href = `/standing/data/${taskId}`;
    } else {
        // 原有逻辑
        const form = document.createElement('form');
        form.action = '/selecttask';
        form.method = 'POST';
        form.style.display = 'none';
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'task_id';
        input.value = taskId;
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
    }
}

// 显示通知
function showNotification(message, type) {
    notificationText.textContent = message;
    notification.className = `notification ${type} show`;
    const icon = notification.querySelector('i');
    if (type === 'success') {
        icon.className = 'fas fa-check-circle';
    } else if (type === 'error') {
        icon.className = 'fas fa-exclamation-circle';
    } else {
        icon.className = 'fas fa-info-circle';
    }
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// 启动倒计时，实时更新剩余时间
function startCountdown(totalTime) {
    if (countdownInterval) clearInterval(countdownInterval);
    countdownInterval = setInterval(() => {
        document.querySelectorAll('#task-list-body tr').forEach(row => {
            const td = row.cells[4];
            let text = td.childNodes[0].textContent.trim();
            if (text.endsWith('s')) {
                let sec = parseFloat(text);
                if (sec > 0) sec-=0.03;
                sec=Math.max(sec,0)
                td.childNodes[0].textContent = sec.toFixed(2) + 's';
                const pct = Math.min(100, (sec / totalTime) * 100);
                td.querySelector('.progress-bar').style.width = pct + '%';
            }
        });
    }, 30);
}
