def parse_http_nostream_response(http_response):
    """
    解析 http nostream response
    解析非流式response
    """
    pass

def structure_request_params(col, api_type):
    """
    根据不同的api，构建不同的参数类型
    """
    if api_type == 'async_sales_qa':
        return {
             "text": col,
             "sessionId": "sdfsadfsadfsadfsa",
             "params": {
                "type": ["纯文本"]
             },
             "userKey": "app-10000",
             "user": "abc-123"
        }
    else:
        return None
    

# 解析recall_result
def parse_recall_result(recall_result):
    """
    解析召回结果dict
    """
    res = []
    for item in recall_result:
        item_string = ''
        try:
            for k,v in item.items():
                item_string += (f'【{k}】{v}' + '\n')
        except Exception as e:
            print(str(e))
            item_string = str(item)
        res.append(item_string)
    return "**************\n".join(res)


# 解析recall_result
def parse_recall_result_special(recall_result):
    """
    解析召回结果dict
    """
    res = []
    for item in recall_result:
        item_string = ''
        try:
            item_string = f"""
【id】{str(item['id']).strip()} 【score】{str(item['score']).strip()}
【content】{str(item['content']).strip()}
【answer】{str(item['answer']).strip()}
【category】{str(item['category']).strip()}
【tags】{item['tags']}"""
        except Exception as e:
            print(str(e))
            item_string = str(item)
        res.append(item_string)
    return "**************\n".join(res)
