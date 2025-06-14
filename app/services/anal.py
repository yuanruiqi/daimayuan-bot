from collections import defaultdict
import pandas as pd
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)

def run(submission_data):
    """
    入口函数：处理提交数据，生成DataFrame、用户名列表和提交历史。
    """
    if not submission_data:
        logger.warning("收到空提交数据")
        return pd.DataFrame(), [], {}
    
    logger.info(f"收到的提交数据示例: {submission_data[:5]}...")  # 只显示前5条数据
    
    # 创建数据结构
    id_map = {}
    name_list = []
    problem_scores = defaultdict(lambda: defaultdict(int))
    submission_history = defaultdict(lambda: defaultdict(list))  # 记录每个用户的提交历史
    
    # 处理每条提交记录
    for submission_id, username, problem_id, score in submission_data:  # 直接使用四元组
        try:
            score_val = int(score)
            logger.debug(f"处理提交: id={submission_id}, user={username}, problem={problem_id}, score={score_val}")
        except ValueError:
            logger.warning(f"无效的分数值: {score}")
            continue
        
        # 映射用户名到ID
        if username not in id_map:
            new_id = len(id_map) + 1
            id_map[username] = new_id
            name_list.append(username)
        
        user_id = id_map[username]
        
        # 更新最高分
        if score_val > problem_scores[problem_id][user_id]:
            problem_scores[problem_id][user_id] = score_val
        
        # 记录提交历史
        submission_history[username][problem_id].append((submission_id, score_val))
    
    # 创建DataFrame数据
    df_data = []
    for problem_id, user_scores in problem_scores.items():
        row = [problem_id]
        for user_id in range(1, len(id_map) + 1):
            row.append(user_scores.get(user_id, 0))
        df_data.append(row)
    
    # 添加总分行
    total_row = ['总分'] + [0] * len(id_map)
    for row in df_data:
        for i, score in enumerate(row[1:], 1):
            total_row[i] += score
    df_data.append(total_row)
    
    # 创建DataFrame
    df = pd.DataFrame(df_data, columns=['题目'] + name_list)
    
    # 转置DataFrame
    df_transposed = df.set_index('题目').T.reset_index()
    df_transposed.columns = ['用户名'] + list(df_transposed.columns[1:])

    logger.info(f"{len(submission_data)} 条数据分析完成")
    logger.info(f"用户数量: {len(name_list)}")
    logger.info(f"题目数量: {len(problem_scores)}")
    
    return df_transposed, name_list, submission_history