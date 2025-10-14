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

```python
from batch_data_test_tool import cola_start

# 启动交互式界面
cola_start()
```

### 界面操作步骤

启动`cola_start()`后，按以下步骤操作：

1. **Step001: 选择数据文件** - 从`data/`目录选择CSV或Excel文件
2. **API配置** - 从`config.json`中选择预配置的API接口
3. **Step002: 读取数据** - 点击"读取数据"按钮加载文件
4. **Step003: 数据预览** - 查看数据前5行
5. **Step004: 选择数据列** - 将数据列映射到API参数（自动根据config.json生成）
6. **Step005: 批量处理** - 发送HTTP请求并处理响应
7. **Step006: 选择保存列** - 选择要保存的结果列
8. **Step007: 保存数据** - 自定义文件名保存到`output/`目录


## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.2.0
- 🚀 **重大更新 - coffee_start通用批量处理工具**:
  - 新增`coffee_start`入口，提供通用的批量处理功能
  - 保存完整Response结果，不做解析，提升通用性
  - 支持嵌套参数解析，处理复杂API配置结构
- ⚡ **性能优化**:
  - 增加并发处理功能，支持多线程批量请求
  - 动态进度条显示，实时展示处理进度
  - 自动保存功能，防止大量数据长时间运行丢失
- 📊 **日志系统**:
  - 结构化日志记录，包含元数据日志
  - 每行数据详细日志（数据本身、Request、Response、异常信息）
  - 日志分离：控制台显示简洁信息，文件记录详细信息
- 🎯 **界面增强**:
  - 并发数选择器，可调节处理并发度
  - 自动保存勾选框，支持处理完成后自动保存
  - 进度条实时显示处理状态

### v1.1.1
- ✨ **新增功能**:
  - 支持JSON配置文件，可配置多个API接口
  - 动态参数映射，支持数据列与API参数的灵活映射
  - API配置切换时自动更新参数选择器
  - 自定义文件名保存功能
  - 自动创建output目录并保存结果文件
- 🎯 **界面优化**:
  - 新增API配置选择器
  - 动态列选择器，根据API配置自动调整
  - 自定义文件名输入框
- 📁 **文件管理**:
  - 结果文件自动保存到output目录
  - 支持时间序列命名和自定义命名


## 支持

如果您遇到任何问题或有建议，请：

1. 查看 [文档](https://github.com/zzti-bsj/batch-data-test-tool#readme)
2. 搜索 [已知问题](https://github.com/zzti-bsj/batch-data-test-tool/issues)
3. 创建新的 [Issue](https://github.com/zzti-bsj/batch-data-test-tool/issues/new)
