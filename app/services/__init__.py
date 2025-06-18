import logging

from .down import run as downrun
from .ren import run as renrun
from .anal import run as analrun
import requests

logger = logging.getLogger(__name__)

def run(start_id, end_id, cid, task_id, progress_callback=None,should_cancel=None,should_pause=None):
    logger.info(f"任务 {task_id} 开始获得数据")
    # 1. 获取提交数据
    status,submission_data,problem_map = downrun(start_id, end_id, cid, task_id, progress_callback,should_cancel,should_pause)
    if status != 'completed':
        return status,''
    
    logger.info(f"任务 {task_id} 开始分析数据")
    # 2. 分析数据生成DataFrame
    df, name_order, submission_history = analrun(submission_data)
    
    logger.info(f"任务 {task_id} 开始生成 html context")
    # 3. 渲染HTML context
    context = renrun(df, start_id,end_id,cid,name_order, submission_history, problem_map)
    return 'completed', context