import os
import sys
import json
import pandas as pd
import ipywidgets as widgets
from ..tools.data_processing import read_dataframe_from_file, clean_dataframe_for_json
from ..tools.http_request import sync_http_request, parse_http_stream_false_response, parse_http_stream_true_response
from ..tools.http_response import structure_request_params, parse_recall_result_special
from ..tools import DATA_PROCESSING_METHODS
from ..tools.get_config import get_api_url_name_list, get_api_params_placeholder_list_by_name, get_api_url_by_name, get_api_headers_by_name, get_api_params_by_name, get_api_timeout_by_name
from IPython.display import display

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

# 是否启用并发 并发数
# 构建请求数据
# 向接口发送请求
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
        
        parsed_result = []
        # 3. 对于此列的每一个数据都调用接口请求数据
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
                response = sync_http_request(api_url, request_params, headers, timeout)
                
                # 记录响应时间
                if response is not None and hasattr(response, 'response_time'):
                    new_df.loc[index, 'response_time'] = response.response_time
                else:
                    new_df.loc[index, 'response_time'] = None
                
                if stream_parser:
                    answer = parse_http_stream_false_response(response)
                    # 当没有召回的时候
                    try:
                        recall_list = parse_http_stream_true_response(response)
                    except Exception as e:
                        print(f"第「{index}」列的召回结果为空")
                        recall_list = []
                    res = {
                        'answer': answer,
                        'recall_list': parse_recall_result_special(recall_list)
                    }
                else:
                    # parse_http_nostream_response
                    res = {
                        'answer': None,  # 添加输入数据
                        'recall_list': None  # 需要实现这个函数
                    }
                parsed_result.append(res)
                
            except Exception as e:
                print(f"处理第{index}行时出错: {e}")
                # 添加错误结果
                parsed_result.append({
                    'answer': f"处理失败: {str(e)}",
                    'recall_list': None,
                    'response_time': None
                })
            # print(res)
            # 处理完一条数据
        result_df = pd.DataFrame(parsed_result)
        new_df = new_df.assign(**result_df.to_dict('list'))
        
        # 清理NaN值，使其能够正确序列化为JSON
        new_df = clean_dataframe_for_json(new_df)
        
        # 将结果转换为字典格式返回
        global result_data
        result_data = new_df.to_dict('records')
        
        print(f"✅ 批量处理完成！处理了 {len(result_data)} 条记录")
        print(f"📊 结果数据列: {list(new_df.columns)}")
        
        # 更新列选择器
        update_available_columns()
        
        return result_data
        
    except Exception as e:
        print('a')
        return 'Error'

# 创建事件处理函数
def on_process_batch_http_request_clicked(b):
    """批量处理http请求按钮点击事件"""
    global df, result_data
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
            rd = pd.DataFrame(result_data)
            display(rd.head())

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
                print(f"✅ 文件已保存到: {filepath}")
                
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



def cola_start():
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
        create_control_section("Step005: 批量http请求", [step005_button]),
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