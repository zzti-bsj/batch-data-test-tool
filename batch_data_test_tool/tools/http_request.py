import json
import requests

def sync_http_request(api_url=None, request_params=None, headers=None):
    """
    请求 http 的数据
    """
    try:
        response = requests.post(url=api_url, data=request_params, headers=headers)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response
        else:
            raise Exception(f"{str(response.text)}")
    except Exception as e:
        raise Exception(f"sync_http_request 错误：{e}")



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