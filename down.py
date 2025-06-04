import requests
from bs4 import BeautifulSoup
from diskcache import Cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import config

def create_session():
    """创建并配置具有重试机制和连接池的请求会话"""
    session = requests.Session()
    
    # 配置重试策略
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    # 配置连接池适配器
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=100,
        pool_maxsize=100
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 应用默认请求头和cookies
    session.headers.update(config.down.headers)
    session.cookies.update(config.down.cookies)
    
    return session

def parse_submission_page(html_content, submission_id):
    """解析提交页面并提取关键信息"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find(class_="table-responsive")
        
        # 提取问题、用户名和分数
        problem = table.find_all('td')[1].text
        username = table.find('span', class_='uoj-username').text
        score = table.find('a', class_='uoj-score').text
        
        # 构建输出字符串
        out_str = f'{problem}\n{username}\n{score}'
        
        # 提取比赛ID
        table_html = str(table)
        contest_id_val = -1
        if '/contest/' in table_html:
            start_idx = table_html.find('/contest/') + 9
            contest_str = ""
            for char in table_html[start_idx:]:
                if char.isdigit():
                    contest_str += char
                else:
                    break
            if contest_str:
                contest_id_val = int(contest_str)
                
        return out_str, contest_id_val
        
    except Exception as e:
        # 处理编译错误情况
        if 'Compile Error' in str(table):
            return 'CE', -1
        print(f"解析提交{submission_id}时出错: {e}")
        return None, None

def fetch_submission(session, submission_id):
    """获取单个提交页面内容"""
    url = f"{config.down.base_url}{submission_id}"
    try:
        response = session.get(
            url, 
            timeout=config.down.timeout, 
            allow_redirects=True
        )
        return response
    except Exception as e:
        print(f"请求提交{submission_id}时出错: {e}")
        return None

def process_submission_range(start_id, end_id, target_contest_id, cache, session, progress_callback):
    """处理指定范围内的提交ID"""
    submissions_data = []
    not_found_count = config.down.max_404_count
    total = end_id - start_id + 1
    
    for idx, submission_id in enumerate(range(start_id, end_id + 1), 1):
        # 更新进度
        current_progress = int(idx * 100 / total)
        if progress_callback and (idx % 10 == 0 or current_progress != (idx-1) * 100 // total):
            progress_callback(idx, total, submission_id)
        
        # 检查缓存
        cache_key = str(submission_id)
        cached_data = cache.get(cache_key)
        if cached_data:
            out_str, contest_id = cached_data
            if contest_id == target_contest_id:
                submissions_data.append(tuple(out_str.split('\n')))
            continue
        
        # 获取提交页面
        response = fetch_submission(session, submission_id)
        if response is None:
            continue
            
        # 处理响应状态
        if response.status_code == 404:
            not_found_count -= 1
            print(f"提交{submission_id}: 404 (剩余{not_found_count}次)")
            if not_found_count <= 0:
                break
            continue
                
        if response.status_code != 200:
            print(f"提交{submission_id}: 非预期状态码 {response.status_code}")
            continue
            
        # 解析页面内容
        out_str, contest_id = parse_submission_page(response.text, submission_id)
        if out_str is None:
            continue
            
        # 更新缓存
        cache.set(cache_key, (out_str, contest_id))
        
        # 收集目标比赛数据
        if contest_id == target_contest_id:
            submissions_data.append(tuple(out_str.split('\n')))
            print(f"有效提交: {submission_id}")
    
    return submissions_data

def run(start_id, end_id, contest_id, progress_callback=None):
    """主运行函数：收集指定比赛范围内的提交数据"""
    # 验证参数有效性
    if start_id < config.down.min_id or start_id > end_id:
        return []
    
    # 初始化会话和缓存
    session = create_session()
    cache = Cache(config.general.cache_dir)
    
    # 处理提交范围
    try:
        return process_submission_range(
            start_id=start_id,
            end_id=end_id,
            target_contest_id=contest_id,
            cache=cache,
            session=session,
            progress_callback=progress_callback
        )
    finally:
        # 确保最后发送完成进度
        if progress_callback:
            total = end_id - start_id + 1
            progress_callback(total, total, end_id)
        cache.close()