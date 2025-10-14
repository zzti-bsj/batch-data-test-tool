import re
import json
from typing import List

def get_api_url_name_list(config_file_path: str = 'config.json') -> List[str]:
    with open(config_file_path, 'r') as f:
        configs = json.load(f)
    return [config['api_name'] for config in configs]
    
def get_api_params_placeholder_list_by_name(config_file_path: str = 'config.json', api_name: str = 'test_api_name') -> List[str]:
    """
    递归解析嵌套参数结构中的占位符
    支持多层嵌套的字典和列表结构
    """
    placeholder_list = []
    
    def extract_placeholders_recursive(data, path=""):
        """递归提取占位符"""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                extract_placeholders_recursive(value, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                extract_placeholders_recursive(item, current_path)
        elif isinstance(data, str):
            # 查找字符串中的所有占位符
            matches = re.findall(r'\${([^}]+)}', data)
            for match in matches:
                placeholder_list.append(match)
    
    with open(config_file_path, 'r') as f:
        configs = json.load(f)
    
    # 根据api_name获取配置
    for config in configs:
        if config['api_name'] == api_name:
            params = config['params']
            extract_placeholders_recursive(params)
            break
    
    # 去重并保持顺序
    seen = set()
    unique_placeholders = []
    for placeholder in placeholder_list:
        if placeholder not in seen:
            seen.add(placeholder)
            unique_placeholders.append(placeholder)
    
    return unique_placeholders

def get_api_url_by_name(config_file_path: str = 'config.json', api_name: str = 'test_api_name') -> str:
    with open(config_file_path, 'r') as f:
        configs = json.load(f)
    for config in configs:
        if config['api_name'] == api_name:
            return config['api_url']
    return None

def get_api_params_by_name(config_file_path: str = 'config.json', api_name: str = 'test_api_name') -> dict:
    with open(config_file_path, 'r') as f:
        configs = json.load(f)
    for config in configs:
        if config['api_name'] == api_name:
            return config['params']
    return None

def get_api_headers_by_name(config_file_path: str = 'config.json', api_name: str = 'test_api_name') -> dict:
    with open(config_file_path, 'r') as f:
        configs = json.load(f)
    for config in configs:
        if config['api_name'] == api_name:
            return config['headers']
    return None