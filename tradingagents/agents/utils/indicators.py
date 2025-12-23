# tradingagents/agents/utils/indicators.py
import numpy as np
import pandas as pd
from typing import List, Dict, Any

def calculate_rsi(prices: List[float], window: int = 14) -> List[float]:
    """
    计算RSI（相对强弱指数）
    :param prices: 收盘价列表
    :param window: 计算窗口（默认14）
    :return: RSI值列表（长度和输入一致，前window个值为NaN）
    """
    if len(prices) < window:
        return [np.nan] * len(prices)
    
    prices_series = pd.Series(prices)
    delta = prices_series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.tolist()

def calculate_macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, List[float]]:
    """
    计算MACD（指数平滑异同移动平均线）
    :param prices: 收盘价列表
    :return: 包含macd、signal、hist的字典
    """
    if len(prices) < slow_period:
        return {
            "macd": [np.nan] * len(prices),
            "signal": [np.nan] * len(prices),
            "hist": [np.nan] * len(prices)
        }
    
    prices_series = pd.Series(prices)
    ema_fast = prices_series.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices_series.ewm(span=slow_period, adjust=False).mean()
    
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    hist = macd - signal
    
    return {
        "macd": macd.tolist(),
        "signal": signal.tolist(),
        "hist": hist.tolist()
    }

def calculate_bollinger_bands(prices: List[float], window: int = 20, num_std: float = 2) -> Dict[str, List[float]]:
    """
    计算布林带
    :param prices: 收盘价列表
    :return: 包含中轨、上轨、下轨的字典
    """
    if len(prices) < window:
        return {
            "middle": [np.nan] * len(prices),
            "upper": [np.nan] * len(prices),
            "lower": [np.nan] * len(prices)
        }
    
    prices_series = pd.Series(prices)
    middle_band = prices_series.rolling(window=window).mean()
    std = prices_series.rolling(window=window).std()
    
    upper_band = middle_band + (std * num_std)
    lower_band = middle_band - (std * num_std)
    
    return {
        "middle": middle_band.tolist(),
        "upper": upper_band.tolist(),
        "lower": lower_band.tolist()
    }

def calculate_technical_indicators(stock_data: Dict[str, Any], ohlc_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一计算所有技术指标（对外暴露的核心函数）
    :param stock_data: 实时股票数据（数据源模块输出）
    :param ohlc_data: K线数据（数据源模块输出）
    :return: 整合后的技术指标结果
    """
    # 提取收盘价列表（从K线数据）
    close_prices = ohlc_data.get("c", [])
    
    # 计算各指标
    rsi = calculate_rsi(close_prices)
    macd = calculate_macd(close_prices)
    bollinger = calculate_bollinger_bands(close_prices)
    
    # 整合结果（只保留最新值+趋势描述）
    latest_rsi = rsi[-1] if rsi and not np.isnan(rsi[-1]) else None
    latest_macd = macd["macd"][-1] if macd["macd"] and not np.isnan(macd["macd"][-1]) else None
    latest_macd_signal = macd["signal"][-1] if macd["signal"] and not np.isnan(macd["signal"][-1]) else None
    latest_bollinger_upper = bollinger["upper"][-1] if bollinger["upper"] and not np.isnan(bollinger["upper"][-1]) else None
    latest_bollinger_lower = bollinger["lower"][-1] if bollinger["lower"] and not np.isnan(bollinger["lower"][-1]) else None
    
    # 指标趋势判断
    rsi_trend = None
    if latest_rsi:
        if latest_rsi > 70:
            rsi_trend = "超买（Overbought），可能回调"
        elif latest_rsi < 30:
            rsi_trend = "超卖（Oversold），可能反弹"
        else:
            rsi_trend = "中性（Neutral）"
    
    macd_trend = None
    if latest_macd and latest_macd_signal:
        if latest_macd > latest_macd_signal:
            macd_trend = "MACD上穿信号线，多头信号"
        else:
            macd_trend = "MACD下穿信号线，空头信号"
    
    bollinger_trend = None
    current_price = stock_data.get("current_price")
    if current_price and latest_bollinger_upper and latest_bollinger_lower:
        if current_price >= latest_bollinger_upper:
            bollinger_trend = "价格触及上轨，可能承压回落"
        elif current_price <= latest_bollinger_lower:
            bollinger_trend = "价格触及下轨，可能获得支撑"
        else:
            bollinger_trend = "价格在布林带中间，趋势不明"
    
    return {
        "latest_values": {
            "rsi": latest_rsi,
            "macd": latest_macd,
            "macd_signal": latest_macd_signal,
            "bollinger_upper": latest_bollinger_upper,
            "bollinger_lower": latest_bollinger_lower,
            "current_price": current_price
        },
        "trends": {
            "rsi": rsi_trend,
            "macd": macd_trend,
            "bollinger": bollinger_trend
        },
        "raw_indicators": {
            "rsi": rsi,
            "macd": macd,
            "bollinger": bollinger
        }
    }