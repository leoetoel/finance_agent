# tradingagents/dataflows/finhub.py
"""Finhub API封装：实现实时数据、K线数据等接口"""
import requests
from typing import Dict, Any, Optional
from .config import get_config

# 初始化配置
CONFIG = get_config()
FINHUB_API_KEY = CONFIG.get("FINHUB_API_KEY")
FINHUB_BASE_URL = "https://finnhub.io/api/v1"
REQUEST_TIMEOUT = CONFIG.get("timeout", 10)

# 前置校验：API密钥是否配置
if not FINHUB_API_KEY:
    raise EnvironmentError(
        "Finhub API密钥未配置！请通过set_config设置或在default_config.py中填写\n"
        "获取密钥地址：https://finnhub.io/dashboard"
    )

def get_finhub_realtime_data(stock_code: str, **kwargs) -> Dict[str, Any]:
    """
    调用Finhub API获取股票实时报价
    接口文档：https://finnhub.io/docs/api/quote
    :param stock_code: 股票代码（如AAPL、MSFT，需符合Finhub格式）
    :return: 格式化后的实时数据字典
    """
    # 构造请求参数
    params = {
        "symbol": stock_code,
        "token": FINHUB_API_KEY
    }
    
    try:
        # 发送请求
        response = requests.get(
            url=f"{FINHUB_BASE_URL}/quote",
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "TradingAgents/1.0"}
        )
        # 抛出HTTP错误（4xx/5xx）
        response.raise_for_status()
        raw_data = response.json()

        # 统一数据格式（和yfinance输出对齐，方便上层兼容）
        formatted_data = {
            "stock_code": stock_code,
            "current_price": raw_data.get("c"),  # 当前价格
            "open_price": raw_data.get("o"),     # 当日开盘价
            "high_price": raw_data.get("h"),     # 当日最高价
            "low_price": raw_data.get("l"),      # 当日最低价
            "prev_close": raw_data.get("pc"),    # 昨日收盘价
            "change": raw_data.get("d"),         # 价格变动
            "change_percent": raw_data.get("dp"),# 涨跌幅（%）
            "volume": raw_data.get("v"),         # 成交量
            "timestamp": raw_data.get("t"),      # 数据时间戳
            "source": "finhub",                  # 数据源标记
            "raw_data": raw_data                 # 保留原始数据（备用）
        }
        return formatted_data

    # 针对性异常处理
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise RuntimeError("Finhub API密钥无效！请检查密钥是否正确") from e
        elif response.status_code == 429:
            raise RuntimeError("Finhub API调用超限！请等待1分钟后重试") from e
        elif response.status_code == 404:
            raise RuntimeError(f"股票代码{stock_code}不存在！请检查代码格式") from e
        else:
            raise RuntimeError(f"Finhub HTTP错误：{e} 状态码：{response.status_code}") from e
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Finhub请求超时（{REQUEST_TIMEOUT}秒）：{stock_code}")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Finhub网络连接失败！请检查网络或Finhub服务状态")
    except Exception as e:
        raise RuntimeError(f"Finhub调用未知错误：{str(e)}") from e

def get_finhub_ohlc_data(
    stock_code: str,
    resolution: str = "1D",
    count: int = 30,
    start: Optional[int] = None,
    end: Optional[int] = None
) -> Dict[str, Any]:
    """
    调用Finhub API获取K线数据
    接口文档：https://finnhub.io/docs/api/stock-candles
    :param stock_code: 股票代码
    :param resolution: K线周期（1, 5, 15, 30, 60, D, W, M）
    :param count: K线数量（默认30根）
    :param start: 开始时间戳（秒）
    :param end: 结束时间戳（秒）
    :return: 格式化后的K线数据
    """
    params = {
        "symbol": stock_code,
        "resolution": resolution,
        "count": count,
        "token": FINHUB_API_KEY
    }
    # 可选时间范围（二选一：count 或 start+end）
    if start and end:
        params.pop("count")
        params["from"] = start
        params["to"] = end

    try:
        response = requests.get(
            url=f"{FINHUB_BASE_URL}/stock/candle",
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "TradingAgents/1.0"}
        )
        response.raise_for_status()
        raw_data = response.json()

        # 格式化K线数据
        formatted_data = {
            "stock_code": stock_code,
            "resolution": resolution,
            "t": raw_data.get("t"),  # 时间戳列表
            "o": raw_data.get("o"),  # 开盘价列表
            "h": raw_data.get("h"),  # 最高价列表
            "l": raw_data.get("l"),  # 最低价列表
            "c": raw_data.get("c"),  # 收盘价列表
            "v": raw_data.get("v"),  # 成交量列表
            "s": raw_data.get("s"),  # 状态（ok/no_data）
            "source": "finhub",
            "raw_data": raw_data
        }
        return formatted_data

    except Exception as e:
        raise RuntimeError(f"Finhub K线数据获取失败：{str(e)}") from e