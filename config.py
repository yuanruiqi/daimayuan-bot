class general:
    cache_file='cache.json'
    outfile='templates/out.html'
    outtemplate='template.html'

class down:
    # 请求头, 模拟浏览器请求
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/90.0.4430.93 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive'
    }

    # 将你的登录 cookie 信息复制到下面
    cookies = {
        "UOJSESSID": "3htc4g05jcb0oa4pn5adtjhe3n"
    }

    min_id = 3932620

    base_url = 'http://oj.daimayuan.top/submission/'

    max_404_count =15

    timeout = 10

class anal:
    extlines = 3