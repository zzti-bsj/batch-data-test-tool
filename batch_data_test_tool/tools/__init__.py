"""
工具模块

包含数据处理、HTTP请求和响应处理等核心功能。
"""

from .data_processing import read_dataframe_from_file, clean_dataframe_for_json, join_list_with_delimiter
from .http_request import sync_http_request, parse_http_stream_false_response, parse_http_stream_true_response
from .http_response import structure_request_params, parse_recall_result_special, parse_recall_result
from .parser import get_json_field_value, get_all_json_keys

# 数据预处理方法配置
DATA_PROCESSING_METHODS = {
    "join_list_with_delimiter": {
        "object": join_list_with_delimiter,
        "params": {
            "delimiter": ","
        }
    }
}

# Response解析方法配置
RESPONSE_PARSING_METHODS = {
    "get_field_value": {
        "method": get_json_field_value,
        "method_name": "获取指定字段值"
    },
    "get_all_keys": {
        "method": get_all_json_keys,
        "method_name": "获取所有字段路径"
    }
}

__all__ = [
    "read_dataframe_from_file",
    "clean_dataframe_for_json", 
    "join_list_with_delimiter",
    "sync_http_request",
    "parse_http_stream_false_response",
    "parse_http_stream_true_response",
    "structure_request_params",
    "parse_recall_result_special",
    "parse_recall_result",
    "get_json_field_value",
    "get_all_json_keys",
    "DATA_PROCESSING_METHODS",
    "RESPONSE_PARSING_METHODS"
]

