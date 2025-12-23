# test_finhub.py
import sys
import os
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)
"""测试Finhub API调用功能"""
from tradingagents.dataflows.interface import route_to_vendor  
from tradingagents.dataflows.config import set_config

# 1. 配置真实密钥（替换为你的Finhub密钥）
CUSTOM_CONFIG = {
    "FINHUB_API_KEY": "d53sdf1r01qkplh15q4gd53sdf1r01qkplh15q50",  # 替换为真实密钥
    "data_vendors": {"core_stock_apis": "finhub,yfinance"}
}
set_config(CUSTOM_CONFIG)

# 2. 测试用例
def test_finhub_realtime_data():
    """测试实时数据获取"""
    try:
        # 调用get_stock_data方法（自动优先用Finhub）
        data = route_to_vendor("get_stock_data", "AAPL")
        print("\n=== Finhub实时数据测试 ===")
        print(f"股票代码：{data['stock_code']}")
        print(f"当前价格：${data['current_price']}")
        print(f"当日涨跌幅：{data['change_percent']}%")
        print(f"当日高低：${data['low_price']} - ${data['high_price']}")
        return data
    except Exception as e:
        print(f"❌ 实时数据测试失败：{str(e)}")
        return None

def test_finhub_ohlc_data():
    """测试K线数据获取"""
    try:
        # 调用get_ohlc_data方法（获取AAPL近30天日线数据）
        data = route_to_vendor("get_ohlc_data", "AAPL", resolution="1D", count=30)
        print("\n=== Finhub K线数据测试 ===")
        print(f"股票代码：{data['stock_code']}")
        print(f"K线周期：{data['resolution']}")
        print(f"K线数量：{len(data['c'])}根")
        print(f"最新收盘价：${data['c'][-1]}")
        return data
    except Exception as e:
        print(f"❌ K线数据测试失败：{str(e)}")
        return None

if __name__ == "__main__":
    # 执行测试
    test_finhub_realtime_data()
    test_finhub_ohlc_data()
