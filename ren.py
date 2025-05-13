import pandas as pd
from bs4 import BeautifulSoup

def generate_ranked_html_with_css(csv_file: str, html_file: str):
    # 1. 读取 CSV 并预处理
    df = pd.read_csv(csv_file, skipinitialspace=True)
    df.rename(columns={df.columns[0]: 'Username'}, inplace=True)
    df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')

    # 2. 计算总分并排序、加排名
    df['Score'] = df.iloc[:, 1:].sum(axis=1)
    df_sorted = df.sort_values(by='Score', ascending=False).reset_index(drop=True)
    df_sorted.index += 1
    df_sorted.insert(0, '#', df_sorted.index)

    # 3. 重新排列列，将 Score 放在 Username 之后
    problem_cols = list(df.columns[1:-1])
    new_order = ['#', 'Username', 'Score'] + problem_cols
    df_sorted = df_sorted[new_order]

    # 4. 生成无样式 HTML（先不做任何正则替换）
    table_html = df_sorted.to_html(index=False, escape=False)

    # 5. 整体 HTML + 内联 CSS（移除 class 样式）
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
</body>
</html>
"""

    # 6. 给非排名列的数值单元格设置渐变颜色（使用 style 属性）
    def score_to_color(val: float) -> str:
        val = max(0, min(val, 100))
        hue = int((val / 100) * 120)  # 红到绿：0° → 120°
        return f"hsl({hue}, 100%, 40%)"

    soup = BeautifulSoup(html, 'html.parser')
    tbody = soup.find('tbody')
    for tr in tbody.find_all('tr'):
        tds = tr.find_all('td')
        for idx, td in enumerate(tds[2:]):  # 跳过排名（#）和用户名列，从分数列开始
            text = td.get_text(strip=True)
            try:
                val = float(text)
                if (idx == 0):
                    val /= 3
                color = score_to_color(val)
                td['style'] = td.get('style', '') + f'color: {color};'
            except ValueError:
                continue

    # 7. 写文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"已生成带 CSS 渐变色的 HTML：{html_file}")

def run():
    generate_ranked_html_with_css(
        csv_file='tab.csv',
        html_file='templates/out.html'
    )
