import re
import json
from typing import List

def get_api_url_name_list(config_file_path: str = 'config.json') -> List[str]:
    with open(config_file_path, 'r') as f:
        configs = json.load(f)
    return [config['api_name'] for config in configs]
    
def get_api_params_placeholder_list_by_name(config_file_path: str = 'config.json', api_name: str = 'test_api_name') -> List[str]:
    # 匹配配置文件中${conversation_text}
    """
    目前先实现单列数据作为请求参数
    """
    placeholder_list = []
    with open(config_file_path, 'r') as f:
        configs = json.load(f)
    # 根据api_name获取配置
    for config in configs:
        if config['api_name'] == api_name:
            params = config['params']
            for key, value in params.items():
                # 提取匹配到的值
                match = re.match(r'\${.*?}', str(value))
                if match:
                    # 不要外面的美元符号和括号
                    placeholder_list.append(match.group(0).replace('${', '').replace('}', ''))
            break
    return placeholder_list

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