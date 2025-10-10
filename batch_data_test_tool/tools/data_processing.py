import pandas as pd
import numpy as np

def clean_dataframe_for_json(df):
    """
    清理DataFrame中的NaN值，使其能够正确序列化为JSON
    """
    # 将NaN值替换为None，这样JSON序列化时会被转换为null
    df = df.where(pd.notnull(df), None)
    
    # 处理numpy的NaN值
    df = df.replace([np.nan], [None])
    
    return df

def read_dataframe_from_file(filepath):
    """
    从文件中读取df
    """
    df = None
    # 判断文件类型
    if 'csv' in filepath:
        df = pd.read_csv(filepath)
    elif 'xlsx' in filepath:
        df = pd.read_excel(filepath)
    
    # 清理NaN值，避免JSON序列化问题
    if df is not None:
        df = clean_dataframe_for_json(df)
    
    return df


def get_input_col_from_df(df, input_field_name):
    """
    从df数据中读取给定的列作为输入
    """
    return df.loc[:, input_field_name]

def join_list_with_delimiter(list_data: list, delimiter: str) -> str:
    """
    name: 分割符拼接列表数据
    function: 将df数据中的列用delimiter连接起来
    """
    import json_repair

    # 如果是空数据
    if not list_data:
        raise Exception(
            Status(
                status="002",
                message="数据预处理-列表为空"
            )
        )
    
    # 如果是str类型
    if isinstance(list_data, str):
        try:
            list_data = json_repair.loads(list_data)
        except Exception as e:
            raise Exception(
                Status(
                    status="002",
                    message=f"数据预处理-{str(e)}"
                )
            )

    # 最终返回join的结果
    try:
        return delimiter.join(list_data)
    except Exception as e:
        raise Exception(
            Status(
                status="002",
                message=f"数据预处理-{str(e)}"
            )
        )

