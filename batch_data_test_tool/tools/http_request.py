import logging
import json
import requests
import re
import time

def clean_control_characters(text):
    """
    清理字符串中的控制字符，将特殊字符转换为安全格式
    """
    if not isinstance(text, str):
        return text
    
    # 先处理特殊字符的转换
    cleaned = text
    
    # 制表符转换为4个空格
    cleaned = cleaned.replace('\t', '    ')
    
    # 回车符转换为转义字符
    cleaned = cleaned.replace('\r', '\\r')
    
    # 换行符转换为转义字符
    cleaned = cleaned.replace('\n', '\\n')
    
    # 清理其他控制字符（保留已转换的字符）
    # 移除ASCII控制字符（除了已处理的制表符、回车符、换行符）
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', cleaned)
    
    # 额外清理：移除其他可能导致JSON问题的字符
    # 移除零宽字符和其他不可见字符
    cleaned = re.sub(r'[\u200B-\u200D\uFEFF]', '', cleaned)
    
    return cleaned

def safe_json_dumps(data, ensure_ascii=False):
    """
    安全的JSON序列化，处理控制字符
    """
    try:
        # 如果数据是字符串，先清理控制字符
        if isinstance(data, str):
            data = clean_control_characters(data)
        elif isinstance(data, dict):
            # 递归清理字典中的字符串值
            data = clean_dict_control_characters(data)
        
        # 使用更严格的JSON序列化设置
        json_str = json.dumps(data, ensure_ascii=ensure_ascii, separators=(',', ':'), allow_nan=False)
        
        # 验证生成的JSON是否有效
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            logging.error(f"生成的JSON无效: {e}")
            # 如果仍然无效，尝试更严格的清理
            if isinstance(data, dict):
                data = strict_clean_dict(data)
            json_str = json.dumps(data, ensure_ascii=True, separators=(',', ':'), allow_nan=False)
            return json_str
            
    except Exception as e:
        logging.error(f"JSON序列化失败: {e}")
        raise

def strict_clean_dict(data):
    """
    更严格的字典清理，移除所有可能有问题的字符
    """
    if isinstance(data, dict):
        return {str(key): strict_clean_dict(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [strict_clean_dict(item) for item in data]
    elif isinstance(data, str):
        # 只保留ASCII可打印字符
        cleaned = ''.join(char for char in data if 32 <= ord(char) <= 126)
        return cleaned
    else:
        return data

def clean_dict_control_characters(data):
    """
    递归清理字典中的控制字符
    """
    if isinstance(data, dict):
        return {key: clean_dict_control_characters(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_dict_control_characters(item) for item in data]
    elif isinstance(data, str):
        return clean_control_characters(data)
    else:
        return data

def sync_http_request(api_url=None, request_params=None, headers=None):
    """
    请求 http 的数据
    """
    # 记录请求开始时间
    start_time = time.time()
    
    try:
        # 设置默认headers
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        elif 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        
        # 处理请求参数
        if isinstance(request_params, str):
            # 清理字符串中的控制字符
            cleaned_params = clean_control_characters(request_params)
            logging.debug(f"字符串参数清理前: {repr(request_params[:200])}")
            logging.debug(f"字符串参数清理后: {repr(cleaned_params[:200])}")
            
            # 尝试解析为JSON，如果失败则直接使用清理后的字符串
            try:
                json_data = json.loads(cleaned_params)
                logging.debug(f"JSON解析成功: {type(json_data)}")
                # 使用json参数发送请求
                response = requests.post(url=api_url, json=json_data, headers=headers)
            except json.JSONDecodeError as e:
                logging.debug(f"JSON解析失败，作为普通字符串发送: {e}")
                # 如果不是有效的JSON，作为普通字符串发送
                response = requests.post(url=api_url, data=cleaned_params.encode('utf-8'), headers=headers)
        elif isinstance(request_params, dict):
            # 清理字典中的控制字符并序列化
            cleaned_params = clean_dict_control_characters(request_params)
            logging.debug(f"字典参数清理前: {str(request_params)[:200]}")
            logging.debug(f"字典参数清理后: {str(cleaned_params)[:200]}")
            
            # 先尝试手动序列化以检查是否有问题
            try:
                json_str = safe_json_dumps(cleaned_params)
                logging.debug(f"JSON序列化成功，长度: {len(json_str)}")
                
                # 最终验证：确保JSON字符串不包含控制字符
                final_json = clean_control_characters(json_str)
                if final_json != json_str:
                    logging.warning(f"JSON字符串中仍有控制字符，已清理")
                    json_str = final_json
                
                # 使用data参数发送已验证的JSON字符串
                response = requests.post(url=api_url, data=json_str.encode('utf-8'), headers=headers)
            except Exception as e:
                logging.error(f"JSON序列化失败: {e}")
                # 如果序列化失败，使用严格清理
                try:
                    strict_cleaned = strict_clean_dict(cleaned_params)
                    json_str = json.dumps(strict_cleaned, ensure_ascii=True, separators=(',', ':'))
                    response = requests.post(url=api_url, data=json_str.encode('utf-8'), headers=headers)
                except Exception as e2:
                    logging.error(f"严格清理后仍然失败: {e2}")
                    return None
        else:
            # 其他类型直接发送
            logging.debug(f"其他类型参数: {type(request_params)}")
            response = requests.post(url=api_url, data=request_params, headers=headers)
        
        # 记录请求结束时间并计算响应时间（秒）
        end_time = time.time()
        response_time = end_time - start_time
        
        # 将响应时间附加到response对象上（单位：秒，保留3位小数）
        response.response_time = round(response_time, 3)
        
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            return response
        else:
            # 添加更详细的错误信息
            error_detail = f"HTTP {response.status_code}"
            try:
                error_json = response.json()
                error_detail += f" | {error_json}"
            except:
                error_detail += f" | {response.text[:500]}"
            
            # 记录详细的请求参数信息
            logging.error(f"sync_http_request 错误: {error_detail}")
            logging.error(f"请求URL: {api_url}")
            logging.error(f"请求参数类型: {type(request_params)}")
            logging.error(f"请求参数内容: {request_params}")
            logging.error(f"请求头: {headers}")
            
            # 如果是字典类型，也记录清理后的参数
            if isinstance(request_params, dict):
                try:
                    cleaned_params = clean_dict_control_characters(request_params)
                    logging.error(f"清理后参数: {cleaned_params}")
                except Exception as e:
                    logging.error(f"清理参数时出错: {e}")
            
            return None
            
    except json.JSONDecodeError as e:
        # 记录请求结束时间（即使出错）
        end_time = time.time()
        response_time = round(end_time - start_time, 3)
        logging.error(f"JSON解析错误: {e}")
        logging.error(f"请求URL: {api_url}")
        logging.error(f"请求参数类型: {type(request_params)}")
        logging.error(f"请求参数内容: {request_params}")
        logging.error(f"请求头: {headers}")
        logging.error(f"响应时间: {response_time}秒")
        return None
    except Exception as e:
        # 记录请求结束时间（即使出错）
        end_time = time.time()
        response_time = round(end_time - start_time, 3)
        logging.error(f"sync_http_request 错误: {e}")
        logging.error(f"请求URL: {api_url}")
        logging.error(f"请求参数类型: {type(request_params)}")
        logging.error(f"请求参数内容: {request_params}")
        logging.error(f"请求头: {headers}")
        logging.error(f"异常类型: {type(e).__name__}")
        logging.error(f"响应时间: {response_time}秒")
        return None



def parse_http_stream_false_response(http_response):
    """
    解析 http stream false response
    这个方法的实现具有较强的复杂性
    将http解析成特定的格式
    """
    response_text = http_response.text
    # 用data: 来分割
    try:
        stream_data = response_text.split('data:')
        print(stream_data)
    except Exception as e:
        raise Exception(f"分割数据时错误：{e}: Response: {response_text}")
    # 构建answer
    answer = ''
    for row in stream_data:
        try:
            # 列表中可能有空值
            row_dict = json.loads(row)
            # 拼接 answer
            if ('finish' in row_dict and not row_dict['finish']):
                answer += str(row_dict['content'][0].get("content"))
            elif ('finish' in row_dict['data'] and not row_dict['data']['finish']):
                answer += str(row_dict['content'][0].get("content"))
        except Exception as e:
            print(f"parse_http_stream_false_response 错误：{e}: Row: {row}")

    # 返回answer
    return answer


def parse_http_stream_true_response(http_response):
    """
    解析 http stream true response
    这个方法的实现具有较强的复杂性
    将http解析成特定的格式
    """
    response_text = http_response.text
    # 用data: 来分割
    try:
        stream_data = response_text.split('data:')
    except Exception as e:
        raise Exception(f"分割数据时错误：{e}: Response: {response_text}")
    # 构建answer
    recall_list = []
    for row in stream_data:
        # 先加载成json对象
        try:
            # 列表中可能有空值
            row_dict = json.loads(row)
            # 拼接 answer
            if ('finish' in row_dict and row_dict['finish']):
                recall_list = row_dict["content"][1].get("content")
            elif ('finish' in row_dict['data'] and row_dict['data']['finish']):
                recall_list = row_dict['data']['content'][1].get("content")
        except Exception as e:
            print(f"parse_http_stream_true_response 错误：{e}: Row: {row}")
        
    # 返回召回 列表
    return recall_list