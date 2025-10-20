import json
import re
from functools import lru_cache
from typing import Any, List, Union, Optional

# 可选引入 jmespath，提供更健壮的 JSON 查询能力
try:
    import jmespath  # type: ignore
    _JMESPATH_AVAILABLE = True
except Exception:  # jmespath 未安装时回退到内置解析
    jmespath = None  # type: ignore
    _JMESPATH_AVAILABLE = False

# 负索引检测，用于决定是否交给 jmespath 处理
_NEGATIVE_INDEX_RE = re.compile(r"\[-\d+\]")


def _contains_negative_index(path: str) -> bool:
    return bool(_NEGATIVE_INDEX_RE.search(path))


@lru_cache(maxsize=256)
def _compile_jmespath(expression: str):
    # 仅在 jmespath 可用时调用
    return jmespath.compile(expression)  # type: ignore


def get_json_field_value(json_data: Any, field_path: str) -> Any:
    """
    通过嵌套路径获取JSON指定字段值，支持任意复杂的JSON格式
    
    Args:
        json_data: JSON数据（dict、list、str或已解析的数据）
        field_path: 字段路径，支持多种格式：
            - 对象字段: "user.name"
            - 数组索引: "items[0]"
            - 混合路径: "data.items[0].content"
            - 负数索引: "items[-1]"（从后往前）
            - 范围选择: "items[0:3]"（返回子列表）
            - 通配符: "items[*].name"（返回列表）
            - 深度通配符: "**.name"（搜索所有层级）
            - JSON字符串解析: 自动检测并解析JSON字符串字段
    
    Returns:
        指定路径的值，如果路径不存在返回None
        对于通配符查询，返回列表；对于范围查询，返回切片
    """
    if json_data is None or not field_path:
        return None
    
    try:
        # 如果传入的是字符串，尝试解析为JSON
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        
        # 处理深度通配符
        if '**' in field_path:
            return _deep_search(json_data, field_path.replace('**.', ''))
        
        # 优先使用 jmespath（若可用），对常见路径/通配/切片具备更强表达力
        # 注意：jmespath 不支持负索引，且不支持 "**" 深度通配，因此这些场景回退到旧逻辑
        if _JMESPATH_AVAILABLE and not _contains_negative_index(field_path):
            try:
                result = _compile_jmespath(field_path).search(json_data)  # type: ignore
                if result is not None:
                    return result
            except Exception:
                # 表达式不被 jmespath 支持或运行时异常时，回退到旧逻辑
                pass

        # 处理通配符路径
        if '*' in field_path:
            return _wildcard_search(json_data, field_path)
        
        current_data = json_data
        
        # 使用正则表达式分割路径，正确处理各种复杂情况
        # 匹配模式：字段名、数组索引[0]、范围[0:3]、负数索引[-1]
        pattern = r'([^\.\[\]]+|\[\d+\]|\[-\d+\]|\[\d+:\d+\])'
        parts = re.findall(pattern, field_path)
        
        for part in parts:
            if part.startswith('[') and part.endswith(']'):
                # 处理数组相关操作
                index_expr = part[1:-1]
                
                # 处理范围选择 [0:3]
                if ':' in index_expr:
                    if not isinstance(current_data, list):
                        return None
                    try:
                        start, end = map(int, index_expr.split(':'))
                        current_data = current_data[start:end]
                    except (ValueError, IndexError):
                        return None
                
                # 处理负数索引 [-1]
                elif index_expr.startswith('-'):
                    if not isinstance(current_data, list):
                        return None
                    try:
                        index = int(index_expr)
                        if abs(index) <= len(current_data):
                            current_data = current_data[index]
                        else:
                            return None
                    except (ValueError, IndexError):
                        return None
                
                # 处理普通索引 [0]
                else:
                    try:
                        index = int(index_expr)
                        if isinstance(current_data, list) and 0 <= index < len(current_data):
                            current_data = current_data[index]
                        else:
                            return None
                    except (ValueError, IndexError):
                        return None
            else:
                # 处理对象字段
                if isinstance(current_data, dict) and part in current_data:
                    current_data = current_data[part]
                else:
                    return None
        
        return current_data
        
    except (json.JSONDecodeError, Exception):
        return None


def get_all_json_keys(json_data: Any, parent_path: str = "", max_depth: int = 100) -> List[str]:
    """
    获取JSON中所有嵌套的key路径，支持任意复杂的JSON格式
    
    Args:
        json_data: JSON数据（dict、list、str或已解析的数据）
        parent_path: 父级路径（用于递归）
        max_depth: 最大递归深度，防止栈溢出
    
    Returns:
        list: 所有key的完整路径列表
    """
    if max_depth <= 0:
        return []
    
    keys = []
    
    try:
        # 如果传入的是字符串，尝试解析为JSON（仅限根级别）
        if isinstance(json_data, str) and not parent_path:
            json_data = json.loads(json_data)
        
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                # 处理特殊字符的key
                safe_key = str(key).replace('.', '\\.')
                current_path = f"{parent_path}.{safe_key}" if parent_path else safe_key
                keys.append(current_path)
                
                # 递归处理嵌套结构
                nested_keys = get_all_json_keys(value, current_path, max_depth - 1)
                keys.extend(nested_keys)
                
        elif isinstance(json_data, list):
            for i, item in enumerate(json_data):
                current_path = f"{parent_path}[{i}]" if parent_path else f"[{i}]"
                keys.append(current_path)
                
                # 递归处理嵌套结构
                nested_keys = get_all_json_keys(item, current_path, max_depth - 1)
                keys.extend(nested_keys)
        
        # 处理其他可迭代类型（如元组、集合等）
        elif isinstance(json_data, (tuple, set)):
            for i, item in enumerate(json_data):
                current_path = f"{parent_path}[{i}]" if parent_path else f"[{i}]"
                keys.append(current_path)
                
                # 递归处理嵌套结构
                nested_keys = get_all_json_keys(item, current_path, max_depth - 1)
                keys.extend(nested_keys)
    
    except (json.JSONDecodeError, Exception):
        pass
    
    return keys


def _wildcard_search(data: Any, pattern: str) -> List[Any]:
    """处理通配符搜索"""
    results = []
    
    def _search_recursive(current_data: Any, current_pattern: str, current_path: str = ""):
        if not current_pattern:
            results.append(current_data)
            return
        
        # 获取下一个路径段
        next_star = current_pattern.find('*')
        if next_star == -1:
            # 没有通配符，直接查找
            value = get_json_field_value(current_data, current_pattern)
            if value is not None:
                results.append(value)
            return
        
        # 获取通配符前的部分
        before_star = current_pattern[:next_star].rstrip('.')
        
        if before_star:
            current_data = get_json_field_value(current_data, before_star)
            if current_data is None:
                return
        
        # 处理通配符匹配
        remaining_pattern = current_pattern[next_star + 1:].lstrip('.')
        
        if isinstance(current_data, dict):
            for key, value in current_data.items():
                _search_recursive(value, remaining_pattern, f"{current_path}.{key}")
        elif isinstance(current_data, list):
            for i, item in enumerate(current_data):
                _search_recursive(item, remaining_pattern, f"{current_path}[{i}]")
    
    _search_recursive(data, pattern)
    return results


def _deep_search(data: Any, field_name: str) -> List[Any]:
    """深度搜索指定字段名"""
    results = []
    
    def _search_recursive(current_data: Any, path: str = ""):
        if isinstance(current_data, dict):
            # 检查当前层级是否有目标字段
            if field_name in current_data:
                results.append(current_data[field_name])
            
            # 继续递归搜索
            for value in current_data.values():
                _search_recursive(value, f"{path}.{value}")
                
        elif isinstance(current_data, list):
            for item in current_data:
                _search_recursive(item, f"{path}[{item}]")
    
    _search_recursive(data)
    return results