import pandas as pd
from bs4 import BeautifulSoup

def generate_ranked_html_with_css(df, startid, endid, cid, name_order, html_file):
    if df.empty:
        return
    
    # 1. 准备数据
    df = df.copy()
    df['总分'] = df.iloc[:, 1:-1].sum(axis=1)
    
    # 2. 排序
    df_sorted = df.sort_values(by='总分', ascending=False).reset_index(drop=True)
    df_sorted.index += 1
    df_sorted.insert(0, '#', df_sorted.index)
    
    # 3. 生成HTML
    table_html = df_sorted.to_html(index=False, escape=False)
    
    # 4. 创建完整HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>排名表</title>
<style>
  body {{
    font-family: Arial, sans-serif;
    padding: 20px;
    background-color: #fff;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    border: 1px solid #ddd;
  }}
  th, td {{
    padding: 10px;
    text-align: center;
    border: 1px solid #e0e0e0;
  }}
  thead th {{
    background: #fafafa;
    border-bottom: 1px solid #e0e0e0;
  }}
  tbody tr:nth-child(even) {{
    background: #f9f9f9;
  }}
  tbody tr:hover {{
    background: #e3f2fd;
  }}
</style>
</head>
<body>
<h2>成绩排名表</h2>
{table_html}
<br></br>
<a>({startid}, {endid}, {cid})</a>
</body>
</html>
"""
    
    # 5. 添加颜色
    soup = BeautifulSoup(html, 'html.parser')
    tbody = soup.find('tbody')
    for tr in tbody.find_all('tr'):
        tds = tr.find_all('td')
        for idx, td in enumerate(tds[2:], 2):  # 跳过排名和用户名
            try:
                val = int(td.get_text())
                if idx == 2:  # 总分列
                    val /= len(name_order)
                hue = int((min(max(val, 0), 100) / 100) * 120)
                td['style'] = f'color: hsl({hue}, 100%, 40%);'
            except ValueError:
                continue
    
    # 6. 保存文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"已生成 HTML：{html_file}")

def run(df, startid, endid, cid, name_order, outfile):
    generate_ranked_html_with_css(df, startid, endid, cid, name_order, outfile)