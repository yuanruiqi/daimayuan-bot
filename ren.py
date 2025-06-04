import pandas as pd
from bs4 import BeautifulSoup
from jinja2 import Template
import config

def run(df, startid, endid, cid):
    if df.empty:
        return

    df = prepare_data(df)
    df_sorted = sort_and_rank(df)
    table_html = generate_table_html(df_sorted)
    html = build_html(table_html, startid, endid, cid)
    html = add_cell_coloring(html, df_sorted)
    # print(f"已生成 HTML：{html_file}")
    return html

def prepare_data(df):
    df = df.copy()
    df['总分'] = df.iloc[:, 1:-1].sum(axis=1)
    return df

def sort_and_rank(df):
    df_sorted = df.sort_values(by='总分', ascending=False).reset_index(drop=True)
    df_sorted.index += 1
    df_sorted.insert(0, '#', df_sorted.index)
    return df_sorted

def generate_table_html(df_sorted):
    return df_sorted.to_html(
        index=False,
        escape=False,
        classes='table table-striped table-bordered',
        table_id='rank-table'
    )

def build_html(table_html, startid, endid, cid):
    with open(config.general.outtemplate, 'r', encoding='utf-8') as f:
        html_template = f.read()
    template = Template(html_template)
    return template.render(
        table_html=table_html,
        startid=startid,
        endid=endid,
        cid=cid
    )

def add_cell_coloring(html, df_sorted):
    soup = BeautifulSoup(html, 'html.parser')
    tbody = soup.find('tbody')
    if tbody:
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            for idx, td in enumerate(tds[2:], 2):  # 跳过序号和用户名列
                try:
                    val = int(td.get_text())
                    td['data-sort-value'] = val
                    if idx == len(tds) - 1:
                        max_score = 100 * (len(tds) - 3)  # 假设每题满分100
                        scaled_val = min(val, max_score) / max_score
                    else:
                        scaled_val = min(val, 100) / 100
                    hue = int(120 * scaled_val)  # 绿色到红色
                    td['style'] = f'color: hsl({hue}, 100%, 40%);'
                except ValueError:
                    continue
    return str(soup)

# def save_html(html, html_file):
#     with open(html_file, 'w', encoding='utf-8') as f:
#         f.write(html)
