import os, time
import logging
import json
import pandas as pd
import ipywidgets as widgets
from ..tools.data_processing import read_dataframe_from_file, clean_dataframe_for_json
from ..tools.http_request import sync_http_request, parse_http_stream_false_response, parse_http_stream_true_response
from ..tools.http_response import structure_request_params, parse_recall_result_special
from ..tools import DATA_PROCESSING_METHODS
from ..tools.get_config import get_api_url_name_list, get_api_params_placeholder_list_by_name, get_api_url_by_name, get_api_headers_by_name, get_api_params_by_name, get_api_timeout_by_name
from IPython.display import display
from ..concurrency.multi_threading import multi_exec
from ..tools.structured_log import structured_logging_metadata, structured_logging_row_detail

if not os.path.exists('logs'):
    os.makedirs('logs')
# 日志服务
# 控制台日志 - 只显示重要信息
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# 文件日志 - 记录详细信息
file_handler = logging.FileHandler(f'logs/batch_test_{time.time()}.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 配置根日志器
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)

# 创建专门用于详细日志的logger
detailed_logger = logging.getLogger('detailed')
detailed_logger.setLevel(logging.INFO)
detailed_logger.addHandler(file_handler)  # 只写入文件，不输出到控制台
detailed_logger.propagate = False  # 防止传播到根日志器

# 全局数据
df = None
result_data = None  # 存储批量处理的结果


# Step000. 选择接口配置
api_config_name_list = get_api_url_name_list()
step000_api_config_selector = widgets.Dropdown(
    options=api_config_name_list,
    value=None,
    description='选择接口配置',
    disabled=False,
)


# Step001. 选择数据
data_base_dir = 'data'
files = os.listdir(data_base_dir)
step001_dropdown = widgets.Dropdown(
    options=files,
    value=None,
    description='选择数据文件',
    disabled=False,
)

# Step002. 读取数据
step002_output = widgets.Output()

def on_read_button_clicked(b):
    """按钮点击事件处理函数"""
    global df
    with step002_output:
        step002_output.clear_output()  # 清空之前的输出
        try:
            # 获取选择的文件路径
            filepath = os.path.join(data_base_dir, step001_dropdown.value)
            print(f"正在读取文件: {filepath}")
            
            # 读取数据
            df = read_dataframe_from_file(filepath)
            
            print(f"✅ 数据读取成功！")
            print(f"📊 数据形状: {df.shape}")
            print(f"📋 列名: {df.columns.tolist()}")
            
            # 自动更新列选择器
            update_columns()
            
        except Exception as e:
            print(f"❌ 读取数据时出错: {e}")

step002_button = widgets.Button(
    description='读取数据',
    disabled=False,
    button_style='',
    tooltip='点击读取选中的数据文件'
)

# Step003. 数据预览
step003_output = widgets.Output()

def on_display_button_clicked(b):
    """展示数据按钮点击事件"""
    global df
    with step003_output:
        step003_output.clear_output()
        if df is not None:
            print("前5行数据:")
            display(df.head())
        else:
            print("❌ 请先点击'Step002.读取数据'按钮加载数据")

step003_button = widgets.Button(
    description=f'前5行数据预览',
    disabled=False,
    button_style='',
    tooltip='展示数据的详细信息'
)

# Step004. 列选择器
api_params_placeholder_list = get_api_params_placeholder_list_by_name(api_name=step000_api_config_selector.value)
columns_selector = [widgets.Dropdown(
    options=[],
    value=None,
    description=f'{col}',
    disabled=True,
)
for col in api_params_placeholder_list]

# 创建列选择器容器
columns_container = widgets.VBox([])

# API配置选择器变化事件处理
def on_api_config_changed(change):
    """当API配置选择器改变时的处理函数"""
    global api_params_placeholder_list, columns_selector
    
    # 重新获取参数占位符列表
    api_params_placeholder_list = get_api_params_placeholder_list_by_name(api_name=change['new'])
    print(f"API配置已切换到: {change['new']}")
    print(f"新的参数占位符: {api_params_placeholder_list}")
    
    # 重新创建列选择器
    columns_selector = [widgets.Dropdown(
        options=[],
        value=None,
        description=f'{col}',
        disabled=True,
    ) for col in api_params_placeholder_list]
    
    # 更新容器中的列选择器
    columns_container.children = columns_selector
    
    # 如果已有数据，自动更新列选择器
    if df is not None:
        update_columns()

# 绑定API配置选择器变化事件
step000_api_config_selector.observe(on_api_config_changed, names='value')

# 初始化列选择器容器
columns_container.children = columns_selector

# 当数据改变时自动更新列选择器
def update_columns():
    global df, columns_selector
    if df is not None:
        for index, column in enumerate(columns_selector):
            column.options = df.columns.tolist()
            column.value = df.columns.tolist()[0]
            column.disabled = False
            columns_selector[index] = column
    else:
        for index, column in enumerate(columns_selector):
            column.options = []
            column.value = None
            column.disabled = True
            columns_selector[index] = column


# Step004.1 展示选中列数据
step004_1_output = widgets.Output()

def on_show_column_clicked(b):
    with step004_1_output:
        step004_1_output.clear_output()
        selected_data_dic = {}
        if df is not None and 'columns_selector' in globals():
            for column in columns_selector:
                if column.value is not None:
                    selected_data_dic[column.description] = column.value
            print(f"选中列: {selected_data_dic}")
            print(f"选中列数据: ")
            display(df[list(selected_data_dic.values())].head())
        else:
            print("❌ 请先加载数据并选择列")

step004_1_button = widgets.Button(
    description='展示选中列数据',
    disabled=False,
    button_style='',
    tooltip='展示选中列的详细数据'
)

# 并发数选择器
max_workers_selector = widgets.IntSlider(
    value=4,
    min=1,
    max=10,
    step=1,
    description='并发数:',
    disabled=False,
    style={'description_width': 'initial'}
)

# 进度条
progress_bar = widgets.IntProgress(
    value=0,
    min=0,
    max=100,
    description='处理进度:',
    bar_style='info',
    orientation='horizontal',
    style={'bar_color': '#28a745'},
    layout=widgets.Layout(width='100%')
)

# 自动保存勾选框
auto_save_checkbox = widgets.Checkbox(
    value=False,
    description='自动保存',
    disabled=False,
    style={'description_width': 'initial'}
)

# Step005. 执行批量测试
step005_output = widgets.Output()


def process_batch_http_request(
    df: pd.DataFrame,
    placeholder_params_mapping_list,
    stream_parser: bool,
    data_processing_methods: list,
    api_url: str,
    headers: dict,
    params: str,
    timeout: float = 30
):
    try:
        columns = df.columns.tolist()
        # 保留用户选择的列
        new_df = pd.DataFrame()
        new_df[list(columns)] = df[list(columns)]

        # 3. 构建请求参数
        func_params_dic = {}
        for index, row in new_df.iterrows():
            try:
                # 3.1 构建参数
                # col.description 是占位符的名字
                # col.value 是数据中列名
                placeholder_params_mapping_dic = {
                    col.description: col.value
                    for col in placeholder_params_mapping_list
                }
                request_params = structure_request_params(
                    row,
                    placeholder_params_mapping_dic,
                    json.dumps(params)
                )
                # 3.1.1 字段预处理（pipeline）
                # for data_processing_method in data_processing_methods:
                #     # 使用前端传递的参数，如果没有则使用默认参数
                #     method_params = data_processing_params.get(data_processing_method, DATA_PROCESSING_METHODS[data_processing_method]["params"])
                #     input_data = DATA_PROCESSING_METHODS[data_processing_method]["object"](input_data, **method_params)
                
                
                # 3.2 请求response
                # 只构建参数列表
                func_params = {
                    'api_url': api_url,
                    'headers': headers,
                    'request_params': request_params,
                    'timeout': timeout
                }

                # response = sync_http_request(api_url, request_params, headers)
                func_params_dic[index] = func_params

            except Exception as e:
                logging.error(f"构建第{index}行请求参数时出错: {e} \n\n api_url:参数{func_params}；headers:参数{headers}；request_params:参数{request_params}")
                print(f"处理第{index}行时出错: {e}")
                raise Exception(f"处理第{index}行时出错: {e}")


        # 根据构建好的参数来处理结果
        results = multi_exec(sync_http_request, func_params_dic, max_workers=max_workers_selector.value)
        
        # 初始化进度条
        total_rows = len(new_df)
        progress_bar.max = total_rows
        progress_bar.value = 0
        
        for index, response in results.items():
            # emmm ... 以下解析的逻辑要重写的
            # 需要实现一系列解析Response的方法组成的Pipeline
            exception_message = ''
            # if stream_parser:
            #     try:
            #         answer = parse_http_stream_false_response(response)
            #     except Exception as e:
            #         answer = None
            #         exception_message = f"数据「{index}」解析answer时错误: {str(e)}"
            #         logging.error(f"数据「{index}」解析answer时错误: {str(e)}")
            #     try:
            #         recall_list = parse_http_stream_true_response(response)
            #     except Exception as e:
            #         recall_list = []
            #         exception_message = f"数据「{index}」解析recall_list时错误: {str(e)}"
            #         logging.error(f"数据「{index}」解析recall_list时错误: {str(e)}")
                
            #     # 将列表转换为字符串存储
            #     new_df.loc[index, 'answer'] = str(answer) if answer is not None else None
            #     new_df.loc[index, 'recall_list'] = str(recall_list) if recall_list is not None else None
            # else:
            #     new_df.loc[index, 'answer'] = None
            #     new_df.loc[index, 'recall_list'] = None

            try:
                new_df.loc[index, 'response_text'] = response.text
                # 记录响应时间
                if response is not None and hasattr(response, 'response_time'):
                    new_df.loc[index, 'response_time'] = response.response_time
                else:
                    new_df.loc[index, 'response_time'] = None
            except Exception as e:
                new_df.loc[index, 'response_text'] = None
                new_df.loc[index, 'response_time'] = None
                exception_message = f"数据「{index}」获取response_text时错误: {str(e)}"
                logging.error(f"数据「{index}」获取response_text时错误: {str(e)}")

            # 每行处理完response之后落日志（只写入文件，不显示在控制台）
            if exception_message != '':
                detailed_logger.error(structured_logging_row_detail(
                    row_index=index,
                    row=new_df.loc[index].to_dict(),
                    max_workers=max_workers_selector.value,
                    api_url=api_url,
                    request_params=request_params,
                    headers=headers,
                    response=response,
                    exception_message=exception_message
                ))
            else:
                detailed_logger.info(structured_logging_row_detail(
                    row_index=index,
                    row=new_df.loc[index].to_dict(),
                    max_workers=max_workers_selector.value,
                    api_url=api_url,
                    request_params=request_params,
                    headers=headers,
                    response=response,
                    exception_message=None
                ))
            
            # 更新进度条
            progress_bar.value += 1
        
        # 清理NaN值，使其能够正确序列化为JSON
        new_df = clean_dataframe_for_json(new_df)
        
        # 将结果转换为字典格式返回
        global result_data
        result_data = new_df.to_dict('records')
        logging.info(f"✅ 批量处理完成！处理了 {len(result_data)} 条记录")
        
        # 更新列选择器
        update_available_columns()
        
        # 如果勾选了自动保存，则自动保存数据
        if auto_save_checkbox.value:
            try:
                # 创建output目录
                output_dir = 'output'
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                # 生成文件名
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"auto_save_{timestamp}.xlsx"
                filepath = os.path.join(output_dir, filename)
                
                # 保存所有数据
                new_df.to_excel(filepath, index=False)
                logging.info(f"✅ 自动保存完成！文件已保存到: {filepath}")
                print(f"✅ 自动保存完成！文件已保存到: {filepath}")
            except Exception as e:
                logging.error(f"自动保存失败: {e}")
                print(f"❌ 自动保存失败: {e}")
        
        return result_data
        
    except Exception as e:
        logging.error(f"批量处理出错: {e}")
        print(f"❌ 批量处理出错: {e}")
        return []

# 创建事件处理函数
def on_process_batch_http_request_clicked(b):
    """批量处理http请求按钮点击事件"""
    global df, result_data
    
    # 记录日志元数据
    logging.info(structured_logging_metadata(
        input_file_name=step001_dropdown.value,
        all_columns=df.columns.tolist(),
        input_columns=[column.description for column in columns_selector],
        input_shape=df.shape,
        input_number=len(df)
    ))
    with step005_output:
        step005_output.clear_output()
        if df is not None and columns_selector is not None and step000_api_config_selector.value is not None:
            result_data = process_batch_http_request(
                df,
                columns_selector,
                True,
                [],
                get_api_url_by_name(api_name=step000_api_config_selector.value),
                get_api_headers_by_name(api_name=step000_api_config_selector.value),
                get_api_params_by_name(api_name=step000_api_config_selector.value),
                get_api_timeout_by_name(api_name=step000_api_config_selector.value)
            )
            if result_data and len(result_data) > 0:
                rd = pd.DataFrame(result_data)
                display(rd.head())
            else:
                print("❌ 没有处理结果数据")

            # 更新结果列
            update_available_columns()
        else:
            print("❌ 请先加载数据并选择列")


step005_button = widgets.Button(
    description='批量处理http请求',
    disabled=False,
    button_style='',
    tooltip='批量处理http请求'
)


# Step006 选择要保存的列
available_column_selector = widgets.SelectMultiple(
    options=[],
    value=[],
    description='选择要保存的列',
    disabled=True,
    layout=widgets.Layout(width='300px', height='150px')
)

# 更新列选择器的函数（支持多选）
def update_available_columns():
    """更新可选择的列（多选）"""
    global result_data
    if result_data is not None:
        tmp_df = pd.DataFrame(result_data)
        available_column_selector.options = tmp_df.columns.tolist()
        # 默认选择前3列（如果存在的话）
        default_selection = tmp_df.columns.tolist()[:3]
        available_column_selector.value = default_selection
        available_column_selector.disabled = False
        print(f"✅ 已更新可选列，共 {len(tmp_df.columns)} 列")
        print(f"📋 可选列: {list(tmp_df.columns)}")
        print(f"🎯 默认选中: {default_selection}")
    else:
        available_column_selector.options = []
        available_column_selector.value = []
        available_column_selector.disabled = True
        print("❌ 没有可选择的列，请先完成批量处理")


# Step007 保存数据文件
step007_output = widgets.Output()

# 自定义文件名输入框
custom_filename_input = widgets.Text(
    value='',
    placeholder='输入自定义文件名（可选，不包含扩展名）',
    description='自定义文件名:',
    style={'description_width': 'initial'}
)

# 更新保存数据功能（支持多列）
def on_save_data_clicked(b):
    global available_column_selector, result_data
    with step007_output:
        step007_output.clear_output()
        selected_columns = available_column_selector.value
        display(selected_columns)
        if result_data is not None and selected_columns:
            try:
                save_df = pd.DataFrame(result_data)
                save_df = clean_dataframe_for_json(save_df)
                display(save_df.head())
                available_columns = save_df.columns.tolist()
                missing_columns = [col for col in selected_columns if col not in available_columns]
                if missing_columns:
                    return {"error": f"以下列不存在: {missing_columns}"}
                # 选择指定的列
                display(selected_columns)
                selected_df = save_df[list(selected_columns)]
                
                # 创建output目录
                output_dir = 'output'
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                # 生成文件名
                from datetime import datetime
                custom_name = custom_filename_input.value.strip()
                if custom_name:
                    # 使用用户自定义文件名
                    filename = f"{custom_name}.xlsx"
                else:
                    # 使用默认时间序列文件名
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"batch_test_result_{timestamp}.xlsx"
                filepath = os.path.join(output_dir, filename)
                
                # 保存文件
                selected_df.to_excel(filepath, index=False)
                logging.info(f"✅ 文件已保存到: {filepath}")
                
            except Exception as e:
                print(f"❌ 保存数据时出错: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ 请先完成批量处理并选择要保存的列")

# 创建保存数据的按钮
step007_button = widgets.Button(
    description='保存选中列到文件',
    disabled=False,
    button_style='',
    tooltip='将选中的多列数据保存到CSV文件'
)



def coffee_start():
    step002_output.clear_output()
    step003_output.clear_output()
    step004_1_output.clear_output()
    step005_output.clear_output()
    step007_output.clear_output()
    
    # 绑定事件
    step002_button.on_click(on_read_button_clicked)
    step003_button.on_click(on_display_button_clicked)
    step004_1_button.on_click(on_show_column_clicked)
    step005_button.on_click(on_process_batch_http_request_clicked)
    step007_button.on_click(on_save_data_clicked)
    
    # 创建功能性的布局容器
    def create_control_section(title, controls):
        """创建操作区域 - 无边框，简洁"""
        return widgets.VBox([
            widgets.HTML(f"<h3 style='margin: 15px 0 8px 0; color: #495057;'>{title}</h3>"),
            widgets.VBox(controls, layout=widgets.Layout(margin='0 0 10px 0'))
        ])
    
    def create_output_section(title, output_widget):
        """创建输出区域 - 保留边框区分"""
        return widgets.VBox([
            widgets.HTML(f"<h4 style='margin: 10px 0 5px 0; color: #6c757d;'>{title}</h4>"),
            widgets.VBox([output_widget], layout=widgets.Layout(
                border='1px solid #dee2e6',
                border_radius='5px',
                padding='10px',
                background='#f8f9fa'
            ))
        ])
    
    # 主界面布局
    main_interface = widgets.VBox([
        # 标题
        widgets.HTML("""
        <div style="
            text-align: center;
            background: #f8f9fa;
            color: #495057;
            padding: 15px;
            margin: -10px -10px 20px -10px;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        ">
            <h1 style="margin: 0;">批量数据测试工具</h1>
        </div>
        """),
        
        # Step001 - 文件选择
        create_control_section("Step001: 选择数据文件", [step001_dropdown]),
        
        # API配置
        create_control_section("API配置", [step000_api_config_selector]),
        
        # Step002 - 读取数据
        create_control_section("Step002: 读取数据", [step002_button]),
        create_output_section("读取结果", step002_output),
        
        # Step003 - 数据预览
        create_control_section("Step003: 数据预览", [step003_button]),
        create_output_section("预览结果", step003_output),
        
        # Step004 - 列选择
        create_control_section("Step004: 选择数据列", [columns_container]),
        
        # Step004.1 - 列数据展示
        create_control_section("Step004.1: 列数据详情", [step004_1_button]),
        create_output_section("列数据结果", step004_1_output),
    
        # Step005 - 批量http请求
        create_control_section("Step005: 批量http请求", [max_workers_selector, progress_bar, auto_save_checkbox, step005_button]),
        create_output_section("批量http请求结果", step005_output),
    
        # Step006 - 选择要保存的数据列
        create_control_section("Step006: 选择要保存的数据列", [available_column_selector]),
        
        # Step007 - 保存数据
        create_control_section("Step007: 保存数据", [custom_filename_input, step007_button]),
        create_output_section("保存数据结果", step007_output),
        
        # 使用说明
        widgets.HTML("""
        <div style="
            margin: 20px 0 0 0;
            color: #7f8c8d;
            font-size: 14px;
        ">
            <strong>使用说明:</strong> 按照步骤顺序操作，灰色边框区域为输出结果
        </div>
        """)
    ], layout=widgets.Layout(width='100%'))
    
    # 显示界面
    display(main_interface)