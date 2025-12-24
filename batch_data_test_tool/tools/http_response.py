import json
import re

def parse_http_nostream_response(http_response):
    """
    解析 http nostream response
    解析非流式response
    """
    pass

def structure_request_params(row, placeholder_params_mapping_dic: dict, params: str):
    """
    构建请求参数，支持嵌套字典和列表结构
    解析params中的占位符，保持数据类型（支持list、dict等）
    """
    
    # 将params字符串解析为Python对象
    try:
        params_obj = json.loads(params)
    except json.JSONDecodeError:
        # 如果解析失败，回退到原来的字符串替换方式
        for placeholder, col_name in placeholder_params_mapping_dic.items():
            col_value = row[col_name]
            params = params.replace(f"${{{str(placeholder)}}}", str(col_value))
        return params
    
    def replace_placeholders_recursive(data):
        """递归替换占位符，保持数据类型"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = replace_placeholders_recursive(value)
            return result
        elif isinstance(data, list):
            return [replace_placeholders_recursive(item) for item in data]
        elif isinstance(data, str):
            # 检查是否是占位符
            placeholder_pattern = r'\${([^}]+)}'
            matches = re.findall(placeholder_pattern, data)
            
            if matches:
                # 如果字符串完全匹配占位符格式（如 "${message}"），则替换为实际值
                if re.match(r'^\${([^}]+)}$', data):
                    placeholder = matches[0]
                    if placeholder in placeholder_params_mapping_dic:
                        col_name = placeholder_params_mapping_dic[placeholder]
                        col_value = row[col_name]
                        
                        # 如果col_value已经是list或dict类型，直接返回
                        if isinstance(col_value, (list, dict)):
                            return col_value
                        
                        # 如果col_value是字符串，尝试解析为JSON（可能是JSON字符串）
                        if isinstance(col_value, str):
                            try:
                                parsed_value = json.loads(col_value)
                                return parsed_value  # 返回解析后的对象（可能是list、dict等）
                            except (json.JSONDecodeError, TypeError):
                                # 如果不是JSON字符串，直接返回原值
                                return col_value
                        else:
                            # 其他类型（int、float、bool等），直接返回
                            return col_value
                    else:
                        return data  # 占位符未找到映射，保持原样
                else:
                    # 字符串中包含占位符但不是完全匹配（如 "prefix_${message}_suffix"）
                    # 进行字符串替换
                    result = data
                    for placeholder in matches:
                        if placeholder in placeholder_params_mapping_dic:
                            col_name = placeholder_params_mapping_dic[placeholder]
                            col_value = row[col_name]
                            result = result.replace(f"${{{placeholder}}}", str(col_value))
                    return result
            else:
                return data  # 没有占位符，直接返回
        else:
            return data  # 其他类型（int、float、bool等），直接返回
    
    # 递归替换占位符
    params_obj = replace_placeholders_recursive(params_obj)
    
    # 重新序列化为JSON字符串
    return json.dumps(params_obj, ensure_ascii=False)

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
