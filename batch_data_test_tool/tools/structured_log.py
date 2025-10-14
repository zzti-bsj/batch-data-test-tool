import json
def structured_logging_metadata(
    input_file_name: str,
    all_columns: list,
    input_columns: list,
    input_shape: tuple,
    input_number: int
):
    """
    MetaData 数据输入文件名称、数据列、数据形状、数据数量等
    """
    return json.dumps({
        "metadata": {
            "输入文件": input_file_name,
            "文件所含列": all_columns,
            "输入数据列": input_columns,
            "输入数据形状": input_shape,
            "输入数据数量": input_number
        }
    }, ensure_ascii=False)

def structured_logging_row_detail(
    row_index: int,
    row: dict,
    max_workers: int,
    api_url: str,
    request_params: dict,
    headers: dict,
    response,
    exception_message: str
):
    """
    日志结构化输出
    """
    if response.status_code == 200:
        structured_response = {
            "response_status_code": "Succeed",
            "response_content": response.text
        }
    else:
        structured_response = {
            "response_status_code": "Failed",
            "response_content": str(response.text) + " / " + str(exception_message)
        }
    
    return json.dumps({
        "数据「" + str(row_index) + "」": row,
        "Request": {
            "api_url": api_url,
            "请求头": headers,
            "请求参数": request_params,
            "并发数": max_workers
        },
        "Response": structured_response
    }, ensure_ascii=False)
