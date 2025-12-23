import sys
from pathlib import Path
from typing import Dict, Any
import numpy as np

# 修复路径（复用原有逻辑）
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

# 导入核心依赖（仅保留必要的，移除common）
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.dataflows.config import get_config

# 初始化LLM（直接初始化，不封装）
try:
    from langchain_openai import ChatOpenAI
    config = get_config()
    llm = ChatOpenAI(
        model=config.get("llm_model", "deepseek-chat"),
        api_key=config.get("deepseek_api_key"),
        base_url=config.get("deepseek_base_url", "https://api.deepseek.com/v1"),
        temperature=0.1
    )
except Exception as e:
    raise Exception(f"LLM初始化失败：{str(e)}")

def calculate_fundamental_indicators(financial_data: Dict, market_data: Dict) -> Dict:
    """
    计算核心基本面指标（移除common异常，直接抛普通Exception）
    """
    indicators = {
        "latest_values": {},
        "trends": {}
    }

    # 1. 提取核心数据（空值容错）
    revenue = financial_data.get("total_revenue", 0)
    net_profit = financial_data.get("net_profit", 0)
    revenue_growth = financial_data.get("revenue_growth_yoy", 0)
    profit_growth = financial_data.get("profit_growth_yoy", 0)
    roe = financial_data.get("roe", 0)
    debt_to_equity = financial_data.get("debt_to_equity", 0)
    pe_ratio = market_data.get("pe_ratio", 0)

    # 2. 填充指标值
    indicators["latest_values"] = {
        "revenue": revenue,
        "net_profit": net_profit,
        "revenue_growth": revenue_growth,
        "profit_growth": profit_growth,
        "roe": roe,
        "pe_ratio": pe_ratio,
        "debt_to_equity": debt_to_equity
    }

    # 3. 趋势判断
    # 营收增长
    if revenue_growth > 20:
        indicators["trends"]["revenue_growth"] = "高速增长（>20%）"
    elif 5 <= revenue_growth <= 20:
        indicators["trends"]["revenue_growth"] = "稳健增长（5%-20%）"
    elif -5 <= revenue_growth < 5:
        indicators["trends"]["revenue_growth"] = "增长停滞（-5%-5%）"
    else:
        indicators["trends"]["revenue_growth"] = "负增长（<-5%）"

    # ROE
    if roe > 15:
        indicators["trends"]["roe"] = "优秀（>15%，盈利能力强）"
    elif 8 <= roe <= 15:
        indicators["trends"]["roe"] = "良好（8%-15%，盈利能力中等）"
    else:
        indicators["trends"]["roe"] = "较差（<8%，盈利能力弱）"

    # PE估值
    if pe_ratio < 15:
        indicators["trends"]["pe_ratio"] = "低估（<15倍）"
    elif 15 <= pe_ratio <= 30:
        indicators["trends"]["pe_ratio"] = "合理（15-30倍）"
    else:
        indicators["trends"]["pe_ratio"] = "高估（>30倍）"

    return indicators

def get_fundamental_analysis(stock_code: str) -> Dict[str, Any]:
    """
    基本面分析师核心函数（无common依赖）
    """
    print(f"📊 开始分析{stock_code}基本面...")

    # 1. 获取基础数据
    try:
        market_data = route_to_vendor("get_market_data", stock_code)
        financial_data = route_to_vendor("get_financial_data", stock_code)
    except Exception as e:
        raise Exception(f"基本面数据获取失败：{str(e)}")

    # 2. 计算指标
    print(f"📈 计算{stock_code}基本面指标...")
    fundamental_indicators = calculate_fundamental_indicators(financial_data, market_data)

    # 3. 构造LLM提示词
    prompt = f"""
    你是资深金融基本面分析师，基于以下数据撰写{stock_code}的基本面分析报告：
    
    ### 基础市场数据
    - 当前股价：{market_data['current_price']} USD
    - 总市值：{market_data['market_cap']/1e9:.2f} 亿美元
    - 市盈率（PE）：{fundamental_indicators['latest_values']['pe_ratio']}

    ### 核心财务数据
    - 总营收：{financial_data['total_revenue']/1e9:.2f} 亿美元
    - 净利润：{financial_data['net_profit']/1e9:.2f} 亿美元
    - 营收同比增长率：{financial_data['revenue_growth_yoy']}%
    - 净资产收益率（ROE）：{financial_data['roe']}%
    - 资产负债率：{financial_data['debt_to_equity']}%

    ### 指标趋势
    - 营收增长：{fundamental_indicators['trends']['revenue_growth']}
    - ROE水平：{fundamental_indicators['trends']['roe']}
    - PE估值：{fundamental_indicators['trends']['pe_ratio']}

    ### 输出要求
    1. 业绩分析：营收/利润增长的核心驱动因素；
    2. 估值判断：当前PE是否合理（对比行业均值）；
    3. 风险提示：潜在风险点；
    4. 投资评级：买入/持有/卖出（理由清晰）；
    5. 格式：分点清晰，纯中文，500字以内。
    """

    # 4. 调用LLM
    print(f"🤖 调用LLM生成{stock_code}基本面报告...")
    try:
        response = llm.invoke(prompt)
        analysis_report = response.content.strip()
    except Exception as e:
        raise Exception(f"LLM生成报告失败：{str(e)}")

    # 5. 整合结果
    final_result = {
        "stock_code": stock_code,
        "market_data": market_data,
        "financial_data": financial_data,
        "fundamental_indicators": fundamental_indicators,
        "llm_analysis_report": analysis_report,
        "source": market_data["source"],
        "timestamp": market_data.get("timestamp", 0)
    }

    print(f"✅ {stock_code}基本面分析完成")
    return final_result

# 测试入口
if __name__ == "__main__":
    try:
        result = get_fundamental_analysis("AAPL")
        print(f"\n📝 {result['stock_code']} 分析报告：\n{result['llm_analysis_report']}")
    except Exception as e:
        print(f"❌ 分析失败：{str(e)}")