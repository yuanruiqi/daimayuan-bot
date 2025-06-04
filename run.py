import os
import down
import ren
import anal
import config

def run(a, b, c):
    if not os.path.exists(config.general.cache_file):
        with open(config.general.cache_file, 'w') as f:
            f.write('{}')
    
    # 1. 获取提交数据
    submission_data = down.run(a, b, c)
    
    # 2. 分析数据生成DataFrame
    df, name_order = anal.run(submission_data, a, b, c)
    
    # 3. 生成HTML排名表
    ren.run(df, a, b, c, name_order, config.general.outfile)