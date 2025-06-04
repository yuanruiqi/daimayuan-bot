import requests
from bs4 import BeautifulSoup
import json
# import time
import config

def run(start_id, end_id, contest_id):

    if (start_id < config.down.min_id):
        return
    
    # 设置起始的 submission ID
    # start_id = 3932620
    # 可根据需要设置结束的 ID（如果未知，也可以设计成一个无限循环，遇到错误就 break）
    # end_id = q

    with open(config.general.cache_file, 'r', encoding = 'utf-8') as f:
        cache_dict = json.load(f)

    # start_id, end_id = map(int, input().split())

    out_file = open(config.general.datafile, 'w')

    out_file.write(str(start_id)+'\n')
    out_file.write(str(end_id)+'\n')
    out_file.write(str(contest_id)+'\n')

    _404count = config.down.max_404_count # 防止卡爆
    
    for submission_id in range(start_id, end_id + 1):
        if (cache_dict.get(str(submission_id)) != None):
            out_str, val = cache_dict.get(str(submission_id))
            if (val != contest_id):
                continue
            print(out_str, file = out_file)
            continue
        url = f"{config.down.base_url}{submission_id}"
        # print(url)
        try:
            response = requests.get(url, headers=config.down.headers, cookies=config.down.cookies, timeout=10)
        except Exception as e:
            print(f"[错误] 请求 {url} 时出现异常: {e}")
            continue

        if response.status_code == 200:
            try:
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
                    out_str = f'{problem}\n{username}\n{score}'
                except:
                    cache_dict[str(submission_id)] = ('CE', -1)
                    continue
                # print(table)
                # cache_dict[str(submission_id)] = (out_str, )
                table_str = str(table)
                if (table_str.find('/contest/') == -1):
                    cache_dict[str(submission_id)] = (out_str, -1)
                    continue
                'xxxxx/contest/int/yyyyy'
                cur = table_str.find('/contest/') + 9
                val = 0
                while cur < len(table_str) and table_str[cur].isdigit():
                    val = val * 10 + int(table_str[cur])
                    cur += 1
                cache_dict[str(submission_id)] = (out_str, val)
                if (val != contest_id):
                    continue
                print(out_str, file = out_file)
                # 根据页面结构进一步提取你需要的数据
                # 比如查找提交结果所在的标签：
                # result_div = soup.find('div', class_='result')
                # if result_div:
                #     result = result_div.text.strip()
                #     print(f"结果: {result}")
                print(submission_id)
            except:
                pass
        elif response.status_code==404:
            _404count -= 1
            print(f"URL: {url} 返回了状态码 404，剩余检测 404 次数为 {_404count}")
        else:
            print(f"[警告] URL: {url} 返回了状态码 {response.status_code}，可能已无数据或需要重新认证")
        if _404count < 0:
            break
        # 暂停 1 秒，避免请求访问过快造成封禁
        # time.sleep(0.001)

    with open(config.general.cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_dict, f, ensure_ascii=False, indent=4)

    out_file.close()