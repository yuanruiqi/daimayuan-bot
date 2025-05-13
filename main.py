import requests
from bs4 import BeautifulSoup
import time
import csv

# 请求头, 模拟浏览器请求
headers = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/90.0.4430.93 Safari/537.36')
}

# 将你的登录 cookie 信息复制到下面
cookies = {
  "uoj_preferred_language": "C++",
  "uoj_remember_token": "mDS03jtKJfCoPUnqfl33iJaY6EkniCpR4MFRxx1UKwpJDugh5Exr0MHd6Kwl",
  "uoj_remember_token_checksum": "74634670b43e158cc40797194b6f5785",
  "uoj_username": "wrkwrk",
  "uoj_username_checksum": "45c62b8291abd741bd20010f283e39d7",
  "UOJSESSID": "vsfn2609891aiuusnrqpsssta7"
}



# 设置起始的 submission ID
start_id = 3932924
# 可根据需要设置结束的 ID（如果未知，也可以设计成一个无限循环，遇到错误就 break）
end_id = 3932929

base_url = 'http://oj.daimayuan.top/submission/'

start_id, end_id = map(int, input().split())

out_file = open('tab', 'w')

score_dict = {}

for submission_id in range(start_id, end_id + 1):
    url = f"{base_url}{submission_id}"
    # print(url)
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
    except Exception as e:
        print(f"[错误] 请求 {url} 时出现异常: {e}")
        break

    if response.status_code == 200:
        # 使用 BeautifulSoup 解析返回的 HTML 内容
        soup = BeautifulSoup(response.text, 'html.parser')
        # print(soup)
        # 举例：提取页面的标题
        # title_tag = soup.find('title')
        # title = title_tag.string.strip() if title_tag else '无标题'
        # print(f"Submission ID: {submission_id}  -- Title: {title}")
        try:

            table = soup.find(class_ = "table-responsive")
            problem = table.find_all('td')[1].text
            username = table.find('span', class_='uoj-username').text
            score = table.find('a', class_='uoj-score').text
        # print(f'{problem}\n{username}\n{score}', file = out_file)
        # 根据页面结构进一步提取你需要的数据
        # 比如查找提交结果所在的标签：
        # result_div = soup.find('div', class_='result')
        # if result_div:
        #     result = result_div.text.strip()
        #     print(f"结果: {result}")
            key = (username, problem)
        # 如果已存在记录，则比较，更新为较大者（假定分数为数字时可直接比较）
            if key in score_dict:
                try:
                    current_val = int(score_dict[key])
                    new_val = int(score)
                    if new_val > current_val:
                        score_dict[key] = score
                except (ValueError, TypeError):
                    # 如果无法转换为数字，保留原值
                    pass
            else:
                score_dict[key] = score
        except:
            print("Error on ",submission_id)
    else:
        print(f"[警告] URL: {url} 返回了状态码 {response.status_code}，可能已无数据或需要重新认证")
        
    
    # 暂停 1 秒，避免请求访问过快造成封禁
    time.sleep(0.001)

output_csv = "成绩.csv"
with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    # 写入表头
    writer.writerow(["用户名", "题目", "最高分"])
    # 按字典内容输出每个用户、题目的最高分成绩
    for (username, problem), max_score in score_dict.items():
        writer.writerow([username, problem, max_score])

print(f"所有成绩已保存到 {output_csv}")
out_file.close()