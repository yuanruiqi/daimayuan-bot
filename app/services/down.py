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

def fetch_submission(session,submission_id):
    """获取单个提交的页面内容"""
    url = f"{CONFIG['down']['base_url']}{submission_id}"
    try:
        response = session.get(url, timeout=CONFIG['down']['timeout'])
        return response
    except requests.RequestException as e:
        logger.error(f"获取提交{submission_id}失败: {e}")
        return None

def get_contest_problems(session, contest_id):
    """获取比赛中的所有问题ID和题目名称"""
    url = f"http://oj.daimayuan.top/contest/{contest_id}"
    response = session.get(url)

    print(response.text)
    if response.status_code != 200:
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    problem_map = dict()
    for tr in soup.select('table tbody tr'):
        tds = tr.find_all('td')
        if len(tds) < 2:
            continue
        a = tds[1].find('a')
        if not a or '/problem/' not in a['href']:
            continue
        try:
            problem_id = int(a['href'].split('/problem/')[1])
            problem_name = a.text.strip()
            problem_map[problem_id] = problem_name
        except Exception:
            continue
    return problem_map

def process_single_submission(session, submission_id, target_contest_id, cache):
    """处理单个提交，包含缓存逻辑"""
    cache_key = f"submission_{submission_id}"
    
    # 尝试从缓存获取
    try:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"从缓存读取{submission_id}的数据: {cached_data}")
            # 如果是旧的三元组格式，转换为四元组
            if len(cached_data[0]) == 3:
                submission_id, username, problem_id = cached_data[0]
                result = (submission_id, username, problem_id, -1)  # 添加默认分数0
                logger.info(f"转换缓存数据为四元组: {result}")
                return result, 'ok'
            return cached_data
    except Exception as e:
        logger.warning(f"从缓存读取{submission_id}失败: {e}")
    
    # 缓存未命中，获取新数据
    response = fetch_submission(session,submission_id)
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
        result = (submission_id, username, problem_id, score)
        logger.info(f"处理提交{submission_id}的结果: {result}")
        
        # 存入缓存
        try:
            cache.set(cache_key, (result, 'ok'), expire=CONFIG['down']['cache']['expire'])
        except Exception as e:
            logger.warning(f"写入缓存{submission_id}失败: {e}")
        
        return result, 'ok'
    except Exception as e:
        logger.warning(f"处理提交{submission_id}时出错: {e}")
        return None, 'error'

def run(start_id, end_id, target_contest_id, task_id, progress_callback=None, should_cancel=None, should_pause=None):
    """主运行函数：收集指定比赛范围内的提交数据"""
    if not all(isinstance(x, int) for x in [start_id, end_id, target_contest_id]):
        logger.error("参数类型错误：所有ID必须是整数")
        return 'error', []
    
    # 创建会话
    session = create_session()
    
    # 获取比赛的所有问题ID和名称
    problem_map = get_contest_problems(session, target_contest_id)
    if not problem_map:
        logger.error(f"无法获取比赛 {target_contest_id} 的问题列表")
        return 'error', []
    
    # 创建缓存
    cache = get_cache()
    
    # 准备提交ID列表
    id_list = [(i, start_id + i) for i in range(end_id - start_id + 1)]
    
    # 收集数据
    submissions_data = []
    not_found_count = CONFIG['down']['max_404_count']
    total = end_id - start_id + 1
    
    # 分批处理
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
                    logger.info(f"获取到提交{submission_id}的结果: data_tuple={data_tuple}, status={status}")
                    # 更新进度
                    if progress_callback:
                        progress_callback(idx, total, submission_id)
                except Exception as e:
                    logger.warning(f"处理提交{submission_id}时出错: {e}")
                    continue
                    
                if status == 'not_found':
                    batch_not_found += 1
                    logger.info(f"提交 {submission_id} 不存在")
                elif status == 'error' or status == 'no_match':
                    # 'error' 和 'no_match' 都不计入 404，也不收集
                    continue
                else:  # status == 'ok'
                    submissions_data.append(data_tuple)
                    logger.info(f"添加有效提交: {submission_id}, 数据: {data_tuple}")
            
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

    logger.info(f"{task_id} down 完成，收集到的数据: {submissions_data[:5]}...")  # 只显示前5条数据
    return 'completed', submissions_data, problem_map