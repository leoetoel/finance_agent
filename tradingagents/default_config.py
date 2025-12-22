# tradingagents/default_config.py
"""全局默认配置文件，所有配置项在此定义，可被自定义配置覆盖"""

DEFAULT_CONFIG = {
    # LLM 相关配置
    "deep_think_llm": "gpt-4o",
    "fast_think_llm": "gpt-4.1-mini",
    
    # 数据源优先级配置：key=分类名，value=数据源列表（逗号分隔）
    "data_vendors": {
        "core_stock_apis": "finhub,yfinance,alpha_vantage",  # 优先Finhub，失败降级到yfinance/AlphaVantage
        "news_data": "alpha_vantage,openai",
        "technical_indicators": "yfinance,alpha_vantage"
    },
    
    # 方法级数据源优先级（可选，优先级高于分类级）
    "tool_vendors": {},
    
    # API密钥配置（运行时需替换为真实密钥）
    "FINHUB_API_KEY": "d53sdf1r01qkplh15q4gd53sdf1r01qkplh15q50",
    "ALPHA_VANTAGE_API_KEY": "",
    "OPENAI_API_KEY": "",
    
    # 通用配置
    "timeout": 10,  # API请求超时时间（秒）
    "cache_ttl": 300  # 数据缓存有效期（秒）
}