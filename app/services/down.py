import requests
from bs4 import BeautifulSoup
from diskcache import Cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time
import os

from app.config import CONFIG

logger = logging.getLogger(__name__)

def create_session():
    """创建并配置具有重试机制和连接池的请求会话"""
    session = requests.Session()
    
    # 配置重试策略
    retry_config = CONFIG['down']['retry']
    retry_strategy = Retry(
        total=retry_config['max_retries'],
        backoff_factor=retry_config['backoff_factor'],
        status_forcelist=retry_config['status_forcelist']
    )
    
    # 配置连接池
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 设置请求头
    session.headers.update(CONFIG['down']['headers'])
    
    # 设置cookies
    if CONFIG['down']['cookies']:
        session.cookies.update(CONFIG['down']['cookies'])
    
    return session

def get_cache():
    """创建并配置缓存"""
    # 确保缓存目录存在
    cache_dir = CONFIG['general']['cache_dir']
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_config = CONFIG['down']['cache']
    return Cache(
        cache_dir,
        timeout=cache_config['timeout'],
        retry=cache_config['retry']
    )

def fetch_submission(session, submission_id):
    """获取单个提交的页面内容"""
    url = f"{CONFIG['down']['base_url']}{submission_id}"
    try:
        response = session.get(url, timeout=CONFIG['down']['timeout'])
        return response
    except requests.RequestException as e:
        logger.error(f"获取提交{submission_id}失败: {e}")
        return None

def get_contest_problems(session, contest_id):
    """获取比赛中的所有问题ID"""
    url = f"http://oj.daimayuan.top/contest/{contest_id}"
    response = session.get(url)
    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    problem_links = soup.select('a[href*="/problem/"]')
    problem_ids = set()
    
    for link in problem_links:
        try:
            problem_id = int(link['href'].split('/problem/')[1])
            problem_ids.add(problem_id)
        except (ValueError, IndexError):
            continue
    
    return problem_ids

def process_single_submission(session, submission_id, target_contest_id, cache):
    """处理单个提交，包含缓存逻辑"""
    cache_key = f"submission_{submission_id}"
    
    # 尝试从缓存获取
    try:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
    except Exception as e:
        logger.warning(f"从缓存读取{submission_id}失败: {e}")
    
    # 缓存未命中，获取新数据
    response = fetch_submission(session, submission_id)
    if response is None:
        return None, 'error'
    
    if response.status_code == 404:
        return None, 'not_found'
    
    if response.status_code != 200:
        return None, 'error'
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 检查是否是目标比赛的提交
        problem_link = soup.select_one('td a[href*="/problem/"]')
        if not problem_link:
            return None, 'no_match'
        
        # 从链接中提取问题ID
        href = problem_link['href']
        problem_id = int(href.split('/problem/')[1])
        
        # 获取比赛的所有问题ID
        contest_problems = get_contest_problems(session, target_contest_id)
        if not contest_problems:
            logger.error(f"无法获取比赛 {target_contest_id} 的问题列表")
            return None, 'error'
        
        # 检查问题是否属于目标比赛
        if problem_id not in contest_problems:
            return None, 'no_match'
        
        # 提取用户名和分数
        username_elem = soup.select_one('td span.uoj-username')
        if not username_elem:
            return None, 'error'
        
        username = username_elem.text.strip()
        score_elem = soup.select_one('td a.uoj-score')
        if not score_elem:
            return None, 'error'
        
        score = score_elem.text.strip()
        
        # 构建结果
        result = (submission_id, username, score)
        
        # 存入缓存
        try:
            cache.set(cache_key, (result, 'ok'), expire=CONFIG['down']['cache']['expire'])
        except Exception as e:
            logger.warning(f"写入缓存{submission_id}失败: {e}")
        
        return result, 'ok'
    except Exception as e:
        logger.warning(f"处理提交{submission_id}时出错: {e}")
        return None, 'error'

def process_submission_range(start_id, end_id, target_contest_id, cache, task_id, session, progress_callback, should_cancel, should_pause):
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
        for batch_idx in range(num_batches):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, len(id_list))
            batch = id_list[batch_start:batch_end]
            
            # 提交本批次的所有任务
            futures = {
                executor.submit(
                    process_single_submission,
                    session,
                    submission_id,
                    target_contest_id,
                    cache
                ): (idx, submission_id)
                for idx, submission_id in batch
            }
            
            # 处理本批次的结果
            batch_not_found = 0
            for future in as_completed(futures):
                idx, submission_id = futures[future]
                try:
                    data_tuple, status = future.result()
                    # 更新进度
                    if progress_callback:
                        progress_callback(idx, total, submission_id)
                except Exception as e:
                    logger.warning(f"处理提交{submission_id}时出错: {e}")
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
                return 'cancelled', []
            if should_pause and should_pause(task_id):
                logger.info(f"{task_id} 中用户暂停：")
                return 'paused', []
            if executor._shutdown:
                logger.warning(f"{task_id} 被系统关闭")
                return 'paused', []

    logger.info(f"{task_id} down 完成")
    return 'completed', submissions_data

def run(start_id, end_id, contest_id, task_id, progress_callback=None, should_cancel=None, should_pause=None):
    """主运行函数：收集指定比赛范围内的提交数据"""
    if not all(isinstance(x, int) for x in [start_id, end_id, contest_id]):
        logger.error("参数类型错误：所有ID必须是整数")
        return 'error', []
    
    if start_id > end_id:
        logger.error("起始ID大于结束ID")
        return 'error', []
    
    # 初始化会话和缓存
    session = create_session()
    cache = get_cache()
    
    # 处理提交范围
    status, submissions_data = process_submission_range(
        start_id, end_id, contest_id, cache, task_id, session,
        progress_callback, should_cancel, should_pause
    )
    
    # 关闭缓存
    cache.close()
    
    return status, submissions_data