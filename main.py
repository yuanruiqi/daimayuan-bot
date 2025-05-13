import requests
from bs4 import BeautifulSoup
import time

# 请求头, 模拟浏览器请求
headers = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/90.0.4430.93 Safari/537.36')
}

# 将你的登录 cookie 信息复制到下面
cookies = {
    'sessionid': 'your_session_value_here',
    # 根据具体情况添加其他 cookie 信息，例如 'token': 'xxx'
}

# 设置起始的 submission ID
start_id = 3932924
# 可根据需要设置结束的 ID（如果未知，也可以设计成一个无限循环，遇到错误就 break）
end_id = 3933000

base_url = 'http://oj.daimayuan.top/submission/'

for submission_id in range(start_id, end_id):
    url = f"{base_url}{submission_id}"
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
    except Exception as e:
        print(f"[错误] 请求 {url} 时出现异常: {e}")
        break

    if response.status_code == 200:
        # 使用 BeautifulSoup 解析返回的 HTML 内容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 举例：提取页面的标题
        title_tag = soup.find('title')
        title = title_tag.string.strip() if title_tag else '无标题'
        print(f"Submission ID: {submission_id}  -- Title: {title}")

        # 根据页面结构进一步提取你需要的数据
        # 比如查找提交结果所在的标签：
        # result_div = soup.find('div', class_='result')
        # if result_div:
        #     result = result_div.text.strip()
        #     print(f"结果: {result}")
    else:
        print(f"[警告] URL: {url} 返回了状态码 {response.status_code}，可能已无数据或需要重新认证")
    
    # 暂停 1 秒，避免请求访问过快造成封禁
    time.sleep(1)
