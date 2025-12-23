"""
技术分析师Agent测试文件
覆盖场景：
1. 基础功能测试（正常股票代码、完整流程）
2. 异常场景测试（无效代码、API失败、密钥缺失）
3. 结果合理性测试（指标与分析报告一致性）
"""
import os
import pytest
import numpy as np
from dotenv import load_dotenv

# 导入核心模块
from tradingagents.dataflows.config import set_config, get_config
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.agents.tech_analyst import get_technical_analysis
from tradingagents.agents.utils.indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands
)

# ===================== 前置配置 =====================
# 加载.env文件（优先从环境变量读密钥）
load_dotenv()

# 基础配置（可根据需要调整）
BASE_CONFIG = {
    "FINHUB_API_KEY": os.getenv("FINHUB_API_KEY", ""),
    "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "data_vendors": {"core_stock_apis": "finhub,yfinance"},
    "llm_model": "deepseek-chat",
    "llm_temperature": 0.1
}
# 应用基础配置
set_config(BASE_CONFIG)

# ===================== 基础功能测试 =====================
def test_basic_technical_analysis():
    """测试正常股票代码的完整分析流程"""
    # 测试标的（覆盖美股常见代码）
    test_codes = ["AAPL", "MSFT"]
    
    for stock_code in test_codes:
        print(f"\n=== 测试股票代码：{stock_code} ===")
        try:
            # 调用技术分析师Agent
            result = get_technical_analysis(stock_code)
            
            # 核心验证点
            assert result["stock_code"] == stock_code, "股票代码匹配失败"
            assert result["source"] in ["finhub", "yfinance"], "数据源异常"
            assert "basic_data" in result, "缺失基础数据"
            assert "technical_indicators" in result, "缺失技术指标"
            assert "analysis_report" in result, "缺失分析报告"
            
            # 验证基础数据完整性
            basic_data = result["basic_data"]
            required_basic_fields = ["current_price", "open_price", "high_price", "low_price", "change_percent"]
            for field in required_basic_fields:
                assert field in basic_data, f"基础数据缺失字段：{field}"
                assert basic_data[field] is not None, f"基础数据字段{field}为空"
            
            # 验证技术指标完整性
            indicators = result["technical_indicators"]
            assert "latest_values" in indicators, "缺失指标最新值"
            assert "trends" in indicators, "缺失指标趋势"
            
            # 验证分析报告非空且符合要求
            report = result["analysis_report"]
            assert len(report) > 100, "分析报告过短（可能生成失败）"
            assert any(keyword in report for keyword in ["趋势判断", "支撑位", "压力位", "交易信号"]), "分析报告格式异常"
            
            # 打印成功信息
            print(f"✅ {stock_code} 基础功能测试通过")
            print(f"📊 数据源：{result['source']} | 当前价格：${basic_data['current_price']}")
            print(f"📝 分析报告预览：{report[:100]}...")
            
        except Exception as e:
            pytest.fail(f"{stock_code} 基础功能测试失败：{str(e)}")

# ===================== 异常场景测试 =====================
def test_invalid_stock_code():
    """测试无效股票代码"""
    invalid_code = "INVALID_12345"
    try:
        # 预期会抛出异常
        get_technical_analysis(invalid_code)
        pytest.fail("无效股票代码未抛出异常")
    except RuntimeError as e:
        # 验证异常信息包含关键描述
        assert any(keyword in str(e) for keyword in ["调用失败", "不存在", "无效"]), "异常信息不符合预期"
        print(f"✅ 无效股票代码测试通过，异常信息：{str(e)[:50]}...")
    except Exception as e:
        pytest.fail(f"无效股票代码测试抛出非预期异常：{str(e)}")

def test_finhub_fail_fallback_yfinance():
    """测试Finhub失败后降级到Yfinance"""
    # 临时覆盖配置：设置无效的Finhub密钥
    temp_config = BASE_CONFIG.copy()
    temp_config["FINHUB_API_KEY"] = "invalid_key_123456"
    set_config(temp_config)
    
    try:
        result = get_technical_analysis("AAPL")
        # 验证是否降级到Yfinance
        assert result["source"] == "yfinance", "Finhub失败后未降级到Yfinance"
        print(f"✅ Finhub降级测试通过，当前数据源：{result['source']}")
    except Exception as e:
        pytest.fail(f"Finhub降级测试失败：{str(e)}")
    finally:
        # 恢复原配置
        set_config(BASE_CONFIG)

def test_missing_llm_api_key():
    """测试LLM密钥缺失"""
    # 临时覆盖配置：清空DeepSeek密钥
    temp_config = BASE_CONFIG.copy()
    temp_config["deepseek_api_key"] = ""
    set_config(temp_config)
    
    try:
        get_technical_analysis("AAPL")
        pytest.fail("LLM密钥缺失未抛出异常")
    except Exception as e:
        assert any(keyword in str(e).lower() for keyword in ["api key", "密钥", "invalid"]), "异常信息不符合预期"
        print(f"✅ LLM密钥缺失测试通过，异常信息：{str(e)[:50]}...")
    finally:
        # 恢复原配置
        set_config(BASE_CONFIG)

# ===================== 技术指标单元测试 =====================
def test_technical_indicators_calculation():
    """测试技术指标计算逻辑"""
    # 构造测试价格数据（15天连续上涨）
    prices = [100 + i*2 for i in range(15)]
    
    # 测试RSI计算
    rsi = calculate_rsi(prices)
    assert len(rsi) == 15, "RSI长度与输入价格不匹配"
    assert not np.isnan(rsi[-1]), "RSI最后一个值为NaN"
    assert rsi[-1] > 70, "上涨趋势RSI未达到超买区间"
    
    # 测试MACD计算
    macd_result = calculate_macd(prices)
    assert "macd" in macd_result and "signal" in macd_result and "hist" in macd_result, "MACD返回格式异常"
    assert not np.isnan(macd_result["macd"][-1]), "MACD最后一个值为NaN"
    
    # 测试布林带计算
    bollinger = calculate_bollinger_bands(prices)
    assert bollinger["upper"][-1] > bollinger["middle"][-1], "布林带上轨应大于中轨"
    assert bollinger["lower"][-1] < bollinger["middle"][-1], "布林带下轨应小于中轨"
    
    print("✅ 技术指标计算测试全部通过")

# ===================== 结果合理性测试 =====================
def test_analysis_report_reasonableness():
    """测试分析报告的合理性（基于构造的超买数据）"""
    # 构造RSI超买的模拟数据
    mock_stock_data = {
        "stock_code": "TEST",
        "current_price": 128,
        "open_price": 120,
        "high_price": 129,
        "low_price": 118,
        "volume": 1000000,
        "change_percent": 6.7,
        "source": "mock",
        "timestamp": 1735689600
    }
    mock_ohlc_data = {
        "c": [100 + i*2 for i in range(15)],  # 15天上涨价格
        "t": [1735689600 - i*86400 for i in range(15)],
        "o": [99 + i*2 for i in range(15)],
        "h": [101 + i*2 for i in range(15)],
        "l": [98 + i*2 for i in range(15)],
        "v": [1000000 for i in range(15)],
        "s": "ok"
    }
    
    # 计算技术指标
    from tradingagents.agents.utils.indicators import calculate_technical_indicators
    indicators = calculate_technical_indicators(mock_stock_data, mock_ohlc_data)
    
    # 验证RSI趋势判断
    assert indicators["trends"]["rsi"] == "超买（Overbought），可能回调", "RSI超买趋势判断错误"
    
    # 构造提示词并调用LLM
    prompt = f"""
    基于以下数据分析TEST股票：
    RSI（14日）：{indicators['latest_values']['rsi']} → {indicators['trends']['rsi']}
    要求：必须提到超买风险，交易信号建议持有或卖出
    """
    config = get_config()
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model=config["llm_model"],
        api_key=config["deepseek_api_key"],
        base_url="https://api.deepseek.com/v1",
        temperature=0.1
    )
    response = llm.invoke(prompt)
    report = response.content
    
    # 验证分析报告合理性
    assert "超买" in report or "Overbought" in report, "分析报告未提及超买风险"
    assert any(word in report for word in ["持有", "卖出", "Hold", "Sell"]), "分析报告未给出交易信号"
    print("✅ 分析报告合理性测试通过")

# ===================== 主函数（执行所有测试） =====================
if __name__ == "__main__":
    # 执行顺序：先单元测试，再功能测试，最后异常测试
    print("========== 开始执行技术分析师Agent测试 ==========\n")
    
    # 1. 技术指标单元测试
    try:
        test_technical_indicators_calculation()
    except Exception as e:
        print(f"❌ 技术指标测试失败：{e}")
    
    # 2. 基础功能测试
    print("\n" + "-"*50)
    try:
        test_basic_technical_analysis()
    except Exception as e:
        print(f"❌ 基础功能测试失败：{e}")
    
    # 3. 异常场景测试
    print("\n" + "-"*50)
    try:
        test_invalid_stock_code()
    except Exception as e:
        print(f"❌ 无效代码测试失败：{e}")
    
    try:
        test_finhub_fail_fallback_yfinance()
    except Exception as e:
        print(f"❌ Finhub降级测试失败：{e}")
    
    try:
        test_missing_llm_api_key()
    except Exception as e:
        print(f"❌ LLM密钥缺失测试失败：{e}")
    
    # 4. 结果合理性测试
    print("\n" + "-"*50)
    try:
        test_analysis_report_reasonableness()
    except Exception as e:
        print(f"❌ 分析报告合理性测试失败：{e}")
    
    print("\n========== 所有测试执行完成 ==========")