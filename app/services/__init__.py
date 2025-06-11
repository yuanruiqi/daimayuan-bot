import logging

from .down import run as down
from .ren import run as ren
from .anal import run as anal
import requests

logger = logging.getLogger(__name__)

def run(start_id, end_id, cid, task_id, progress_callback=None,should_cancel=None,should_pause=None):
    logger.info(f"任务 {task_id} 开始获得数据")
    # 1. 获取提交数据
    status,submission_data,problem_map = down(start_id, end_id, cid, task_id, progress_callback,should_cancel,should_pause)
    if status != 'completed':
        return status,''
    
    logger.info(f"任务 {task_id} 开始分析数据")
    # 2. 分析数据生成DataFrame
    df, name_order, submission_history = anal(submission_data)
    
    logger.info(f"任务 {task_id} 开始生成 html")
    # 3. 渲染HTML
    table_html = ren(df, start_id,end_id,cid,name_order, submission_history, problem_map)
    
    return 'completed', table_html