def parse_http_nostream_response(http_response):
    """
    解析 http nostream response
    解析非流式response
    """
    pass

def structure_request_params(row, placeholder_params_mapping_dic: dict, params: str):
    """
    非嵌套字典的构建
    解析params中的占位符
    """
    for placeholder, col_name in placeholder_params_mapping_dic.items():
        col_value = row[col_name]
        params = params.replace(f"${{{str(placeholder)}}}", str(col_value))
    return params

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
