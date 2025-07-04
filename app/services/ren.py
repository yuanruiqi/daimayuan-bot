from bs4 import BeautifulSoup
from jinja2 import Template, Environment, FileSystemLoader
import logging

from app.config import CONFIG, config

# 获取日志记录器
logger = logging.getLogger(__name__)

def run(df, startid, endid, cid, name_order, submission_history, problem_map):
    """
    入口函数：处理数据并生成 standing.html 所需 context。
    """
    df = prepare_data(df)
    df_sorted = sort_and_rank(df)
    # 处理时间轴数据
    timeline_data = []
    for username, problems in submission_history.items():
        for problem_id, submissions in problems.items():
            for sub_id, score in submissions:
                timeline_data.append({
                    'time': sub_id,  # 使用提交ID作为时间点
                    'submissionId': str(sub_id),
                    'username': username,
                    'problemId': str(problem_id),
                    'score': score
                })
    # 按提交ID排序
    timeline_data.sort(key=lambda x: x['time'])
    # 渲染表格HTML
    table_html = render_table(df_sorted, name_order, submission_history, problem_map)
    # 构建context字典
    context = build_html(table_html, startid, endid, cid, timeline_data)
    logger.info(f"{startid},{endid},{cid},已生成 HTML context")
    return context

def prepare_data(df):
    """
    预处理数据，计算总分。
    """
    df = df.copy()
    df['总分'] = df.iloc[:, 1:-1].sum(axis=1)
    return df

def sort_and_rank(df):
    """
    按总分降序排序并添加排名列。
    """
    df = df.sort_values('总分', ascending=False)
    df.insert(0, '排名', range(1, len(df) + 1))
    return df

def build_html(table_html, startid, endid, cid, timeline_data):
    """
    返回渲染 standing.html 所需的 context 字典，供 Flask 的 render_template 使用。
    """
    return {
        'table_html': table_html,
        'startid': startid,
        'endid': endid,
        'cid': cid,
        'timeline_data': timeline_data
    }

def render_table(df, name_order, submission_history, problem_map):
    """
    渲染成绩表格为HTML。
    """
    html = []
    html.append('<table id="rank-table" class="table table-hover">')
    
    # 表头
    html.append('<thead><tr>')
    for col in df.columns:
        if col == '排名':
            th_text = col
        elif col == '用户名':
            th_text = col
        elif problem_map and str(col).isdigit() and int(col) in problem_map:
            th_text = f'{col}：{problem_map[int(col)]}'
        else:
            th_text = col
        html.append(f'<th data-sort>{th_text}</th>')
    html.append('</tr></thead>')
    
    # 表格内容
    html.append('<tbody>')
    for _, row in df.iterrows():
        html.append('<tr>')
        for col in df.columns:
            cell_value = row[col]
            if col == '用户名':
                username = cell_value
                cell = f'<td class="username-cell">{cell_value}</td>'
            elif col == '排名':
                cell = f'<td class="rank-cell">{cell_value}</td>'
            else:
                # 添加提交历史信息
                history_info = ''
                if str(col).isdigit() and username in submission_history and int(col) in submission_history[username]:
                    history_items = submission_history[username][int(col)]
                    history_items.sort(reverse=True)
                    history_html = []
                    for sub_id, score in history_items:
                        history_html.append(
                            f'<div class="history-item">'
                            f'<a href="http://oj.daimayuan.top/submission/{sub_id}" class="submission-link">#{sub_id}</a>'
                            f'<span class="score">{score}</span>'
                            f'</div>'
                        )
                    history_info = f'<div class="submission-history">{chr(10).join(history_html)}</div>'
                # 判断是否为数字分数列
                try:
                    sort_val = float(cell_value)
                    cell = f'<td class="score-cell" data-sort="{sort_val}">{history_info}<span class="score-text">{cell_value}</span></td>'
                except Exception:
                    cell = f'<td class="score-cell">{history_info}<span class="score-text">{cell_value}</span></td>'
            html.append(cell)
        html.append('</tr>')
    html.append('</tbody></table>')
    
    return chr(10).join(html)

