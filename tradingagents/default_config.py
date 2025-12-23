# tradingagents/default_config.py
"""全局默认配置文件，所有配置项在此定义，可被自定义配置覆盖"""

DEFAULT_CONFIG = {
    # DeepSeek LLM 相关配置（替换原有OpenAI配置）
    "llm_model": "deepseek-chat",  # DeepSeek默认对话模型，也可填deepseek-coder
    "deepseek_api_key": "sk-4010fb2096b74025945e2b6e49a979e9",        # 需替换为你的DeepSeek API Key
    "deepseek_base_url": "https://api.deepseek.com/v1",  # DeepSeek API基础地址
    "llm_temperature": 0.1,        # 低随机性保证分析严谨
    
    # 数据源优先级配置（保留不变）
    "data_vendors": {
        "core_stock_apis": "finhub,yfinance,alpha_vantage",
        "news_data": "alpha_vantage,openai",
        "technical_indicators": "yfinance,alpha_vantage"
    },
    
    # 方法级数据源优先级（可选）
    "tool_vendors": {},
    
    # API密钥配置（保留，Finhub/AlphaVantage不变）
    "FINHUB_API_KEY": "d53sdf1r01qkplh15q4gd53sdf1r01qkplh15q50",
    "ALPHA_VANTAGE_API_KEY": "",
    
    # 通用配置（保留）
    "timeout": 10,
    "cache_ttl": 300
}