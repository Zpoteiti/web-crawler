"""
CSV输出模块
提供CSV格式的数据输出功能
"""

import csv
from typing import List, Union
from pathlib import Path

from ..core import get_logger
from ..data import CommodityData, ForexData


class CSVWriter:
    """CSV文件写入器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def write_commodity_data(self, commodities: List[CommodityData], filepath: Union[str, Path]):
        """
        写入商品数据到CSV文件
        
        Args:
            commodities: 商品数据列表
            filepath: 输出文件路径
        """
        if not commodities:
            self.logger.warning("无商品数据可写入")
            return
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # 定义CSV字段
        fieldnames = [
            'name', 'chinese_name', 'symbol', 'category', 'currency',
            'current_price', 'change_amount', 'change_percent',
            'open_price', 'high_price', 'low_price', 'previous_close',
            'volume', 'market_cap', 'source', 'timestamp'
        ]
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # 写入表头
                writer.writeheader()
                
                # 写入数据
                for commodity in commodities:
                    row_data = {
                        'name': commodity.name,
                        'chinese_name': commodity.chinese_name,
                        'symbol': commodity.symbol,
                        'category': commodity.category,
                        'currency': commodity.currency,
                        'current_price': commodity.current_price,
                        'change_amount': commodity.change_amount,
                        'change_percent': commodity.change_percent,
                        'open_price': commodity.open_price,
                        'high_price': commodity.high_price,
                        'low_price': commodity.low_price,
                        'previous_close': commodity.previous_close,
                        'volume': commodity.volume,
                        'market_cap': commodity.market_cap,
                        'source': commodity.source,
                        'timestamp': commodity.timestamp.isoformat() if commodity.timestamp else None
                    }
                    writer.writerow(row_data)
            
            self.logger.info(f"成功写入 {len(commodities)} 条商品数据到 {filepath}")
            
        except Exception as e:
            self.logger.error(f"写入CSV文件失败: {e}")
            raise
    
    def write_forex_data(self, forex_data: List[ForexData], filepath: Union[str, Path]):
        """
        写入外汇数据到CSV文件
        
        Args:
            forex_data: 外汇数据列表
            filepath: 输出文件路径
        """
        if not forex_data:
            self.logger.warning("无外汇数据可写入")
            return
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # 定义CSV字段
        fieldnames = [
            'pair', 'base_currency', 'quote_currency',
            'bid_price', 'ask_price', 'mid_price', 'spread',
            'change_amount', 'change_percent',
            'source', 'timestamp'
        ]
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # 写入表头
                writer.writeheader()
                
                # 写入数据
                for forex in forex_data:
                    row_data = {
                        'pair': forex.pair,
                        'base_currency': forex.base_currency,
                        'quote_currency': forex.quote_currency,
                        'bid_price': forex.bid_price,
                        'ask_price': forex.ask_price,
                        'mid_price': forex.mid_price,
                        'spread': forex.spread,
                        'change_amount': forex.change_amount,
                        'change_percent': forex.change_percent,
                        'source': forex.source,
                        'timestamp': forex.timestamp.isoformat() if forex.timestamp else None
                    }
                    writer.writerow(row_data)
            
            self.logger.info(f"成功写入 {len(forex_data)} 条外汇数据到 {filepath}")
            
        except Exception as e:
            self.logger.error(f"写入CSV文件失败: {e}")
            raise 