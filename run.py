import os
import down
import ren
import anal
import config
import logging
logger = logging.getLogger(__name__)

def run(start_id, end_id, cid, task_id, progress_callback=None,should_cancel=None,should_pause=None,pause_event=None):
    logger.info(f"任务 {task_id} 开始获得数据")
    # 1. 获取提交数据
    submission_data = down.run(start_id, end_id, cid, task_id, progress_callback,should_cancel,should_pause,pause_event)
    
    logger.info(f"任务 {task_id} 开始分析数据")
    # 2. 分析数据生成DataFrame
    df, name_order = anal.run(submission_data)
    
    logger.info(f"任务 {task_id} 开始生成 html")
    # 3. 生成HTML排名表
    return ren.run(df, start_id, end_id, cid)