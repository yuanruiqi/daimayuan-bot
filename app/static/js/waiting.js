// waiting.js
// 提取自 waiting.html 的所有 JS 逻辑

function updateProgress() {
    fetch('/progress')
        .then(response => response.json())
        .then(data => {
            const progress = data.progress || 0;
            const status = data.status || 'not_started';

            document.getElementById('progress-fill').style.width = progress + '%';

            if (status !== 'running') {
                document.getElementById('cancel-btn').style.display = 'none';
                document.getElementById('home-btn').style.display = '';
            } else {
                document.getElementById('cancel-btn').style.display = '';
                document.getElementById('home-btn').style.display = 'none';
            }

            // 处理暂停状态
            if(data.status=='not_started'|| data.status ==='cancelled'){
                document.getElementById('pause-btn').style.display = 'none';
                document.getElementById('resume-btn').style.display = 'none';
            }else if (data.status === 'paused') {
                document.getElementById('pause-btn').style.display = 'none';
                document.getElementById('resume-btn').style.display = '';
            } else {
                document.getElementById('pause-btn').style.display = '';
                document.getElementById('resume-btn').style.display = 'none';
            }

            if (status === 'completed') {
                window.location.href = '/result';
            } else if (status === 'running') {
                document.getElementById('status-text').textContent =
                    `处理中: ${progress}% (当前ID: ${data.current || 'N/A'})`;
                document.getElementById('info-text').textContent =
                    `扫描范围: ${data.start} 到 ${data.end}`;
            } else if (status === 'error') {
                document.getElementById('status-text').textContent = '处理出错！';
                document.getElementById('info-text').textContent = data.error || '未知错误';
            } else if (status === 'cancelled') {
                document.getElementById('status-text').textContent = '已取消';
            } else if(status === 'paused'){
                document.getElementById('status-text').textContent='已暂停';
            }else {
                document.getElementById('status-text').textContent = '等待任务开始...';
            }
        });
}

document.getElementById('cancel-btn').addEventListener('click', function () {
    document.getElementById('confirm-modal').style.display = 'flex';
});

document.getElementById('confirm-yes').addEventListener('click', function () {
    fetch('/cancel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert('取消任务失败: ' + data.message);
            }
        });
    document.getElementById('confirm-modal').style.display = 'none';
});

document.getElementById('confirm-no').addEventListener('click', function () {
    document.getElementById('confirm-modal').style.display = 'none';
});

document.getElementById('home-btn').addEventListener('click', function () {
    window.location.href = '/';
});

document.getElementById('pause-btn').addEventListener('click', function () {
    fetch('/pause', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 可选：处理暂停成功
        } else {
            alert('暂停失败: ' + data.message);
        }
    });
});
// 恢复按钮事件

document.getElementById('resume-btn').addEventListener('click', function() {
    fetch('/resume', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('pause-btn').style.display = '';
            document.getElementById('resume-btn').style.display = 'none';
            document.getElementById('status-text').textContent = '恢复中...';
        } else {
            alert('恢复失败: ' + data.message);
        }
    });
});
setInterval(updateProgress, 1000);
updateProgress(); // 初始加载
