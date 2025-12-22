# tradingagents/dataflows/interface.py
"""数据源路由核心：统一调用入口+自动失败降级"""
from typing import List, Callable, Any, Dict
from .config import get_config

# 导入各数据源实现（按需扩展）
from .finhub import get_finhub_realtime_data, get_finhub_ohlc_data
from .y_finance import get_yfinance_ohlc_data
# 以下为兼容原有框架的示例（若不需要yfinance/AlphaVantage可注释）
# from .y_finance import get_yfinance_stock_data, get_yfinance_ohlc_data
# from .alpha_vantage import get_alpha_vantage_stock_data, get_alpha_vantage_ohlc_data

# 核心映射表：{统一方法名: {数据源名: 实现函数}}
VENDOR_METHODS: Dict[str, Dict[str, Callable]] = {
    # 实时股票数据（核心方法）
    "get_stock_data": {
        "finhub": get_finhub_realtime_data,
        # "yfinance": get_yfinance_stock_data,
        # "alpha_vantage": get_alpha_vantage_stock_data
    },
    # K线数据
    "get_ohlc_data": {
        "finhub": get_finhub_ohlc_data,
        "yfinance": get_yfinance_ohlc_data,
        # "alpha_vantage": get_alpha_vantage_ohlc_data
    }
}

# 数据源分类映射（用于优先级配置）
TOOL_CATEGORIES = {
    "core_stock_apis": ["get_stock_data"],
    "technical_indicators": ["get_ohlc_data"]
}

def get_category_for_method(method_name: str) -> str:
    """
    根据方法名获取所属分类
    :param method_name: 统一方法名（如get_stock_data）
    :return: 分类名（如core_stock_apis）
    """
    for category, methods in TOOL_CATEGORIES.items():
        if method_name in methods:
            return category
    raise ValueError(f"方法{method_name}未配置分类！请检查TOOL_CATEGORIES")

def get_vendor_priority(method_name: str) -> List[str]:
    """
    获取方法的数据源优先级列表
    优先级：方法级配置 > 分类级配置 > 默认配置
    :param method_name: 统一方法名
    :return: 按优先级排序的数据源列表
    """
    config = get_config()
    # 1. 优先读取方法级配置
    tool_vendors = config.get("tool_vendors", {})
    if method_name in tool_vendors:
        return [v.strip() for v in tool_vendors[method_name].split(",")]
    # 2. 读取分类级配置
    category = get_category_for_method(method_name)
    data_vendors = config.get("data_vendors", {})
    if category in data_vendors:
        return [v.strip() for v in data_vendors[category].split(",")]
    # 3. 默认优先级
    return ["finhub", "yfinance", "alpha_vantage"]

def route_to_vendor(method_name: str, *args, **kwargs) -> Any:
    """
    统一数据源调用入口
    :param method_name: 统一方法名（如get_stock_data）
    :param args: 传递给实现函数的位置参数
    :param kwargs: 传递给实现函数的关键字参数
    :return: 第一个成功的数据源返回结果
    :raises RuntimeError: 所有数据源调用失败时抛出
    """
    # 校验方法是否支持
    if method_name not in VENDOR_METHODS:
        raise ValueError(
            f"不支持的方法：{method_name}！支持的方法列表：{list(VENDOR_METHODS.keys())}"
        )
    
    # 获取优先级和可用数据源
    vendor_priority = get_vendor_priority(method_name)
    method_vendors = VENDOR_METHODS[method_name]
    last_exception = None

    # 按优先级遍历数据源
    for vendor in vendor_priority:
        # 跳过不支持该方法的数据源
        if vendor not in method_vendors:
            print(f"ℹ️ 数据源{vendor}不支持方法{method_name}，跳过")
            continue
        
        try:
            # 调用具体数据源实现
            print(f"🔍 尝试调用{vendor}的{method_name}方法...")
            result = method_vendors[vendor](*args, **kwargs)
            print(f"✅ 成功获取{vendor}数据！")
            return result
        
        except Exception as e:
            last_exception = e
            print(f"❌ {vendor}调用失败：{str(e)}，尝试下一个数据源")
    
    # 所有数据源失败
    raise RuntimeError(
        f"所有数据源调用{method_name}失败！最后错误：{str(last_exception)}"
    ) from last_exception
