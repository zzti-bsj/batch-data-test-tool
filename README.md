# 批量数据测试工具 (Batch Data Test Tool)

一个用于批量处理数据并发送HTTP请求的Python工具包。支持CSV和Excel文件读取，提供交互式Jupyter界面，方便进行批量API测试。

## 功能特性

- 📊 **数据文件支持**: 支持CSV和Excel文件读取
- 🔄 **批量处理**: 批量发送HTTP请求并处理响应
- 🎛️ **交互式界面**: 基于Jupyter Widgets的友好用户界面
- 📈 **数据预览**: 实时预览处理结果
- 💾 **智能保存**: 支持自定义文件名，自动保存到output目录
- 🛠️ **灵活配置**: 支持JSON配置文件，动态选择API接口
- 🔧 **参数映射**: 支持数据列与API参数的动态映射
- ⚡ **实时更新**: API配置切换时自动更新参数选择器

## 安装

### 基础安装
```bash
pip install batch-data-test-tool
```

### 推荐安装（包含JupyterLab）
```bash
pip install batch-data-test-tool jupyterlab
```

> 💡 **推荐使用JupyterLab**：该工具专为Jupyter环境设计，提供最佳的用户体验

## 快速开始

### 使用前准备

1. **确保data目录存在**
   ```bash
   mkdir data
   ```
   > ⚠️ 如果data目录不存在，程序会报错

2. **配置config.json**
   在项目根目录创建`config.json`文件，配置您的API接口：
   ```json
   [
       {
           "api_name": "我的API接口",
           "api_url": "http://your-api-endpoint.com/api",
           "headers": {
               "Content-Type": "application/json",
               "User-Agent": "BatchDataTestTool/1.0"
           },
           "params": {
               "conversation_text": "${conversation_text}",
               "sessionId": "default_session",
               "userKey": "app-10000"
           }
       }
   ]
   ```

   #### 占位符配置说明

   **什么是占位符？**
   占位符使用`${变量名}`格式，用于将数据文件中的列动态映射到API请求参数。

   **配置规则：**
   - 格式：`${变量名}`，变量名可以是任意字符串
   - 位置：只能放在`params`字段的值中
   - 数量：支持多个占位符同时使用

   **配置示例：**
   ```json
   {
       "params": {
           "conversation_text": "${conversation_text}",    // 映射到数据中的conversation_text列
           "user_id": "${user_id}",                        // 映射到数据中的user_id列
           "sessionId": "fixed_session_123",               // 固定值，不映射
           "timestamp": "${timestamp}"                      // 映射到数据中的timestamp列
       }
   }
   ```

   **工作原理：**
   1. 工具会自动扫描`params`中所有`${}`格式的占位符
   2. 在界面中为每个占位符创建对应的列选择器
   3. 用户选择数据列后，占位符会被替换为实际数据值
   4. 固定值（非占位符）会直接使用

   **注意事项：**
   - 占位符名称建议与数据列名保持一致，便于理解
   - 占位符名称不能包含特殊字符，建议使用字母、数字、下划线
   - 如果数据文件中没有对应的列，需要在列选择器中选择其他列

3. **准备测试数据**
   将您的CSV或Excel文件放入`data/`目录

### 在JupyterLab中使用

**coffee_start** - 通用批量处理工具：
```python
from batch_data_test_tool import coffee_start

# 启动交互式界面
coffee_start()
```

**black_tea_start** - 高级批量处理工具：
```python
from batch_data_test_tool import black_tea_start

# 启动高级交互式界面
black_tea_start()
```

### 界面操作步骤

**coffee_start 操作步骤：**
启动`coffee_start()`后，按以下步骤操作：

1. **Step001: 选择数据文件** - 从`data/`目录选择CSV或Excel文件
2. **API配置** - 从`config.json`中选择预配置的API接口
3. **Step002: 读取数据** - 点击"读取数据"按钮加载文件
4. **Step003: 数据预览** - 查看数据前5行
5. **Step004: 选择数据列** - 将数据列映射到API参数（自动根据config.json生成）
6. **Step005: 批量处理** - 发送HTTP请求并处理响应
7. **Step006: 选择保存列** - 选择要保存的结果列
8. **Step007: 保存数据** - 自定义文件名保存到`output/`目录

**black_tea_start 操作步骤：**
启动`black_tea_start()`后，按以下步骤操作：

1. **Step001: 选择数据文件** - 从`data/`目录选择CSV或Excel文件
2. **Step002: 读取数据** - 点击"读取数据"按钮加载文件
3. **Step003: 数据预览** - 查看数据前5行
4. **Step004: 选择数据列** - 将数据列映射到API参数
5. **Step005: 批量处理** - 发送HTTP请求并处理响应
6. **Step005.1: 生成结果字段** - 配置并生成解析字段
7. **Step006: 选择保存列** - 选择要保存的结果列
8. **Step007: 保存数据** - 自定义文件名保存到`output/`目录

### 工具特点

**coffee_start** - 通用批量处理工具：
- ✅ **通用性强**：直接存储`response_text`，不做解析，适用于各种API响应格式
- ✅ **用户自主**：用户可以在获得响应结果后自行解析和处理
- ✅ **完整记录**：保存完整的请求和响应信息，便于后续分析

**black_tea_start** - 高级批量处理工具：
- ✅ **智能解析**：自动解析API响应，提取指定字段值
- ✅ **字段配置**：支持配置多个解析字段，自动生成新列
- ✅ **灵活映射**：支持复杂JSON路径解析，如`data.result[0].summaryColContent.tags`
- ✅ **批量生成**：一次性为所有数据生成解析结果

**已废弃**：
- ❌ `cola_start` - 已废弃，请使用`coffee_start`或`black_tea_start`



## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交Issue和Pull Request！


## 支持

如果您遇到任何问题或有建议，请：

1. 查看 [文档](https://github.com/zzti-bsj/batch-data-test-tool#readme)
2. 搜索 [已知问题](https://github.com/zzti-bsj/batch-data-test-tool/issues)
3. 创建新的 [Issue](https://github.com/zzti-bsj/batch-data-test-tool/issues/new)
