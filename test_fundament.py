import sys
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# 路径配置
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.append(str(PROJECT_ROOT))

# 导入核心模块
from tradingagents.dataflows.config import set_config, get_config
from tradingagents.agents.analysts.fundament_analyst import (
    get_fundamental_analysis, calculate_fundamental_indicators
)

# 前置配置
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
BASE_CONFIG = {
    "FINHUB_API_KEY": os.getenv("FINHUB_API_KEY", ""),
    "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "deepseek_base_url": "https://api.deepseek.com/v1",
    "data_vendors": {"core_stock_apis": "finhub,yfinance"},
    "llm_model": "deepseek-chat",
    "llm_temperature": 0.1
}
set_config(BASE_CONFIG)

# 基础功能测试
def test_basic_fundamental_analysis():
    test_codes = ["AAPL", "MSFT"]
    for stock_code in test_codes:
        print(f"\n=== 测试股票代码：{stock_code} ===")
        try:
            result = get_fundamental_analysis(stock_code)
            
            # 核心断言
            assert result["stock_code"] == stock_code
            assert result["source"] in ["finhub", "yfinance"]
            assert "market_data" in result
            assert "financial_data" in result
            assert "fundamental_indicators" in result
            assert "llm_analysis_report" in result
            assert len(result["llm_analysis_report"]) > 200

            # 打印结果
            print(f"✅ {stock_code} 基本面分析通过")
            print(f"📊 数据源：{result['source']} | 市值：{result['market_data']['market_cap']/1e9:.2f}亿")
            print(f"📝 报告预览：{result['llm_analysis_report'][:100]}...")
            print("\n[Full Report]\n" + result["llm_analysis_report"] + "\n")
        except Exception as e:
            pytest.fail(f"{stock_code} 分析失败：{str(e)}")

# 指标计算测试
def test_fundamental_indicators_calculation():
    # 构造测试数据
    financial_data = {
        "total_revenue": 380000000000,
        "net_profit": 99800000000,
        "revenue_growth_yoy": 12.5,
        "profit_growth_yoy": 8.3,
        "roe": 18.2,
        "debt_to_equity": 55.0
    }
    market_data = {
        "market_cap": 2900000000000,
        "pe_ratio": 29.5
    }

    # 计算指标
    indicators = calculate_fundamental_indicators(financial_data, market_data)
    
    # 断言趋势判断
    assert indicators["trends"]["revenue_growth"] == "稳健增长（5%-20%）"
    assert indicators["trends"]["roe"] == "优秀（>15%，盈利能力强）"
    assert indicators["trends"]["pe_ratio"] == "合理（15-30倍）"
    assert indicators["trends"]["debt_to_equity"] == "合理负债（40%-60%）"
    print("✅ 基本面指标计算测试通过")

# 异常场景测试
def test_invalid_stock_code():
    invalid_code = "INVALID_12345"
    try:
        get_fundamental_analysis(invalid_code)
        pytest.fail("无效代码未抛出异常")
    except Exception as e:
        assert any(key in str(e) for key in ["404", "Not Found", "数据获取失败"]), f"异常信息不符：{str(e)}"
        print("✅ 无效代码测试通过")

# 主函数
if __name__ == "__main__":
    print("========== 开始执行基本面分析师测试 ==========\n")
    try:
        test_fundamental_indicators_calculation()
    except Exception as e:
        print(f"❌ 指标测试失败：{e}")
    
    print("\n" + "-"*50)
    try:
        test_basic_fundamental_analysis()
    except Exception as e:
        print(f"❌ 基础分析测试失败：{e}")
    
    print("\n" + "-"*50)
    try:
        test_invalid_stock_code()
    except Exception as e:
        print(f"❌ 无效代码测试失败：{e}")
    
    print("\n========== 所有测试执行完成 ==========")
