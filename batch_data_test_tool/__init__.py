"""
批量数据测试工具 (Batch Data Test Tool)

一个用于批量处理数据并发送HTTP请求的Python工具包。
支持CSV和Excel文件读取，提供交互式Jupyter界面。
"""

__version__ = "1.0.0"
__author__ = "zzti-bsj"
__email__ = "otnw_bsj@163.com"

from .apps.simple_start import simple_start
from .tools.data_processing import read_dataframe_from_file, clean_dataframe_for_json
from .tools.http_request import sync_http_request
from .tools.http_response import structure_request_params, parse_recall_result_special

__all__ = [
    "simple_start",
    "read_dataframe_from_file", 
    "clean_dataframe_for_json",
    "sync_http_request",
    "structure_request_params",
    "parse_recall_result_special"
]
