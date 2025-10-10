"""
在这里放置一个数据预处理方法的选择列表
"""

from tools.data_processing import join_list_with_delimiter

DATA_PROCESSING_METHODS = {
    "join_list_with_delimiter": {
        "object": join_list_with_delimiter,
        "params": {
            "delimiter": ","
        }
    }
}