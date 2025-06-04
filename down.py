import requests
from bs4 import BeautifulSoup
import json
import config

def run(start_id, end_id, contest_id):
    if start_id < config.down.min_id:
        return []
    
    with open(config.general.cache_file, 'r', encoding='utf-8') as f:
        cache_dict = json.load(f)

    submission_data = []
    _404count = config.down.max_404_count
    
    for submission_id in range(start_id, end_id + 1):
        # 检查缓存
        cache_entry = cache_dict.get(str(submission_id))
        if cache_entry:
            out_str, val = cache_entry
            if val == contest_id:
                problem, username, score = out_str.split('\n')
                submission_data.append((problem, username, score))
                continue
        
        # 抓取新数据
        url = f"{config.down.base_url}{submission_id}"
        try:
            response = requests.get(url, headers=config.down.headers, 
                                  cookies=config.down.cookies, timeout=10)
        except Exception as e:
            print(f"[错误] 请求 {url} 时出现异常: {e}")
            continue

        if response.status_code == 200:
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find(class_="table-responsive")
                problem = table.find_all('td')[1].text
                username = table.find('span', class_='uoj-username').text
                score = table.find('a', class_='uoj-score').text
                out_str = f'{problem}\n{username}\n{score}'
                
                # 提取比赛ID
                table_str = str(table)
                if '/contest/' in table_str:
                    cur = table_str.find('/contest/') + 9
                    val = 0
                    while cur < len(table_str) and table_str[cur].isdigit():
                        val = val * 10 + int(table_str[cur])
                        cur += 1
                else:
                    val = -1
                
                # 更新缓存
                cache_dict[str(submission_id)] = (out_str, val)
                
                # 仅添加目标比赛的数据
                if val == contest_id:
                    submission_data.append((problem, username, score))
                    print(submission_id)
            except Exception as e:
                print(f"解析错误: {e}")
                if 'Compile Error' in table.find_all('a')[2]:
                    cache_dict[str(submission_id)] = ('CE', -1)
        elif response.status_code == 404:
            _404count -= 1
            print(f"URL: {url} 返回了状态码 404，剩余检测 404 次数为 {_404count}")
            if _404count <= 0:
                break
        else:
            print(f"[警告] URL: {url} 返回了状态码 {response.status_code}")

    # 保存更新后的缓存
    with open(config.general.cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_dict, f, ensure_ascii=False, indent=4)

    return submission_data