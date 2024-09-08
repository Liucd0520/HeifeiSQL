import json

def generate_sql(structured_info):
    # 解析JSON对象
    time_frame = structured_info.get('时间')
    event_type = structured_info.get('具体事件', '')
    location = structured_info.get('发生区域', '')

    # 构建SQL查询
    sql = "SELECT COUNT(*) AS total_reports FROM table_orders "
    
    where_clause = []
    
    if event_type:
        where_clause.append(f"event_type = '{event_type}'")
    
    if location:
        where_clause.append(f"location = '{location}'")
    
    
    where_clause.append(f"report_time >= NOW() - INTERVAL {time_frame_to_days(time_frame)} DAY")

    if where_clause:
        sql += "WHERE " + " AND ".join(where_clause)

    sql += ";"

    return sql

def time_frame_to_days(time_frame):
    if time_frame == '近10天内':
        return 10
    # 可以添加更多的条件处理
    return 10

# 给定的结构化信息
structured_info = {
    '具体事件': '',
    '发生区域': '',
    '时间': '近10天内'
}

# 生成SQL查询
total_reports_sql = generate_sql(structured_info)

print("Total reports SQL:", total_reports_sql)
