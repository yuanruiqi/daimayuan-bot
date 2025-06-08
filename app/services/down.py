import requests
from bs4 import BeautifulSoup
from diskcache import Cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from app.config import CONFIG

logger = logging.getLogger(__name__)

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
    session.headers.update(CONFIG['down']['headers'])
    session.cookies.update(CONFIG['down']['cookies'])
    
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
        logger.info(f"解析提交{submission_id}时出错: {e}")
        return None, None

def fetch_submission(session, submission_id):
    """获取单个提交页面内容"""
    url = f"{CONFIG['down']['base_url']}{submission_id}"
    try:
        response = session.get(
            url, 
            timeout=CONFIG['down']['timeout'], 
            allow_redirects=True
        )
        return response
    except Exception as e:
        logger.info(f"请求提交{submission_id}时出错: {e}")
        return None

def process_single_submission(submission_id, target_contest_id, cache, session):
    """
    处理单个提交 ID 的逻辑：
    - 缓存命中且比赛 ID 匹配时，直接返回 (data_tuple, 'ok')
    - 如果缓存命中但比赛 ID 不匹配，返回 (None, 'no_match')
    - 发请求失败 / 非 200 / 404 时，分别返回 (None, 'error') 或 (None, 'not_found')
    - 如果请求成功且解析后比赛 ID 匹配，返回 (data_tuple, 'ok')，否则 (None, 'no_match')
    """
    cache_key = str(submission_id)
    # 1. 检查缓存
    cached_data = cache.get(cache_key)
    if cached_data:
        out_str, contest_id = cached_data
        if contest_id == target_contest_id:
            return tuple(out_str.split('\n')), 'ok'
        else:
            return None, 'no_match'

    # 2. 缓存未命中，发起请求
    response = fetch_submission(session, submission_id)
    if response is None:
        # 网络层面出错，算作一般错误，跳过
        return None, 'error'

    if response.status_code == 404:
        # 404 情况，返回 not_found，让调用方做计数和判断
        return None, 'not_found'

    if response.status_code != 200:
        # 其他非 200 状态码，视为一般错误
        logger.info(f"提交 {submission_id}: 非预期状态码 {response.status_code}")
        return None, 'error'

    # 3. 200 OK，解析页面
    out_str, contest_id = parse_submission_page(response.text, submission_id)
    if out_str is None:
        # 解析失败，同样视作一般错误
        return None, 'error'

    # 4. 更新缓存
    cache.set(cache_key, (out_str, contest_id))

    # 5. 根据 contest_id 判断是否属于 target_contest_id
    if contest_id == target_contest_id:
        return tuple(out_str.split('\n')), 'ok'
    else:
        return None, 'no_match'


def process_submission_range(start_id, end_id, target_contest_id, cache, task_id, session, progress_callback ,should_cancel,should_pause):
    """
    将提交 ID 按照每 8 个一组并行处理，最后统一计算 404 次数。
    如果累计 404 次数达到 CONFIG['down']['max_404_count']，则提前退出。
    """
    submissions_data = []
    not_found_count = CONFIG['down']['max_404_count']
    total = end_id - start_id + 1

    # 先生成 (idx, submission_id) 列表，方便并行时记录进度
    id_list = [
        (idx, submission_id)
        for idx, submission_id in enumerate(range(start_id, end_id + 1), start=1)
    ]

    # 按照每 8 个一组分批
    batch_size = CONFIG['down']['batch_size']
    num_batches = math.ceil(len(id_list) / batch_size)

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        completed = False
        for batch_index in range(num_batches):
            batch_slice = id_list[batch_index * batch_size : (batch_index + 1) * batch_size]
            futures = {}

            # 1. 先提交这一批中的所有任务，并在提交前更新进度
            for idx, submission_id in batch_slice:
                # 更新进度回调
                current_progress = int(idx * 100 / total)
                if progress_callback and (idx % 10 == 0 or current_progress != (idx - 1) * 100 // total):
                    progress_callback(idx, total, submission_id)
                
                if not executor._shutdown:
                    # 提交任务
                    future = executor.submit(
                        process_single_submission,
                        submission_id,
                        target_contest_id,
                        cache,
                        session
                    )
                    futures[future] = (idx, submission_id)

            # 2. 等待这一批所有任务完成，统计 404 数量并收集 'ok' 结果
            batch_not_found = 0
            for future in as_completed(futures):
                idx, submission_id = futures[future]
                try:
                    data_tuple, status = future.result()
                except Exception as e:
                    # 如果单个任务抛异常，视为一般错误
                    logger.warning(f"{task_id} 中提交 {submission_id} 处理失败: {e}")
                    continue
                if status == 'not_found':
                    batch_not_found += 1
                    logger.info(f"提交 {submission_id}: 404 (本批次累计 404={batch_not_found})")
                elif status == 'error' or status == 'no_match':
                    # 'error' 和 'no_match' 都不计入 404，也不收集
                    continue
                else:  # status == 'ok'
                    submissions_data.append(data_tuple)
                    logger.info(f"有效提交: {submission_id}")

            # 3. 本批次结束后，统一扣减 not_found_count
            not_found_count -= batch_not_found
            if batch_not_found > 0:
                logger.info(f"{task_id} 中批次共 {batch_not_found} 次 404，剩余可容忍 404 次数 = {not_found_count}")
            if not_found_count <= 0:
                logger.info(f"{task_id} 中累计 404 次数达到上限，提前终止。")
                break
            if should_cancel and should_cancel(task_id):
                logger.info(f"{task_id} 中用户取消：")
                return 'cancelled',[]
            if should_pause and should_pause(task_id):
                logger.info(f"{task_id} 中用户暂停：")
                return 'paused',[]
            if executor._shutdown:
                logger.warning(f"{task_id} 被系统关闭")
                return 'paused',[]

    logger.info(f"{task_id} down 完成")

    return 'completed',submissions_data


def run(start_id, end_id, contest_id, task_id, progress_callback=None, should_cancel=None, should_pause=None):
    """主运行函数：收集指定比赛范围内的提交数据"""
    # 验证参数有效性
    if start_id < CONFIG['down']['min_id'] or start_id > end_id:
        logger.warning(f"{task_id}因为不满足条件所以返回空，start={start_id},end={end_id}")
        return 'completed',[]
    
    # 初始化会话和缓存
    session = create_session()
    cache = Cache(CONFIG['general']['cache_dir'])
    
    # 处理提交范围
    try:
        return process_submission_range(
            start_id=start_id,
            end_id=end_id,
            target_contest_id=contest_id,
            cache=cache,
            session=session,
            task_id=task_id,
            progress_callback=progress_callback,
            should_cancel=should_cancel,
            should_pause=should_pause
        )
    finally:
        # 确保最后发送完成进度
        if progress_callback:
            total = end_id - start_id + 1
            progress_callback(total, total, end_id)
        cache.close()