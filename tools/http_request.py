import json
import requests

def sync_http_request(url, request_json_data, headers):
    """
    请求 http 的数据
    """
    try:
        response = requests.post(url=url, data=request_json_data, headers=headers)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response
        else:
            raise Exception(f"sync_http_request 响应码非200")
    except Exception as e:
        raise Exception(f"sync_http_request 错误：{e}")

    return response


def parse_http_stream_false_response(http_response):
    """
    解析 http stream false response
    这个方法的实现具有较强的复杂性
    将http解析成特定的格式
    """
    response_text = http_response.text
    # 用data: 来分割
    stream_data = response_text.split('data:')
    # 构建answer
    answer = ''
    for row in stream_data:
        try:
            # 列表中可能有空值
            row_dict = json.loads(row)
        except Exception as e:
            continue
        # 拼接 answer
        if not row_dict['finish']:
            answer += str(row_dict['content'][0].get("content"))
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
    stream_data = response_text.split('data:')
    # 构建answer
    recall_list = []
    for row in stream_data:
        # 先加载成json对象
        try:
            # 列表中可能有空值
            row_dict = json.loads(row)
        except Exception as e:
            continue
        # 拼接 answer
        if row_dict['finish']:
            recall_list = row_dict["content"][1].get("content")

    # 返回召回 列表
    return recall_list