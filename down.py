import requests
from bs4 import BeautifulSoup
import json
# import time

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

min_id = 3932620

def run(start_id, end_id, contest_id):

    if (start_id < min_id):
        return
    
    # 设置起始的 submission ID
    # start_id = 3932620
    # 可根据需要设置结束的 ID（如果未知，也可以设计成一个无限循环，遇到错误就 break）
    # end_id = 3933050

    with open('cache.json', 'r', encoding = 'utf-8') as f:
        cache_dict = json.load(f)

    base_url = 'http://oj.daimayuan.top/submission/'

    # start_id, end_id = map(int, input().split())

    out_file = open('data', 'w')

    for submission_id in range(start_id, end_id + 1):
        if (cache_dict.get(str(submission_id)) != None):
            print(cache_dict.get(str(submission_id)), file = out_file)
            continue
        url = f"{base_url}{submission_id}"
        # print(url)
        try:
            response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
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
                table = soup.find(class_ = "table-responsive")
                if (str(table).find('/contest/' + str(contest_id) + '/') == -1):
                    continue
                problem = table.find_all('td')[1].text
                username = table.find('span', class_='uoj-username').text
                score = table.find('a', class_='uoj-score').text
                out_str = f'{problem}\n{username}\n{score}'
                print(out_str, file = out_file)
                cache_dict[str(submission_id)] = out_str
                # 根据页面结构进一步提取你需要的数据
                # 比如查找提交结果所在的标签：
                # result_div = soup.find('div', class_='result')
                # if result_div:
                #     result = result_div.text.strip()
                #     print(f"结果: {result}")
                print(submission_id)
            except:
                pass
        else:
            print(f"[警告] URL: {url} 返回了状态码 {response.status_code}，可能已无数据或需要重新认证")
        
        # 暂停 1 秒，避免请求访问过快造成封禁
        # time.sleep(0.001)

    with open('cache.json', 'w', encoding='utf-8') as f:
        json.dump(cache_dict, f, ensure_ascii=False, indent=4)

    out_file.close()