import os, time, threading
import logging
import json
import pandas as pd
import ipywidgets as widgets
from concurrent.futures import ThreadPoolExecutor
from ..tools.data_processing import read_dataframe_from_file, clean_dataframe_for_json
from ..tools.http_request import sync_http_request, parse_http_stream_false_response, parse_http_stream_true_response
from ..tools.http_response import structure_request_params, parse_recall_result_special
from ..tools import DATA_PROCESSING_METHODS, RESPONSE_PARSING_METHODS, get_json_field_value, get_all_json_keys
from ..tools.get_config import get_api_url_name_list, get_api_params_placeholder_list_by_name, get_api_url_by_name, get_api_headers_by_name, get_api_params_by_name
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
processing_lock = threading.Lock()  # 处理锁，防止重复执行
is_processing = False  # 当前是否正在处理


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
    max=30,
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
    bar_style='',
    orientation='horizontal',
    style={'bar_color': '#6c757d'},
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
    params: str
):
    global preview_response_first, is_processing
    
    # 使用锁防止重复执行
    with processing_lock:
        if is_processing:
            step005_output.append_stdout("⚠️ 已有任务正在执行中，请等待完成\n")
            return []
        
        is_processing = True
    
    try:
        # 清空输出区域并重置状态
        step005_output.clear_output()
        progress_bar.value = 0
        step005_output.append_stdout("🚀 开始批量HTTP请求处理...\n\n")
        
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
                    'request_params': request_params
                }

                # response = sync_http_request(api_url, request_params, headers)
                func_params_dic[index] = func_params

            except Exception as e:
                logging.error(f"构建第{index}行请求参数时出错: {e} \n\n api_url:参数{func_params}；headers:参数{headers}；request_params:参数{request_params}")
                print(f"处理第{index}行时出错: {e}")
                raise Exception(f"处理第{index}行时出错: {e}")


        # 初始化进度条
        total_rows = len(new_df)
        progress_bar.max = total_rows
        progress_bar.value = 0
        
        # 实时并发执行和结果处理 - 改进版本
        results = {}
        completed_count = 0
        lock = threading.Lock()
        
        def update_ui_with_result(index, response):
            """在UI线程中更新结果和日志"""
            nonlocal completed_count
            exception_message = ''
            
            try:
                new_df.loc[index, 'response_text'] = response.text
                status_msg = f"✅ 行{index}: 请求完成\n"
            except Exception as e:
                new_df.loc[index, 'response_text'] = None
                exception_message = f"数据「{index}」获取response_text时错误: {str(e)}"
                logging.error(f"数据「{index}」获取response_text时错误: {str(e)}")
                status_msg = f"❌ 行{index}: {exception_message}\n"
            
            # 安全更新UI
            with lock:
                step005_output.append_stdout(status_msg)
                completed_count += 1
                progress_bar.value = completed_count
        
        def process_future(index, future):
            """处理单个future的结果"""
            try:
                response = future.result()
                results[index] = response
                
                # 使用线程安全的方式更新UI
                threading.Thread(target=update_ui_with_result, args=(index, response), daemon=True).start()
                
            except Exception as e:
                step005_output.append_stdout(f"❌ 行{index}: 执行失败 - {str(e)}\n")
                with lock:
                    completed_count += 1
                    progress_bar.value = completed_count
        
        # 启动并发执行
        with ThreadPoolExecutor(max_workers=max_workers_selector.value) as executor:
            futures = {index: executor.submit(sync_http_request, **args) for index, args in func_params_dic.items()}
            
            # 为每个future创建监控线程
            monitor_threads = []
            for index, future in futures.items():
                thread = threading.Thread(target=process_future, args=(index, future), daemon=True)
                thread.start()
                monitor_threads.append(thread)
            
            # 等待所有监控线程完成
            for thread in monitor_threads:
                thread.join()
                
        # 最终状态更新
        step005_output.append_stdout(f"\n🎉 所有请求完成！成功: {len([r for r in results.values() if r])}, 总数: {len(func_params_dic)}\n")
          
        # 清理NaN值，使其能够正确序列化为JSON
        new_df = clean_dataframe_for_json(new_df)
        
        # 将结果转换为字典格式返回
        global result_data
        result_data = new_df.to_dict('records')
        logging.info(f"✅ 批量处理完成！处理了 {len(result_data)} 条记录")
        
        # 更新列选择器
        update_available_columns()
        
        # 更新解析字段配置的路径选项
        update_all_field_path_options()
        
        # 更新预览响应第一个
        preview_response_first = result_data[0]['response_text']

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
                filename = f"auto_save_{timestamp}.csv"
                filepath = os.path.join(output_dir, filename)
                
                # 保存所有数据
                new_df.to_csv(filepath, index=False)
                logging.info(f"✅ 自动保存完成！文件已保存到: {filepath}")
                step005_output.append_stdout(f"💾 自动保存完成！文件已保存到: {filepath}\n")
            except Exception as e:
                logging.error(f"自动保存失败: {e}")
                step005_output.append_stdout(f"❌ 自动保存失败: {e}\n")
        
        return result_data
        
    except Exception as e:
        logging.error(f"批量处理出错: {e}")
        step005_output.append_stdout(f"❌ 批量处理出错: {e}\n")
        return []
        
    finally:
        # 确保最终释放处理锁
        with processing_lock:
            is_processing = False

# 创建事件处理函数
def on_process_batch_http_request_clicked(b):
    """批量处理http请求按钮点击事件"""
    global df, result_data
    
    # 防止重复点击
    if is_processing:
        step005_output.append_stdout("⚠️ 已有任务正在执行中，请等待完成\n")
        return
    
    # 检查必要条件
    if df is None or columns_selector is None or step000_api_config_selector.value is None:
        step005_output.append_stdout("❌ 请先加载数据并选择列\n")
        return
    
    # 临时禁用按钮防止重复点击
    step005_button.disabled = True
    step005_button.description = "执行中..."
    
    # 记录日志元数据
    logging.info(structured_logging_metadata(
        input_file_name=step001_dropdown.value,
        all_columns=df.columns.tolist(),
        input_columns=[column.description for column in columns_selector],
        input_shape=df.shape,
        input_number=len(df)
    ))
    
    # 在后台线程中执行处理，避免阻塞UI
    def execute_processing():
        try:
            result_data = process_batch_http_request(
                df, 
                columns_selector, 
                True, 
                [], 
                get_api_url_by_name(api_name=step000_api_config_selector.value), 
                get_api_headers_by_name(api_name=step000_api_config_selector.value),
                get_api_params_by_name(api_name=step000_api_config_selector.value)
            )
            
            # 在UI线程中更新结果
            if result_data and len(result_data) > 0:
                step005_output.append_stdout("\n📊 处理结果预览:\n")
                rd = pd.DataFrame(result_data)
                with step005_output:
                    display(rd.head())
            else:
                step005_output.append_stdout("❌ 没有处理结果数据\n")

            # 更新结果列
            update_available_columns()
            
        except Exception as e:
            step005_output.append_stdout(f"❌ 执行过程中出错: {str(e)}\n")
        finally:
            # 恢复按钮状态
            step005_button.disabled = False
            step005_button.description = "批量处理http请求"
    
    # 启动处理线程
    processing_thread = threading.Thread(target=execute_processing, daemon=True)
    processing_thread.start()


step005_button = widgets.Button(
    description='批量处理http请求',
    disabled=False,
    button_style='',
    tooltip='批量处理http请求'
)


# Step005.1 Response解析配置
# 解析字段配置列表
parsing_fields = []

# preview_response_first
preview_response_first = None

# 新增字段按钮
add_field_button = widgets.Button(
    description='新增解析字段',
    disabled=False,
    button_style='',
    tooltip='添加新的响应解析字段'
)

# 手动更新字段路径按钮
manual_update_button = widgets.Button(
    description='手动更新字段路径',
    disabled=False,
    button_style='',
    tooltip='手动更新所有字段的路径选项'
)

# 生成结果字段按钮
generate_result_fields_button = widgets.Button(
    description='生成结果字段',
    disabled=False,
    button_style='',
    tooltip='根据配置的解析器处理所有response_text数据并生成新字段'
)

# 字段配置容器
field_configs_container = widgets.VBox([])

# 解析方式选择器
parsing_method_selector = widgets.Dropdown(
    options=[
        (method['method_name'], method['method'])
        for method in RESPONSE_PARSING_METHODS.values()
    ],
    value=None,
    description='选择解析器',
    disabled=False,
    style={'description_width': 'initial'}
)

# 字段路径选择器（动态生成）
field_path_selector = widgets.Dropdown(
    options=[],
    value=None,
    description='选择Response字段路径',
    disabled=True,
    style={'description_width': 'initial'}
)

# 预解析按钮
preview_parse_button = widgets.Button(
    description='预解析',
    disabled=True,
    button_style='success',
    tooltip='预览解析结果',
    icon='eye'
)

# 预解析结果输出
step005_1_output = widgets.Output()

def on_add_field_clicked(b):
    """新增字段按钮点击事件"""
    global parsing_fields
    
    print(f"🔍 新增字段按钮被点击")
    
    # 创建字段配置
    field_config = {
        'field_name': f'field_{len(parsing_fields) + 1}',
        'parsing_method': None,
        'field_path': None,
        'widgets': {}
    }
    
    # 创建字段配置UI
    field_widgets = create_field_config_widgets(field_config)
    field_config['widgets'] = field_widgets
    
    # 添加到配置列表
    parsing_fields.append(field_config)
    
    # 更新容器
    update_field_configs_container()
    
    # 立即更新字段路径选项
    print(f"🔍 立即更新新字段的路径选项")
    update_field_path_options(field_config)

def create_field_config_widgets(field_config):
    global preview_response_first
    """创建单个字段的配置UI"""
    # 字段名称输入框
    field_name_input = widgets.Text(
        value=field_config['field_name'],
        placeholder='输入字段名称',
        description='字段名:',
        style={'description_width': 'initial'}
    )
    
    # 解析方式选择器（固定为获取指定字段值）
    parsing_method = widgets.Dropdown(
        options=[
            (method['method_name'], method['method'])
            for method in RESPONSE_PARSING_METHODS.values()
        ],
        value=None,
        description='选择解析器',
        disabled=False,  # 禁用选择，固定为获取指定字段值
        style={'description_width': 'initial'}
    )
    
    # 字段路径选择器
    field_path = widgets.Dropdown(
        options=[],
        value=None,
        description='选择Response字段路径',
        disabled=True,
        style={'description_width': 'initial'}
    )
    
    # 预解析按钮
    preview_button = widgets.Button(
        description='预解析',
        disabled=True,
        button_style='',
        tooltip='预览解析结果'
    )
    
    # 删除按钮
    delete_button = widgets.Button(
        description='删除',
        disabled=False,
        button_style='',
        tooltip='删除此字段配置'
    )
    
    # 预解析结果输出
    preview_output = widgets.Output()
    
    # 绑定事件
    def on_field_path_changed(change):
        field_config['field_path'] = change['new']
        preview_button.disabled = False
        print(f"🔍 字段路径改变: {change['new']}")
    
    def on_preview_clicked(b):
        with preview_output:
            preview_output.clear_output()
            preview_parse_result(field_config)
    
    def on_delete_clicked(b):
        global parsing_fields
        if field_config in parsing_fields:
            parsing_fields.remove(field_config)
            update_field_configs_container()
    
    def on_field_name_changed(change):
        field_config['field_name'] = change['new']
    
    def on_parsing_method_changed(change):
        field_config['parsing_method'] = change['new']
    
    # 绑定事件处理器
    field_path.observe(on_field_path_changed, names='value')
    parsing_method.observe(on_parsing_method_changed, names='value')
    field_name_input.observe(on_field_name_changed, names='value')
    preview_button.on_click(on_preview_clicked)
    delete_button.on_click(on_delete_clicked)
    
    print(f"🔍 事件处理器已绑定")
    
    return {
        'field_name': field_name_input,
        'parsing_method': parsing_method,
        'field_path': field_path,
        'preview_button': preview_button,
        'delete_button': delete_button,
        'preview_output': preview_output
    }

def update_field_path_options(field_config):
    """更新字段路径选项"""
    global result_data
    
    print(f"🔍 开始更新字段路径选项...")
    print(f"🔍 result_data状态: {result_data is not None}, 长度: {len(result_data) if result_data else 0}")
    
    if result_data is None or len(result_data) == 0:
        print(f"❌ result_data为空，无法更新字段路径")
        return
    
    # 获取第一个response作为样本
    first_response = result_data[0]
    print(f"🔍 第一个response的keys: {list(first_response.keys())}")
    
    if 'response_text' not in first_response:
        print(f"❌ 第一个response中没有response_text字段")
        return
    
    try:
        # 解析JSON响应
        response_text = first_response['response_text']
        print(f"🔍 response_text长度: {len(response_text)}")
        print(f"🔍 response_text前200字符: {response_text[:200]}")
        
        response_json = json.loads(response_text)
        print(f"✅ JSON解析成功，类型: {type(response_json)}")
        
        # 获取所有字段路径
        all_keys = get_all_json_keys(response_json)
        print(f"✅ 获取到 {len(all_keys)} 个字段路径")
        print(f"🔍 前10个路径: {all_keys[:10]}")
        
        # 检查widgets是否存在并更新字段路径下拉框
        if 'widgets' in field_config and 'field_path' in field_config['widgets']:
            field_config['widgets']['field_path'].options = all_keys
            field_config['widgets']['field_path'].disabled = False
            print(f"✅ 字段路径下拉框已更新，选项数量: {len(all_keys)}")
        else:
            print(f"❌ field_config中没有widgets或field_path")
            print(f"🔍 field_config keys: {list(field_config.keys())}")
            
    except Exception as e:
        print(f"❌ 解析响应JSON时出错: {e}")
        import traceback
        traceback.print_exc()

def preview_parse_result(field_config):
    """预览解析结果"""
    global result_data
    
    if result_data is None or len(result_data) == 0:
        print("❌ 没有可用的响应数据")
        return
    
    try:
        # 获取第一个response作为样本
        first_response = result_data[0]
        if 'response_text' not in first_response:
            print("❌ 响应数据中没有response_text字段")
            return
        
        # 解析JSON响应
        response_json = json.loads(first_response['response_text'])
        
        # 使用__init__.py中配置的方法进行解析
        parse_method = field_config['parsing_method']
        field_path = field_config['field_path']
        if parse_method and field_path:
            # 使用RESPONSE_PARSING_METHODS中配置的方法
            result = parse_method(response_json, field_path)
            print(f"✅ 字段路径: {field_path}")
            print(f"📊 解析结果: {result}")
            print(f"📋 数据类型: {type(result).__name__}")
            
            # 如果结果是复杂类型，显示更多信息
            if isinstance(result, (list, dict)):
                print(f"📏 结果长度: {len(result) if hasattr(result, '__len__') else 'N/A'}")
                if isinstance(result, list) and len(result) > 0:
                    print(f"🔍 列表第一个元素: {result[0]}")
                elif isinstance(result, dict) and len(result) > 0:
                    print(f"🔍 字典第一个键值对: {list(result.items())[0]}")
        else:
            print("❌ 请先选择解析器和字段路径")
            
    except Exception as e:
        print(f"❌ 预览解析时出错: {e}")
        import traceback
        traceback.print_exc()

def update_field_configs_container():
    """更新字段配置容器"""
    global parsing_fields
    
    # 清空容器
    field_configs_container.children = []
    
    # 为每个字段配置创建UI
    for i, field_config in enumerate(parsing_fields):
        widgets_list = field_config['widgets']
        
        # 创建字段配置的UI布局
        field_ui = widgets.VBox([
            widgets.HTML(f"<h4 style='margin: 10px 0 5px 0; color: #495057;'>字段配置 {i+1}</h4>"),
            widgets.HBox([
                widgets_list['field_name'],
                widgets_list['parsing_method'],
                widgets_list['field_path'],
                widgets_list['preview_button'],
                widgets_list['delete_button']
            ]),
            widgets_list['preview_output']
        ], layout=widgets.Layout(
            border='1px solid #dee2e6',
            border_radius='5px',
            padding='10px',
            margin='5px 0'
        ))
        
        field_configs_container.children += (field_ui,)

def update_all_field_path_options():
    """更新所有字段配置的路径选项"""
    global parsing_fields
    
    print(f"🔍 开始更新所有字段配置的路径选项，共 {len(parsing_fields)} 个字段配置")
    
    for i, field_config in enumerate(parsing_fields):
        print(f"🔍 更新第 {i+1} 个字段配置")
        update_field_path_options(field_config)

def on_manual_update_clicked(b):
    """手动更新字段路径按钮点击事件"""
    print(f"🔍 手动更新字段路径按钮被点击")
    update_all_field_path_options()

def on_generate_result_fields_clicked(b):
    """生成结果字段按钮点击事件"""
    global result_data, parsing_fields
    
    print(f"🔍 生成结果字段按钮被点击")
    
    if result_data is None or len(result_data) == 0:
        print("❌ 没有可用的响应数据，请先完成Step005")
        return
    
    if not parsing_fields:
        print("❌ 没有配置任何解析字段，请先添加解析字段")
        return
    
    # 检查所有字段配置是否完整
    incomplete_fields = []
    for field_config in parsing_fields:
        if not field_config.get('field_name'):
            incomplete_fields.append("字段名称")
        if not field_config.get('parsing_method'):
            incomplete_fields.append("解析器")
        if not field_config.get('field_path'):
            incomplete_fields.append("字段路径")
    
    if incomplete_fields:
        print(f"❌ 字段配置不完整，缺少: {', '.join(set(incomplete_fields))}")
        return
    
    try:
        print(f"✅ 开始处理 {len(result_data)} 条数据，生成 {len(parsing_fields)} 个新字段")
        
        # 为每条数据生成新字段
        for index, row_data in enumerate(result_data):
            if 'response_text' not in row_data:
                print(f"⚠️ 第{index}行数据没有response_text字段，跳过")
                continue
            
            try:
                # 解析JSON响应
                response_json = json.loads(row_data['response_text'])
                
                # 为每个配置的字段生成结果
                for field_config in parsing_fields:
                    field_name = field_config['field_name']
                    parse_method = field_config['parsing_method']
                    field_path = field_config['field_path']
                    
                    # 使用配置的解析方法处理数据
                    result = parse_method(response_json, field_path)
                    
                    # 将结果保存到数据中
                    row_data[field_name] = result
                    
            except Exception as e:
                print(f"⚠️ 处理第{index}行数据时出错: {e}")
                # 为所有字段设置None值
                for field_config in parsing_fields:
                    field_name = field_config['field_name']
                    row_data[field_name] = None
        
        print(f"✅ 成功生成结果字段！")
        print(f"📊 新增字段: {[field_config['field_name'] for field_config in parsing_fields]}")
        print(f"📋 数据总列数: {len(result_data[0]) if result_data else 0}")
        
        # 显示完成提示
        print("🎉 Step005.1 已完成！所有配置的解析字段已成功生成到数据中。")
        print("💡 提示：现在可以进入Step006选择要保存的字段。")
        
    except Exception as e:
        print(f"❌ 生成结果字段时出错: {e}")
        import traceback
        traceback.print_exc()

# 绑定按钮事件
add_field_button.on_click(on_add_field_clicked)
manual_update_button.on_click(on_manual_update_clicked)
generate_result_fields_button.on_click(on_generate_result_fields_clicked)


# Step006 选择要保存的列
available_column_selector = widgets.SelectMultiple(
    options=[],
    value=[],
    description='选择要保存的列',
    disabled=True,
    layout=widgets.Layout(width='300px', height='150px')
)

# 更新可选字段按钮
update_available_columns_button = widgets.Button(
    description='更新可选字段',
    disabled=False,
    button_style='',
    tooltip='刷新获取DataFrame的所有字段列'
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

def on_update_available_columns_clicked(b):
    """更新可选字段按钮点击事件"""
    print(f"🔍 更新可选字段按钮被点击")
    update_available_columns()


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
                    filename = f"{custom_name}.csv"
                else:
                    # 使用默认时间序列文件名
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"batch_test_result_{timestamp}.csv"
                filepath = os.path.join(output_dir, filename)
                
                # 保存文件
                selected_df.to_csv(filepath, index=False)
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

# 绑定更新可选字段按钮事件
update_available_columns_button.on_click(on_update_available_columns_clicked)



def black_tea_start():
    step002_output.clear_output()
    step003_output.clear_output()
    step004_1_output.clear_output()
    step005_output.clear_output()
    step005_1_output.clear_output()
    step007_output.clear_output()
    
    # 绑定事件
    step002_button.on_click(on_read_button_clicked)
    step003_button.on_click(on_display_button_clicked)
    step004_1_button.on_click(on_show_column_clicked)
    step005_button.on_click(on_process_batch_http_request_clicked)
    step007_button.on_click(on_save_data_clicked)
    
    # 创建现代化卡片组件 - 低调版本
    def create_card(title, controls):
        """创建现代化卡片组件"""
        return widgets.VBox([
            widgets.HTML(f"""
            <div style="
                background: #f8f9fa;
                color: #495057;
                padding: 12px 20px;
                margin: 0;
                border-radius: 8px 8px 0 0;
                font-size: 16px;
                font-weight: 600;
                display: flex;
                align-items: center;
                border: 1px solid #dee2e6;
                border-bottom: none;
            ">
                {title}
            </div>
            """),
            widgets.VBox(controls, layout=widgets.Layout(
                padding='20px',
                background='white',
                border='1px solid #dee2e6',
                border_top='none',
                border_radius='0 0 8px 8px',
                margin='0 0 15px 0'
            ))
        ], layout=widgets.Layout(
            background='white',
            border_radius='8px',
            margin='10px 0'
        ))
    
    def create_result_section(title, output_widget):
        """创建结果展示区域"""
        return widgets.VBox([
            widgets.HTML(f"""
            <div style="
                background: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                margin: 0;
                border-radius: 8px 8px 0 0;
                font-size: 14px;
                font-weight: 600;
                display: flex;
                align-items: center;
                border: 1px solid #dee2e6;
                border-bottom: none;
            ">
                {title}
            </div>
            """),
            widgets.VBox([output_widget], layout=widgets.Layout(
                padding='15px',
                background='white',
                border='1px solid #dee2e6',
                border_top='none',
                border_radius='0 0 8px 8px',
                min_height='100px'
            ))
        ], layout=widgets.Layout(
            margin='10px 0'
        ))
    
    # 主界面布局
    main_interface = widgets.VBox([
        # 简洁标题
        widgets.HTML("""
        <div style="
            background: #f8f9fa;
            color: #495057;
            padding: 30px;
            margin: -20px -20px 30px -20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #dee2e6;
        ">
            <h1 style="margin: 0; font-size: 28px; font-weight: 600; position: relative;">
                批量数据测试工具
            </h1>
            <p style="margin: 10px 0 0 0; font-size: 14px; color: #6c757d; position: relative;">
                简洁、高效、实用的批量数据处理工具
            </p>
        </div>
        """),
        
        # 配置区域组
        widgets.HTML("""
        <div style="
            font-size: 18px;
            font-weight: 600;
            color: #495057;
            margin: 20px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #6c757d;
        ">
            基础配置
        </div>
        """),
        
        # Step001 - 文件选择
        create_card("Step001: 选择数据文件", [step001_dropdown]),
        
        # API配置
        create_card("API配置", [step000_api_config_selector]),
        
        # 数据处理区域组
        widgets.HTML("""
        <div style="
            font-size: 18px;
            font-weight: 600;
            color: #495057;
            margin: 30px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #6c757d;
        ">
            数据处理
        </div>
        """),
        
        # Step002 - 读取数据
        create_card("Step002: 读取数据", [step002_button]),
        create_result_section("读取结果", step002_output),
        
        # Step003 - 数据预览
        create_card("Step003: 数据预览", [step003_button]),
        create_result_section("预览结果", step003_output),
        
        # Step004 - 列选择
        create_card("Step004: 选择数据列", [columns_container]),
        
        # Step004.1 - 列数据展示
        create_card("Step004.1: 列数据详情", [step004_1_button]),
        create_result_section("列数据结果", step004_1_output),
    
        # 请求处理区域组
        widgets.HTML("""
        <div style="
            font-size: 18px;
            font-weight: 600;
            color: #495057;
            margin: 30px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #6c757d;
        ">
            请求处理
        </div>
        """),
        
        # Step005 - 批量http请求
        create_card("Step005: 批量HTTP请求", [max_workers_selector, progress_bar, auto_save_checkbox, step005_button]),
        create_result_section("批量请求结果", step005_output),
    
        # 响应解析区域组
        widgets.HTML("""
        <div style="
            font-size: 18px;
            font-weight: 600;
            color: #495057;
            margin: 30px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #6c757d;
        ">
            响应解析
        </div>
        """),
        
        # Step005.1 - Response解析配置
        create_card("Step005.1: Response解析配置", [add_field_button, manual_update_button, generate_result_fields_button, field_configs_container]),
        create_result_section("解析配置结果", step005_1_output),
    
        # 数据保存区域组
        widgets.HTML("""
        <div style="
            font-size: 18px;
            font-weight: 600;
            color: #495057;
            margin: 30px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #6c757d;
        ">
            数据保存
        </div>
        """),
        
        # Step006 - 选择要保存的数据列
        create_card("Step006: 选择要保存的数据列", [update_available_columns_button, available_column_selector]),
        
        # Step007 - 保存数据
        create_card("Step007: 保存数据", [custom_filename_input, step007_button]),
        create_result_section("保存数据结果", step007_output),
        
        # 简洁页脚
        widgets.HTML("""
        <div style="
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0 0 0;
            text-align: center;
            border: 1px solid #dee2e6;
        ">
            <div style="
                font-size: 14px; 
                font-weight: 600; 
                color: #495057;
                margin-bottom: 10px;
            ">
                使用说明
            </div>
            <p style="margin: 0; color: #6c757d; font-size: 13px; line-height: 1.5;">
                按照步骤顺序操作，灰色标题区域为输出结果，白色区域为配置操作。
            </p>
        </div>
        """)
    ], layout=widgets.Layout(
        width='100%',
        padding='20px',
        background='white',
        border_radius='8px',
        border='1px solid #dee2e6'
    ))
    
    # 显示界面
    display(main_interface)