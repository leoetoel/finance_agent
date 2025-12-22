# tradingagents/dataflows/config.py
"""配置读取工具：全局唯一配置，支持动态覆盖"""
from typing import Dict, Any

try:
    # Support running as an installed package.
    from tradingagents.default_config import DEFAULT_CONFIG
except ModuleNotFoundError:
    # Support running from repo root (e.g., python test_finhub.py).
    from default_config import DEFAULT_CONFIG

# 全局配置存储（私有变量）
_CONFIG: Dict[str, Any] = DEFAULT_CONFIG.copy()

def set_config(custom_config: Dict[str, Any]) -> None:
    """
    覆盖默认配置
    :param custom_config: 自定义配置字典
    """
    global _CONFIG
    _CONFIG.update(custom_config)
    print(f"✅ 配置已更新，当前核心配置：{_CONFIG['data_vendors']}")

def get_config() -> Dict[str, Any]:
    """
    获取当前配置（返回副本，避免外部修改）
    :return: 配置字典
    """
    return _CONFIG.copy()
