// standing-anim.js
// 专门用于榜单排名变动动画的 JS 文件

// 触发一次动画的工具函数
function triggerAnimationOnce(el, className) {
  if (!el || !className) return;
  if (el.classList.contains(className)) return;
  el.classList.remove(className); // 保证状态干净
  requestAnimationFrame(() => {
    el.classList.add(className);
    el.addEventListener('animationend', () => {
      el.classList.remove(className);
    }, { once: true });
  });
}

// 榜单排名动画应用函数
function applyRankAnimation(rows, oldPositions, newRows) {
  newRows.forEach((row, newIdx) => {
    const username = row.querySelector('.username-cell').textContent;
    const oldIdx = oldPositions.get(username);
    if (oldIdx !== newIdx) {
      const dist = (oldIdx - newIdx) * row.offsetHeight;
      row.style.setProperty('--move-distance', `${dist}px`);
      const className = oldIdx > newIdx ? 'rank-up' : 'rank-down';
      const rankCell = row.querySelector('.rank-cell');
      if (rankCell) triggerAnimationOnce(rankCell, className);
    }
  });
}

// 导出函数（如需模块化可用）
window.standingAnim = { triggerAnimationOnce, applyRankAnimation };
