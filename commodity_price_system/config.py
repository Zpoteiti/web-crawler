"""
配置文件
"""

import os

# API配置
COMMODITY_API_BASE_URL = "https://commodities-api.com/api"
# 你的API密钥
API_KEY = "15f8909b-e4ae-48f0-adc8-4dfa89725992"

# 商品符号映射 (商品名称 -> API符号)
COMMODITY_SYMBOLS = {
    'gold': 'XAU',
    'silver': 'XAG', 
    'crude_oil': 'BRENTOIL',
    'brent_oil': 'BRENTOIL',
    'natural_gas': 'NG',
    'wheat': 'WHEAT',
    'corn': 'CORN',
    'soybeans': 'SOYBEAN',
    'copper': 'COPPER',
    'rice': 'RICE',
    'sugar': 'SUGAR'
}

# 商品列表
DEFAULT_COMMODITIES = [
    'gold',
    'silver', 
    'crude_oil',
    'natural_gas',
    'wheat',
    'corn',
    'soybeans',
    'copper'
]

# 数据配置
DATA_RETENTION_DAYS = 30
RATE_LIMIT_SECONDS = 36  # API Ninjas免费版：100次/小时

# 报告配置
REPORT_SCHEDULE_TIMES = ["08:00", "18:00"]
DATA_COLLECTION_INTERVAL_HOURS = 1

# 文件路径
DATA_FILE = "commodity_data.json"
# 报告目录
REPORTS_DIR = "reports"