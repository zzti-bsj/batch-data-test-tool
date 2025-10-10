import os
import sys
import json
import pandas as pd
import ipywidgets as widgets
from ..tools.data_processing import read_dataframe_from_file, clean_dataframe_for_json
from ..tools.http_request import sync_http_request, parse_http_stream_false_response, parse_http_stream_true_response
from ..tools.http_response import structure_request_params, parse_recall_result_special
from ..tools import DATA_PROCESSING_METHODS
from IPython.display import display

# 全局数据
df = None
result_data = None  # 存储批量处理的结果

# HTTP请求配置
api_url_input = widgets.Text(
    value='',
    placeholder='请输入API地址',
    description='API地址:',
    style={'description_width': 'initial'}
)

api_type_input = widgets.Text(
    value='async_sales_qa',
    placeholder='请输入API类型',
    description='API类型:',
    style={'description_width': 'initial'}
)

headers = {
    "Content-Type": "application/json",
    "User-Agent": "BatchDataTestTool/1.0"
}


# Step001. 选择数据
data_base_dir = 'data'
files = os.listdir(data_base_dir)
step001_dropdown = widgets.Dropdown(
    options=files,
    value=files[0],
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
    button_style='success',
    tooltip='点击读取选中的数据文件',
    icon='check'
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
    button_style='info',
    tooltip='展示数据的详细信息',
    icon='table'
)

# Step004. 列选择器
column_selector = widgets.Dropdown(
    options=[],
    value=None,
    description='选择列作为输入',
    disabled=True,
)

# 当数据改变时自动更新列选择器
def update_columns():
    global df, column_selector
    if df is not None:
        column_selector.options = df.columns.tolist()
        column_selector.value = df.columns.tolist()[0]
        column_selector.disabled = False
    else:
        column_selector.options = []
        column_selector.value = None
        column_selector.disabled = True


# Step004.1 展示选中列数据
step004_1_output = widgets.Output()

def on_show_column_clicked(b):
    with step004_1_output:
        step004_1_output.clear_output()
        if df is not None and 'column_selector' in globals():
            selected_col = column_selector.value
            print(f"📋 选中列: {selected_col}")
            print(f"📊 数据类型: {df[selected_col].dtype}")
            print(f"\n📄 前5个值:")
            display(df[selected_col].head())
        else:
            print("❌ 请先加载数据并选择列")

step004_1_button = widgets.Button(
    description='展示选中列数据',
    disabled=False,
    button_style='warning',
    tooltip='展示选中列的详细数据',
    icon='list'
)

# 是否启用并发 并发数
# 构建请求数据
# 向接口发送请求
# Step005. 执行批量测试
step005_output = widgets.Output()

def process_batch_http_request(
    df,
    input_field_name,
    stream_parser,
    data_processing_methods,
    api_url,
    api_type,
    headers
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
                input_data = row[input_field_name]
                # 3.1.1 字段预处理（pipeline）
                # for data_processing_method in data_processing_methods:
                #     # 使用前端传递的参数，如果没有则使用默认参数
                #     method_params = data_processing_params.get(data_processing_method, DATA_PROCESSING_METHODS[data_processing_method]["params"])
                #     input_data = DATA_PROCESSING_METHODS[data_processing_method]["object"](input_data, **method_params)
                
                req_params = structure_request_params(input_data, api_type)
                
                # 3.2 请求response
                response = sync_http_request(api_url, json.dumps(req_params), headers)
                
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
                    'recall_list': None
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
        if df is not None and column_selector.value is not None:
            result_data = process_batch_http_request(df, column_selector.value, True, [], api_url_input.value, api_type_input.value, headers)
            rd = pd.DataFrame(result_data)
            display(rd.head())

            # 更新结果列
            update_available_columns()
        else:
            print("❌ 请先加载数据并选择列")


step005_button = widgets.Button(
    description='批量处理http请求',
    disabled=False,
    button_style='warning',
    tooltip='批量处理http请求',
    icon='list'
)


# Step006 选择要保存的列
available_columns_selector = widgets.SelectMultiple(
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
        available_columns_selector.options = tmp_df.columns.tolist()
        # 默认选择前3列（如果存在的话）
        default_selection = tmp_df.columns.tolist()[:3]
        available_columns_selector.value = default_selection
        available_columns_selector.disabled = False
        print(f"✅ 已更新可选列，共 {len(tmp_df.columns)} 列")
        print(f"📋 可选列: {list(tmp_df.columns)}")
        print(f"🎯 默认选中: {default_selection}")
    else:
        available_columns_selector.options = []
        available_columns_selector.value = []
        available_columns_selector.disabled = True
        print("❌ 没有可选择的列，请先完成批量处理")


# Step007 保存数据文件
step007_output = widgets.Output()

# 更新保存数据功能（支持多列）
def on_save_data_clicked(b):
    global available_columns_selector, result_data
    with step007_output:
        step007_output.clear_output()
        selected_columns = available_columns_selector.value
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
                selected_df.to_excel('saved_file.xlsx', index=False)
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
    button_style='primary',
    tooltip='将选中的多列数据保存到CSV文件'
)



def simple_start():
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
            widgets.HTML(f"<h3 style='margin: 15px 0 8px 0; color: #2c3e50;'>{title}</h3>"),
            widgets.VBox(controls, layout=widgets.Layout(margin='0 0 10px 0'))
        ])
    
    def create_output_section(title, output_widget):
        """创建输出区域 - 保留边框区分"""
        return widgets.VBox([
            widgets.HTML(f"<h4 style='margin: 10px 0 5px 0; color: #27ae60;'>📊 {title}</h4>"),
            widgets.VBox([output_widget], layout=widgets.Layout(
                border='1px solid #27ae60',
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
            background: #34495e;
            color: white;
            padding: 15px;
            margin: -10px -10px 20px -10px;
            border-radius: 5px;
        ">
            <h1 style="margin: 0;">📊 批量数据测试工具</h1>
        </div>
        """),
        
        # Step001 - 文件选择
        create_control_section("Step001: 选择数据文件", [step001_dropdown]),
        
        # API配置
        create_control_section("API配置", [api_url_input, api_type_input]),
        
        # Step002 - 读取数据
        create_control_section("Step002: 读取数据", [step002_button]),
        create_output_section("读取结果", step002_output),
        
        # Step003 - 数据预览
        create_control_section("Step003: 数据预览", [step003_button]),
        create_output_section("预览结果", step003_output),
        
        # Step004 - 列选择
        create_control_section("Step004: 选择数据列", [column_selector]),
        
        # Step004.1 - 列数据展示
        create_control_section("Step004.1: 列数据详情", [step004_1_button]),
        create_output_section("列数据结果", step004_1_output),
    
        # Step005 - 批量http请求
        create_control_section("Step005: 批量http请求", [step005_button]),
        create_output_section("批量http请求结果", step005_output),
    
        # Step006 - 选择要保存的数据列
        create_control_section("Step006: 选择要保存的数据列", [available_columns_selector]),
        
        # Step007 - 保存数据
        create_control_section("Step007: 保存数据", [step007_button]),
        create_output_section("保存数据结果", step007_output),
        
        # 使用说明
        widgets.HTML("""
        <div style="
            margin: 20px 0 0 0;
            color: #7f8c8d;
            font-size: 14px;
        ">
            💡 <strong>使用说明:</strong> 按照步骤顺序操作，绿色边框区域为输出结果
        </div>
        """)
    ], layout=widgets.Layout(width='100%'))
    
    # 显示界面
    display(main_interface)