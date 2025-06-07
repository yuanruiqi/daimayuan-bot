import secrets

class general:
    cache_file='cache.json'
    outtemplate='templates/standing.html'
    waitingfile='waiting.html'
    cache_dir='./cache'

    secretkey = secrets.token_hex(16) # 生成随机密钥

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
        "UOJSESSID": ""
    }

    min_id = 3932620

    base_url = 'http://oj.daimayuan.top/submission/'

    max_404_count =15

    timeout = 10

    batch_size = 8

class anal:
    pass

class task:
    savetime=600#秒

class log:
    file='./logs/log'
    level = 'INFO'   
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'  
    max_bytes = 10 * 1024 * 1024  # 10MB 日志文件大小限制
    backup_count = 5  

class models:
    save_minute=5#分钟