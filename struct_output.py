import requests 
from typing import List 
import json 



# 似乎请求的时间比在FASTAPI 页面上要长很多，0.9s V1.5s
url_extract = "http://192.168.0.11:8077/entity_extraction/"
url_clf = "http://192.168.0.11:8077/text_clf/"

def call_extract_api(model_name, content, prompt,  entity_1, entity_2=None, entity_3=None,  ):

    query_params = {
        'model'  : model_name,
        'entity_1': entity_1,
        'entity_2': entity_2,
        'entity_3':  entity_3,
        
    }

    body_params = {
        'content': content,
        'prompt': prompt
    }

    response = requests.post(url_extract, params=query_params, json=body_params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return json.dumps({'result': '执行错误'})


def call_clf_api(model_name, content: str, prompt: str, category: List) -> dict:

    query_params = {
        'model'  : model_name,
    }

    body_params = {
        'content': content,
        'prompt': prompt,
        'category': category
    }

    response = requests.post(url_clf, params=query_params, json=body_params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return json.dumps({'result': '执行错误'})
    


def generate_sql(structured_info):
    # 解析JSON对象
    time_frame = structured_info.get('时间')
    event = structured_info.get('具体事件', '')
    location = structured_info.get('发生区域', '')
    event_type = structured_info.get('事件性质', '')

    # 构建SQL查询
    sql = "SELECT COUNT(*) AS total_reports FROM table_orders "

    where_clause = []    
    if event:
        where_clause.append(f"event = '{event}'")

    if location:
        where_clause.append(f"location = '{location}'")
    
    if event_type:
         where_clause.append(f"event_type = '{event_type}'")

    if time_frame:
        prompt_extract = '请根据自然语句的条件写sql语句，不要有除了SQL语句之外的其他输出。示例如下：1. 近三个月：report_time >= NOW() - INTERVAL 3 MONTH     2. 最近1年 ：  report_time >= NOW() - INTERVAL 1 YEAR    3. 10天内 ：  report_time >= NOW() - INTERVAL 3 DAY 。接下来按照给出的自然语句写出新的SQL语句（只输出SQL语句）'
        entity_1 = 'sql语句'
        response = call_extract_api(model_name='Qwen2-72B',content=time_frame, prompt=prompt_extract, entity_1=entity_1)
        print(response)
        sql_date = json.loads(response['result'])[entity_1]
        where_clause.append(sql_date)
     

    if where_clause:
        sql += "WHERE " + " AND ".join(where_clause)
    sql += ";"

    # 如果是算相似度，而相似度都比较低，可以列表pop某个限制条件
    return sql


if __name__ == '__main__':
    
    content_list = [
        '近10天合肥市蜀山区上报了多少起道路积水的问题?',
        '蜀山区发生了多少起投诉类的事件?',
        '近10天内瑶海区发生了多少起城市管理类的投诉事件?',
        '群众经常上报道路积水的路段有哪些?',
        '群众经常上报宰客的菜市场有哪些?',
        '和小杨哥举办的演唱会相关联的投诉一共有多少起?具体都是关于什么的投诉?',
        '被多次投诉不作为和违规收费的物业有哪些?',
        '今年涉及到私拆承重墙相关的事件有多少起?分别涉及到哪些地方?(要导出结果)',
        '三个月内涉及到飞线充电和电动车上楼的事件有多少起?分别涉及到哪些地方?(要导出结果)',
        '近一个月内上报事件排名前10的事件类型是哪些?',
        '近10天内AI预整产生了多少工单量?其中多少是办结的?多少是未办结的?未办结中最多的是哪一类工单?',
        '近10天内群众通过小程序上报多少个事件?有多少事件和AI预警重复?(时间相近、地点相同、描述相似)',
        '近10天内长江路和天王巷交口上报了多少起违章停车的事件?',
        '近10天内合肥市哪些路段违章停车、闯红灯的问题较多?(10起以上)'
    ]
    

    prompt_extract = '现在有一个工单数据库，里面包含了大量市民来电所反映的问题。下面是一句用户的查询语句，请抽取这句话里的查询句子中所想查询的<具体事件>，<发生区域>、<时间>信息。如果没有则返回空。将抽取的信息以json格式返回，不要有额外的输出。'
    entity_1 = '具体事件'
    entity_2 = '发生区域'
    entity_3 = '时间'
    
    prompt_clf = '现在有一个工单数据库，里面包含了大量市民来电所反映的问题。下面是一句用户的查询。请判断所要查询事件的性质：如果查询语句明确说明是投诉类事件或者有相关字眼则为“投诉”，如果是查询语句明确说明是咨询类事件则是“咨询”，如果查询里没有明确提到事件的性质，则为“没有限制”'
    category = [ "没有限制",   "咨询",  "投诉" ]
    

    for content in content_list:
        response_extract = call_extract_api(model_name='Qwen2-72B',content=content,prompt=prompt_extract, entity_1=entity_1, entity_2=entity_2, entity_3=entity_3, )
        entity_dict = json.loads(response_extract['result'])
        
        response_clf = call_clf_api(model_name='Qwen2-72B', content=content, prompt=prompt_clf, category=category)
        event_type = response_clf['result']
        print('-----------------')
        print(content)
        print(entity_dict, event_type)

        entity_dict.update({'事件性质': '' if event_type == '没有限制' else event_type})
        sql = generate_sql(entity_dict)
        print(sql)