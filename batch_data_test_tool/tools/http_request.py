import logging
import json
import requests
import re

def clean_control_characters(text):
    """
    清理字符串中的控制字符，保留必要的空白字符
    """
    if not isinstance(text, str):
        return text
    
    # 保留必要的空白字符：空格、制表符、换行符、回车符
    # 移除其他控制字符（ASCII 0-31中除了9,10,13,32的字符）
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
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
        
        return json.dumps(data, ensure_ascii=ensure_ascii, separators=(',', ':'))
    except Exception as e:
        logging.error(f"JSON序列化失败: {e}")
        raise

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
            # 尝试解析为JSON，如果失败则直接使用清理后的字符串
            try:
                json_data = json.loads(cleaned_params)
                # 使用json参数发送请求
                response = requests.post(url=api_url, json=json_data, headers=headers)
            except json.JSONDecodeError:
                # 如果不是有效的JSON，作为普通字符串发送
                response = requests.post(url=api_url, data=cleaned_params.encode('utf-8'), headers=headers)
        elif isinstance(request_params, dict):
            # 清理字典中的控制字符并序列化
            cleaned_params = clean_dict_control_characters(request_params)
            # 使用json参数发送请求，让requests自动处理JSON序列化
            response = requests.post(url=api_url, json=cleaned_params, headers=headers)
        else:
            # 其他类型直接发送
            response = requests.post(url=api_url, data=request_params, headers=headers)
        
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
            
            logging.error(f"sync_http_request 错误: {error_detail}")
            logging.debug(f"请求参数: {request_params}")
            logging.debug(f"请求头: {headers}")
            return None
            
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析错误: {e}，数据: {request_params}")
        return None
    except Exception as e:
        logging.error(f"sync_http_request 错误: {e}，数据: {request_params}")
        logging.debug(f"异常类型: {type(e).__name__}")
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