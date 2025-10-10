# 批量数据测试工具 (Batch Data Test Tool)

一个用于批量处理数据并发送HTTP请求的Python工具包。支持CSV和Excel文件读取，提供交互式Jupyter界面，方便进行批量API测试。

## 功能特性

- 📊 **数据文件支持**: 支持CSV和Excel文件读取
- 🔄 **批量处理**: 批量发送HTTP请求并处理响应
- 🎛️ **交互式界面**: 基于Jupyter Widgets的友好用户界面
- 📈 **数据预览**: 实时预览处理结果
- 💾 **结果导出**: 支持将处理结果导出为Excel文件
- 🛠️ **灵活配置**: 支持自定义API端点和请求参数

## 安装

```bash
pip install batch-data-test-tool
```

## 快速开始

### 在Jupyter Notebook中使用

```python
from batch_data_test_tool import simple_start

# 启动交互式界面
simple_start()
```

### 作为命令行工具使用

```bash
batch-test-tool
```

## 使用示例

### 1. 基本用法

```python
from batch_data_test_tool import (
    read_dataframe_from_file,
    sync_http_request,
    structure_request_params
)
import json

# 读取数据文件
df = read_dataframe_from_file('data/test.xlsx')

# 配置API
api_url = 'http://your-api-endpoint.com/api'
headers = {
    "Content-Type": "application/json",
    "User-Agent": "BatchDataTestTool/1.0"
}

# 处理单条数据
input_data = df.iloc[0]['your_column']
params = structure_request_params(input_data, 'async_sales_qa')
response = sync_http_request(api_url, json.dumps(params), headers)
```

### 2. 批量处理

```python
from batch_data_test_tool.apps.simple_start import process_batch_http_request

# 批量处理数据
results = process_batch_http_request(
    df=df,
    input_field_name='your_column',
    stream_parser=True,
    data_processing_methods=[],
    api_url=api_url,
    api_type='async_sales_qa',
    headers=headers
)
```

## API 参考

### 核心函数

#### `read_dataframe_from_file(filepath)`
从文件中读取DataFrame，支持CSV和Excel格式。

**参数:**
- `filepath` (str): 文件路径

**返回:**
- `pandas.DataFrame`: 读取的数据

#### `sync_http_request(url, request_json_data, headers)`
发送同步HTTP请求。

**参数:**
- `url` (str): 请求URL
- `request_json_data` (str): JSON格式的请求数据
- `headers` (dict): 请求头

**返回:**
- `requests.Response`: HTTP响应对象

#### `structure_request_params(data, api_type)`
根据API类型构建请求参数。

**参数:**
- `data`: 输入数据
- `api_type` (str): API类型

**返回:**
- `dict`: 构建的请求参数

### 数据预处理

#### `clean_dataframe_for_json(df)`
清理DataFrame中的NaN值，使其能够正确序列化为JSON。

#### `join_list_with_delimiter(list_data, delimiter)`
使用分隔符连接列表数据。

## 配置

### API类型配置

目前支持的API类型：
- `async_sales_qa`: 异步销售问答API

### 数据预处理方法

- `join_list_with_delimiter`: 列表数据连接

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black batch_data_test_tool/
```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持CSV和Excel文件读取
- 提供交互式Jupyter界面
- 支持批量HTTP请求处理
- 支持结果导出

## 支持

如果您遇到任何问题或有建议，请：

1. 查看 [文档](https://github.com/zzti-bsj/batch-data-test-tool#readme)
2. 搜索 [已知问题](https://github.com/zzti-bsj/batch-data-test-tool/issues)
3. 创建新的 [Issue](https://github.com/zzti-bsj/batch-data-test-tool/issues/new)
