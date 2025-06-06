import os
import down
import ren
import anal
import config

def run(start_id, end_id, cid, task_id, progress_callback=None,should_cancel=None):
    # 1. 获取提交数据
    submission_data = down.run(start_id, end_id, cid, task_id, progress_callback,should_cancel)
    
    # 2. 分析数据生成DataFrame
    df, name_order = anal.run(submission_data)
    
    # 3. 生成HTML排名表
    return ren.run(df, start_id, end_id, cid)