from collections import defaultdict
import pandas as pd

def run(submission_data):
    if not submission_data:
        return pd.DataFrame(), []
    
    # 创建数据结构
    id_map = {}
    name_list = []
    problem_scores = defaultdict(lambda: defaultdict(int))
    
    # 处理每条提交记录
    for problem, username, score in submission_data:
        try:
            score_val = int(score)
        except ValueError:
            continue
        
        # 映射用户名到ID
        if username not in id_map:
            new_id = len(id_map) + 1
            id_map[username] = new_id
            name_list.append(username)
        
        user_id = id_map[username]
        
        # 更新最高分
        if score_val > problem_scores[problem][user_id]:
            problem_scores[problem][user_id] = score_val
    
    # 创建DataFrame
    df_data = []
    for problem, user_scores in problem_scores.items():
        row = [problem]
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
    
    return df_transposed, name_list