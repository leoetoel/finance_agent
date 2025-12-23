# tradingagents/agents/technical_analyst.py
from typing import Dict, Any
from langchain_openai import ChatOpenAI  # DeepSeek兼容OpenAI接口，无需新增依赖
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.dataflows.config import get_config
from .utils.indicators import calculate_technical_indicators

# 初始化配置
CONFIG = get_config()

# ========== 替换为DeepSeek LLM初始化 ==========
llm = ChatOpenAI(
    model=CONFIG.get("llm_model", "deepseek-chat"),  # DeepSeek模型名
    api_key=CONFIG.get("deepseek_api_key"),          # DeepSeek API Key
    base_url=CONFIG.get("deepseek_base_url", "https://api.deepseek.com/v1"),  # DeepSeek API地址
    temperature=CONFIG.get("llm_temperature", 0.1)   # 随机性配置
)

def get_technical_analysis(stock_code: str) -> Dict[str, Any]:
    """
    技术分析师Agent核心函数：输入股票代码，输出完整技术分析报告
    :param stock_code: 股票代码（如AAPL）
    :return: 包含数据、指标、分析报告的结构化结果
    """
    # Step 1: 调用数据源模块获取数据
    print(f"📊 技术分析师Agent：获取{stock_code}的股票数据...")
    stock_data = route_to_vendor("get_stock_data", stock_code)
    ohlc_data = route_to_vendor("get_ohlc_data", stock_code, resolution="1D", count=30)
    
    # Step 2: 计算技术指标
    print(f"📈 技术分析师Agent：计算{stock_code}的技术指标...")
    indicators = calculate_technical_indicators(stock_data, ohlc_data)
    
    # Step 3: 构建LLM提示词（保留原有逻辑，DeepSeek兼容相同提示词）
    prompt = f"""
    你是一名资深金融技术分析师，擅长基于技术指标和市场数据做出专业、严谨的分析。
    请基于以下信息，为股票{stock_code}撰写一份详细的技术分析报告：

    ### 1. 基础数据（{stock_code}）
    - 当前价格：{stock_data['current_price']} USD
    - 当日开盘价：{stock_data['open_price']} USD
    - 当日最高价：{stock_data['high_price']} USD
    - 当日最低价：{stock_data['low_price']} USD
    - 成交量：{stock_data['volume']}
    - 涨跌幅：{stock_data['change_percent']}%

    ### 2. 核心技术指标（基于近30天日线数据）
    - RSI（14日）：{indicators['latest_values']['rsi']} → 趋势：{indicators['trends']['rsi']}
    - MACD：{indicators['latest_values']['macd']}（信号线：{indicators['latest_values']['macd_signal']}）→ 趋势：{indicators['trends']['macd']}
    - 布林带：上轨={indicators['latest_values']['bollinger_upper']}，下轨={indicators['latest_values']['bollinger_lower']} → 趋势：{indicators['trends']['bollinger']}

    ### 分析要求
    1. 趋势判断：明确判断短期（1-3天）、中期（1-2周）走势（上涨/下跌/震荡）；
    2. 关键价位：指出支撑位、压力位，并说明判断依据；
    3. 交易信号：给出明确的交易建议（买入/卖出/持有），并说明风险点；
    4. 分析逻辑：基于指标数据和趋势，解释判断的核心依据，避免主观臆断；
    5. 格式要求：分点清晰，语言专业但易懂，总字数控制在500字以内。
    """
    
    # Step 4: 调用DeepSeek LLM生成分析报告（逻辑不变，接口兼容）
    print(f"🤖 技术分析师Agent：调用DeepSeek生成分析报告...")
    response = llm.invoke(prompt)
    analysis_report = response.content.strip()
    
    # Step 5: 整合结构化结果（保留原有逻辑）
    final_result = {
        "stock_code": stock_code,
        "basic_data": stock_data,
        "technical_indicators": indicators,
        "analysis_report": analysis_report,
        "source": stock_data["source"],
        "timestamp": stock_data.get("timestamp")
    }
    
    return final_result