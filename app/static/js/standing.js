document.getElementById('timestamp').textContent = new Date().toLocaleString();

  document.addEventListener('DOMContentLoaded', function() {
    // 自定义分数排序函数
    Tablesort.extend('score', function(item) {
        return item.match(/^-?\d+$/);
    }, function(a, b) {
        a = parseInt(a);
        b = parseInt(b);
        return a - b;
    });

    // 初始化表格排序
    const table = document.querySelector('table');
    new Tablesort(table, {
        descending: true,  // 默认降序
        sortAttribute: 'data-sort',  // 使用data-sort属性
        column: 0  // 默认按第一列排序
    });

    // 添加表头点击事件
    document.querySelectorAll('th').forEach(th => {
        th.addEventListener('click', function() {
            // 移除其他表头的排序标记
            document.querySelectorAll('th').forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            // 添加当前表头的排序标记
            this.classList.add(this.classList.contains('sort-asc') ? 'sort-desc' : 'sort-asc');
        });
    });

    // 搜索功能
    document.getElementById('searchInput').addEventListener('input', function(e) {
      const searchTerm = e.target.value.toLowerCase().trim();
      const rows = document.querySelectorAll('#rank-table tbody tr');
      rows.forEach(row => {
        const username = row.cells[1].textContent.toLowerCase();
        row.style.display = username.includes(searchTerm) ? '' : 'none';
      });
    });

    // 提交历史交互
    document.querySelectorAll('.score-cell').forEach(cell => {
      const history = cell.querySelector('.submission-history');
      if (history) {
        // 点击单元格时显示历史记录
        cell.addEventListener('click', function(e) {
          e.stopPropagation();
          const allHistories = document.querySelectorAll('.submission-history');
          allHistories.forEach(h => {
            if (h !== history) {
              h.style.display = 'none';
            }
          });
          history.style.display = history.style.display === 'none' ? 'block' : 'none';
        });
      }
    });

    // 点击页面其他地方时隐藏所有历史记录
    document.addEventListener('click', function(e) {
      if (!e.target.closest('.score-cell')) {
        document.querySelectorAll('.submission-history').forEach(history => {
          history.style.display = 'none';
        });
      }
    });

    // 分数颜色插值色带
    const colorScale = chroma.scale(['#e74c3c', '#f39c12', '#27ae60']).domain([0, 50, 100]);
    document.querySelectorAll('#rank-table tbody td.score-cell').forEach(cell => {
      let scoreSpan = cell.querySelector('.score-text');
      if (!scoreSpan) {
        const val = cell.childNodes[0] && cell.childNodes[0].nodeType === 3 ? cell.childNodes[0].textContent : cell.textContent;
        scoreSpan = document.createElement('span');
        scoreSpan.className = 'score-text';
        scoreSpan.textContent = val.trim();
        if (cell.childNodes[0] && cell.childNodes[0].nodeType === 3) {
          cell.childNodes[0].replaceWith(scoreSpan);
        } else {
          cell.innerHTML = '';
          cell.appendChild(scoreSpan);
        }
      }
      const score = parseFloat(scoreSpan.textContent);
      const username = cell.parentElement.cells[1].textContent;
      const ths = cell.closest('table').querySelectorAll('thead th');
      const problemName = ths[cell.cellIndex].textContent.trim();
      const isTotalScore = cell.cellIndex === cell.parentElement.cells.length - 1;
      const maxScore = isTotalScore ? 300 : 100;
      cell.setAttribute('data-max', maxScore);
      if (score < 0) {
        scoreSpan.style.color = '#95a5a5';
      } else {
        let percent = Math.max(0, Math.min(1, score / maxScore));
        scoreSpan.style.color = colorScale(percent * 100).hex();
        scoreSpan.style.background = '';
        scoreSpan.style.backgroundClip = '';
        scoreSpan.style.webkitBackgroundClip = '';
      }
      // 获取提交历史
      const history = cell.querySelector('.submission-history');
      if (history) {
        const historyItems = history.querySelectorAll('.history-item');
        let maxScore = -1;
        let lastScore = -1;
        historyItems.forEach(item => {
          const itemScore = parseFloat(item.querySelector('.score').textContent);
          if (itemScore > maxScore) {
            maxScore = itemScore;
          }
          lastScore = itemScore;
        });
        cell.setAttribute('data-bs-toggle', 'tooltip');
        if (maxScore >= 0) {
          cell.setAttribute('title', `${username} 在 ${problemName} 的最高分: ${maxScore}分`);
        } else {
          cell.setAttribute('title', `${username} 在 ${problemName} 的得分: ${score}分`);
        }
      } else {
        cell.setAttribute('data-bs-toggle', 'tooltip');
        cell.setAttribute('title', `${username} 在 ${problemName} 的得分: ${score}分`);
      }
    });

    // 初始化工具提示
    $(function () {
      $('[data-bs-toggle="tooltip"]').tooltip({
        trigger: 'hover',
        placement: 'top'
      });
    });

    // 计算统计信息
    const scores = Array.from(document.querySelectorAll('#rank-table tbody td:last-child'))
      .map(td => parseFloat(td.textContent) || 0);

    if (scores.length > 0) {
      document.getElementById('totalCount').textContent = scores.length;
      document.getElementById('maxScore').textContent = Math.max(...scores).toFixed(1);
      const sum = scores.reduce((a, b) => a + b, 0);
      document.getElementById('avgScore').textContent = (sum / scores.length).toFixed(1);
      const sortedScores = [...scores].sort((a, b) => a - b);
      const mid = Math.floor(sortedScores.length / 2);
      const median = sortedScores.length % 2 !== 0 
        ? sortedScores[mid] 
        : (sortedScores[mid - 1] + sortedScores[mid]) / 2;
      document.getElementById('medianScore').textContent = median.toFixed(1);
      
      // 绘制图表
      const ctx = document.getElementById('scoreDistributionChart').getContext('2d');
      const maxScore = Math.max(...scores);
      const binCount = 10;
      const binSize = Math.ceil(maxScore / binCount);
      const scoreRanges = [];
      for (let i = 0; i < binCount; i++) {
        const start = i * binSize;
        const end = (i + 1) * binSize;
        scoreRanges.push(`${start}-${end}`);
      }
      const data = new Array(binCount).fill(0);
      scores.forEach(score => {
        const binIndex = Math.min(Math.floor(score / binSize), binCount - 1);
        data[binIndex]++;
      });

      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: scoreRanges,
          datasets: [{
            label: '分数分布',
            data: data,
            backgroundColor: 'rgba(44, 111, 187, 0.7)',
            borderColor: 'rgba(44, 111, 187, 1)',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: false },
            title: { 
              display: true, 
              text: '总分分布', 
              font: { size: 16 },
              color: '#2c3e50'
            }
          },
          scales: {
            y: { 
              beginAtZero: true, 
              title: { 
                display: true, 
                text: '人数',
                color: '#2c3e50'
              }, 
              ticks: { 
                precision: 0,
                color: '#6c757d'
              } 
            },
            x: { 
              title: { 
                display: true, 
                text: '总分区间',
                color: '#2c3e50'
              },
              ticks: {
                color: '#6c757d'
              }
            }
          }
        }
      });
    }

    // 时间轴功能实现
    const slider = document.getElementById('timelineSlider');
    const prevBtn = document.getElementById('prevSnapshot');
    const nextBtn = document.getElementById('nextSnapshot');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const speedSelect = document.getElementById('playbackSpeed');
    const animationToggle = document.getElementById('animationToggle');
    const currentTimeSpan = document.getElementById('currentTime');
    const currentSubmissionSpan = document.getElementById('currentSubmission');
    
    // 从后端获取的时间轴数据
    const timelineData = window.timelineData || [];
    let currentIndex = timelineData.length - 1;
    let isPlaying = false;
    let playInterval = null;
    let lastRankings = new Map(); // 存储上一次的排名
    
    // 自动播放控制
    function togglePlay() {
        isPlaying = !isPlaying;
        if (isPlaying) {
            playPauseBtn.textContent = '⏸';
            playPauseBtn.classList.add('playing');
            startPlayback();
        } else {
            playPauseBtn.textContent = '▶';
            playPauseBtn.classList.remove('playing');
            stopPlayback();
        }
    }
    
    function startPlayback() {
        const speed = parseFloat(speedSelect.value);
        const interval = 1000 / speed; // 基础间隔1秒
        
        playInterval = setInterval(() => {
            if (currentIndex < timelineData.length - 1) {
                currentIndex++;
                updateTimelineInfo();
            } else {
                stopPlayback();
                isPlaying = false;
                playPauseBtn.textContent = '▶';
                playPauseBtn.classList.remove('playing');
            }
        }, interval);
    }
    
    function stopPlayback() {
        if (playInterval) {
            clearInterval(playInterval);
            playInterval = null;
        }
    }
    
    // 速度变化时更新播放间隔
    speedSelect.addEventListener('change', function() {
        if (isPlaying) {
            stopPlayback();
            startPlayback();
        }
    });
    
    // 播放按钮事件
    playPauseBtn.addEventListener('click', togglePlay);
    

    function triggerAnimationOnce(el, className) {
      if (!el || !className) return;

      // 如果已经在动画中，不重复添加类
      if (el.classList.contains(className)) return;

      // 强制触发重绘，再添加类
      el.classList.remove(className); // 保证状态干净
      requestAnimationFrame(() => {
          el.classList.add(className);

          el.addEventListener('animationend', () => {
              el.classList.remove(className);
          }, { once: true });
      });
    }
    // 更新表格数据并添加动画效果
    function updateTableData(submissionId) {
        const table = document.getElementById('rank-table');
        const tbody = table.tBodies[0];
        const rows = Array.from(tbody.rows);

        // 保存当前排名与分数（包括每题得分）
        const currentRankings = new Map();
        const currentTotalScores = new Map();
        const currentProblemScores = new Map(); // key: username|problemId
        const headerCells = Array.from(table.tHead.rows[0].cells);
        const problemCols = headerCells
            .map((th, idx) => ({ pid: th.textContent.split('：')[0].trim(), idx }))
            .filter(item => item.idx > 1 && item.idx < headerCells.length - 1);

        rows.forEach(row => {
            const username = row.querySelector('.username-cell').textContent;
            currentRankings.set(username, parseInt(row.querySelector('.rank-cell').textContent, 10));
            // 总分
            const totalIdx = headerCells.length - 1;
            const total = parseFloat(row.cells[totalIdx].querySelector('.score-text').textContent) || 0;
            currentTotalScores.set(username, total);
            // 每题分数
            problemCols.forEach(({ pid, idx }) => {
                const val = parseFloat(row.cells[idx].querySelector('.score-text').textContent) || 0;
                currentProblemScores.set(`${username}|${pid}`, val);
            });
        });

        // 重置所有分数
        rows.forEach(row => {
            problemCols.forEach(({ idx }) => {
                const span = row.cells[idx].querySelector('.score-text');
                if (span) span.textContent = '0';
            });
        });

        // 按时间线数据更新分数
        const endIndex = timelineData.findIndex(item => item.submissionId === submissionId);
        timelineData.slice(0, endIndex + 1).forEach(item => {
            const row = rows.find(r => r.querySelector('.username-cell').textContent === item.username);
            const col = problemCols.find(pc => pc.pid === item.problemId);
            if (row && col) {
                const span = row.cells[col.idx].querySelector('.score-text');
                if (span) span.textContent = item.score;
            }
        });

        // 每题分数变化动画
        rows.forEach(row => {
            const username = row.querySelector('.username-cell').textContent;
            problemCols.forEach(({ pid, idx }) => {
                const span = row.cells[idx].querySelector('.score-text');
                if (!span) return;
                const oldScore = currentProblemScores.get(`${username}|${pid}`) || 0;
                const newScore = parseFloat(span.textContent) || 0;
                if (newScore !== oldScore) {
                    // pulse 动画
                    triggerAnimationOnce(span, 'score-change');
                }
            });
        });

        // 重新计算总分并检测变化
        const newTotalScores = new Map();
        rows.forEach(row => {
            const username = row.querySelector('.username-cell').textContent;
            let total = 0;
            problemCols.forEach(({ idx }) => {
                total += parseFloat(row.cells[idx].querySelector('.score-text').textContent) || 0;
            });
            newTotalScores.set(username, total);
            // 更新总分单元格
            const totalCell = row.cells[headerCells.length - 1];
            const totalSpan = totalCell.querySelector('.score-text');
            const oldTotal = currentTotalScores.get(username) || 0;
            totalSpan.textContent = total;
            if (total !== oldTotal) {
              triggerAnimationOnce(totalSpan, 'score-change');
                
            }
        });

        // 计算新排名
        const sorted = Array.from(newTotalScores.entries()).sort((a, b) => b[1] - a[1]);
        const oldPositions = new Map(); rows.forEach((r, i) => oldPositions.set(r.querySelector('.username-cell').textContent, i));

        // 更新排名并重排
        const newRows = [];
        sorted.forEach(([username], rank) => {
            const row = rows.find(r => r.querySelector('.username-cell').textContent === username);
            if (row) {
                row.querySelector('.rank-cell').textContent = (rank + 1).toString();
                newRows.push(row);
            }
        });
        newRows.forEach(r => tbody.appendChild(r));

        // 颜色渲染
        newRows.forEach(row => {
            const username = row.querySelector('.username-cell').textContent;
            problemCols.concat({ pid: 'total', idx: headerCells.length - 1 }).forEach(({ idx }) => {
                const span = row.cells[idx].querySelector('.score-text');
                if (!span) return;
                const score = parseFloat(span.textContent) || 0;
                const max = (idx === headerCells.length - 1) ? 300 : 100;
                const p = Math.max(0, Math.min(1, score / max));
                span.style.color = colorScale(p * 100).hex();
                span.style.background = '';
            });
        });

        // 排名动画
        if (animationToggle.checked && currentRankings.size) {
            newRows.forEach((row, newIdx) => {
                const username = row.querySelector('.username-cell').textContent;
                const oldIdx = oldPositions.get(username);
                if (oldIdx !== newIdx) {
                    const dist = (oldIdx - newIdx) * row.offsetHeight;
                    row.style.setProperty('--move-distance', `${dist}px`);
                    const className = oldIdx > newIdx ? 'rank-up' : 'rank-down';
                    triggerAnimationOnce(row, className);
                }
            });
        }

        // 重置提示
        $('[data-bs-toggle="tooltip"]').tooltip('dispose').tooltip({ trigger:'hover', placement:'top' });
        lastRankings = new Map(currentRankings);
    }


    
    // 更新显示信息
    function updateTimelineInfo() {
        const data = timelineData[currentIndex];
        currentTimeSpan.textContent = `当前提交: #${data.submissionId}`;
        currentSubmissionSpan.textContent = `提交编号: ${data.submissionId}`;
        slider.value = (currentIndex / (timelineData.length - 1)) * 100;
        
        // 更新表格数据
        updateTableData(data.submissionId);
        
        // 更新按钮状态
        prevBtn.disabled = currentIndex === 0;
        nextBtn.disabled = currentIndex === timelineData.length - 1;
    }
    
    // 滑动条事件
    slider.addEventListener('input', function() {
        currentIndex = Math.round((this.value / 100) * (timelineData.length - 1));
        updateTimelineInfo();
    });
    
    // 按钮事件
    prevBtn.addEventListener('click', function() {
        if (currentIndex > 0) {
            currentIndex--;
            updateTimelineInfo();
        }
    });
    
    nextBtn.addEventListener('click', function() {
        if (currentIndex < timelineData.length - 1) {
            currentIndex++;
            updateTimelineInfo();
        }
    });
    
    // 初始化显示
    updateTimelineInfo();
    
    // 添加键盘控制
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowLeft' && !prevBtn.disabled) {
            prevBtn.click();
        } else if (e.key === 'ArrowRight' && !nextBtn.disabled) {
            nextBtn.click();
        }
    });
  });

  // 全屏功能实现
  const toggleFullscreenBtn = document.getElementById('toggleFullscreen');
  const exitFullscreenBtn = document.getElementById('exitFullscreen');
  
  toggleFullscreenBtn.addEventListener('click', function() {
    document.body.classList.add('fullscreen-mode');
    window.scrollTo(0, 0);
  });
  
  exitFullscreenBtn.addEventListener('click', function() {
    document.body.classList.remove('fullscreen-mode');
  });
  
  // ESC键退出全屏
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.body.classList.contains('fullscreen-mode')) {
      document.body.classList.remove('fullscreen-mode');
    }
  });
