"""
数据处理器模块
提供数据清洗、转换和标准化功能
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from decimal import Decimal

from ..core import get_logger
from .models import DataPoint, CommodityData, ForexData


class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def clean_price_string(self, price_str: str) -> Optional[float]:
        """
        清洗价格字符串
        
        Args:
            price_str: 原始价格字符串
            
        Returns:
            Optional[float]: 清洗后的价格，如果无法解析则返回None
        """
        if not price_str or pd.isna(price_str):
            return None
        
        # 转换为字符串并去除空白
        price_str = str(price_str).strip()
        
        if not price_str:
            return None
        
        try:
            # 移除货币符号和单位
            price_str = re.sub(r'[^\d.,-]', '', price_str)
            
            # 处理千分位逗号
            if ',' in price_str and '.' in price_str:
                # 如果同时有逗号和点，判断哪个是小数点
                comma_pos = price_str.rfind(',')
                dot_pos = price_str.rfind('.')
                
                if dot_pos > comma_pos:
                    # 点是小数点，逗号是千分位
                    price_str = price_str.replace(',', '')
                else:
                    # 逗号是小数点，点是千分位
                    price_str = price_str.replace('.', '').replace(',', '.')
            
            elif ',' in price_str:
                # 只有逗号，需要判断是千分位还是小数点
                parts = price_str.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # 很可能是小数点
                    price_str = price_str.replace(',', '.')
                else:
                    # 很可能是千分位
                    price_str = price_str.replace(',', '')
            
            # 转换为浮点数
            return float(price_str)
            
        except (ValueError, TypeError):
            self.logger.warning(f"无法解析价格字符串: {price_str}")
            return None
    
    def clean_percentage_string(self, percent_str: str) -> Optional[float]:
        """
        清洗百分比字符串
        
        Args:
            percent_str: 原始百分比字符串
            
        Returns:
            Optional[float]: 清洗后的百分比数值
        """
        if not percent_str or pd.isna(percent_str):
            return None
        
        # 转换为字符串并去除空白
        percent_str = str(percent_str).strip()
        
        if not percent_str:
            return None
        
        try:
            # 移除百分号和其他符号，保留数字、小数点和负号
            percent_str = re.sub(r'[^\d.,-]', '', percent_str)
            
            # 处理逗号
            percent_str = percent_str.replace(',', '.')
            
            # 转换为浮点数
            value = float(percent_str)
            
            # 如果值很大，可能原始数据已经是百分比形式，不需要除以100
            if abs(value) <= 100:
                return value
            else:
                return value / 100
                
        except (ValueError, TypeError):
            self.logger.warning(f"无法解析百分比字符串: {percent_str}")
            return None
    
    def extract_commodity_symbol(self, text: str) -> str:
        """
        从文本中提取商品符号
        
        Args:
            text: 包含符号的文本
            
        Returns:
            str: 提取的符号
        """
        if not text:
            return ""
        
        # 常见的商品符号模式
        symbol_patterns = [
            r'([A-Z]+\d*:COM)',  # 如 GC1:COM
            r'([A-Z]+USD:CUR)',  # 如 XAUUSD:CUR
            r'([A-Z]+\d+)',      # 如 GC1
            r'([A-Z]{2,4})',     # 通用符号
        ]
        
        for pattern in symbol_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def standardize_commodity_name(self, name: str) -> str:
        """
        标准化商品名称
        
        Args:
            name: 原始商品名称
            
        Returns:
            str: 标准化后的名称
        """
        if not name:
            return ""
        
        # 去除多余空白
        name = re.sub(r'\s+', ' ', name.strip())
        
        # 标准化映射
        name_mappings = {
            'Oil (WTI)': 'WTI原油',
            'Oil (Brent)': '布伦特原油',
            'Natural Gas': '天然气',
            'Natural Gas (Henry Hub)': '天然气',
            'RBOB Gasoline': 'RBOB汽油',
            'Heating Oil': '取暖油',
            'Live Cattle': '活牛',
            'Lean Hog': '瘦肉猪',
            'Feeder Cattle': '饲料牛',
        }
        
        return name_mappings.get(name, name)
    
    def categorize_commodity(self, name: str, symbol: str = "") -> str:
        """
        为商品分类
        
        Args:
            name: 商品名称
            symbol: 商品符号
            
        Returns:
            str: 商品分类
        """
        name_lower = name.lower()
        symbol_lower = symbol.lower()
        
        # 能源类
        energy_keywords = ['oil', 'gas', 'gasoline', '原油', '天然气', '汽油', '取暖油', 'heating', 'brent', 'wti']
        if any(keyword in name_lower for keyword in energy_keywords):
            return "能源"
        
        # 贵金属
        precious_metals = ['gold', 'silver', 'platinum', 'palladium', '黄金', '白银', '铂金', '钯金']
        if any(metal in name_lower for metal in precious_metals):
            return "贵金属"
        
        # 工业金属
        industrial_metals = ['copper', 'aluminum', 'zinc', 'nickel', 'lead', 'tin', '铜', '铝', '锌', '镍', '铅', '锡']
        if any(metal in name_lower for metal in industrial_metals):
            return "工业金属"
        
        # 农产品
        agriculture_keywords = ['corn', 'wheat', 'soybean', 'cotton', 'sugar', 'coffee', 'cocoa', 'cattle', 'hog',
                               '玉米', '小麦', '大豆', '棉花', '糖', '咖啡', '可可', '牛', '猪']
        if any(keyword in name_lower for keyword in agriculture_keywords):
            return "农产品"
        
        # 根据符号判断
        if 'com' in symbol_lower:
            return "商品"
        elif 'cur' in symbol_lower:
            return "货币"
        
        return "其他"
    
    def process_raw_data(self, raw_data: List[Dict[str, Any]], data_type: str = "commodity") -> List[Union[CommodityData, ForexData]]:
        """
        处理原始数据
        
        Args:
            raw_data: 原始数据列表
            data_type: 数据类型 ("commodity" 或 "forex")
            
        Returns:
            List: 处理后的数据对象列表
        """
        processed_data = []
        
        for item in raw_data:
            try:
                if data_type == "commodity":
                    processed_item = self._process_commodity_item(item)
                elif data_type == "forex":
                    processed_item = self._process_forex_item(item)
                else:
                    self.logger.warning(f"未知数据类型: {data_type}")
                    continue
                
                if processed_item:
                    processed_data.append(processed_item)
                    
            except Exception as e:
                self.logger.error(f"处理数据项失败: {item} - {e}")
                continue
        
        self.logger.info(f"成功处理 {len(processed_data)}/{len(raw_data)} 条数据")
        return processed_data
    
    def _process_commodity_item(self, item: Dict[str, Any]) -> Optional[CommodityData]:
        """处理单个商品数据项"""
        try:
            # 提取基本信息
            name = self.standardize_commodity_name(item.get('name', ''))
            symbol = self.extract_commodity_symbol(item.get('symbol', ''))
            
            # 处理价格
            current_price = self.clean_price_string(item.get('price', item.get('current_price')))
            
            if not name or current_price is None:
                return None
            
            # 处理变化信息
            change_amount = None
            change_percent = item.get('change_percent')  # 优先使用原始数据中的change_percent
            
            change_str = item.get('change', '')
            if change_str:
                if '%' in str(change_str):
                    if change_percent is None:  # 只有在没有直接提供时才解析
                        change_percent = self.clean_percentage_string(change_str)
                else:
                    change_amount = self.clean_price_string(change_str)
            
            # 创建商品数据对象
            commodity_data = CommodityData(
                name=name,
                value=current_price,
                timestamp=item.get('timestamp', datetime.now()),
                source=item.get('source', ''),
                metadata=item.get('metadata', {}),
                symbol=symbol,
                chinese_name=item.get('chinese_name', name),
                category=self.categorize_commodity(name, symbol),
                currency=item.get('currency', 'USD'),
                current_price=current_price,
                change_amount=change_amount,
                change_percent=change_percent
            )
            
            return commodity_data
            
        except Exception as e:
            self.logger.error(f"处理商品数据失败: {e}")
            return None
    
    def _process_forex_item(self, item: Dict[str, Any]) -> Optional[ForexData]:
        """处理单个外汇数据项"""
        try:
            # 提取货币对信息
            pair = item.get('pair', item.get('currency_pair', ''))
            
            if '/' in pair:
                base_currency, quote_currency = pair.split('/', 1)
            else:
                base_currency = item.get('base_currency', '')
                quote_currency = item.get('quote_currency', '')
                pair = f"{base_currency}/{quote_currency}" if base_currency and quote_currency else pair
            
            # 处理价格
            bid_price = self.clean_price_string(item.get('bid_price'))
            ask_price = self.clean_price_string(item.get('ask_price'))
            current_price = self.clean_price_string(item.get('current_price', item.get('price')))
            
            # 创建外汇数据对象
            forex_data = ForexData(
                name=pair,
                value=current_price,
                timestamp=item.get('timestamp', datetime.now()),
                source=item.get('source', ''),
                metadata=item.get('metadata', {}),
                base_currency=base_currency.strip(),
                quote_currency=quote_currency.strip(),
                pair=pair,
                bid_price=bid_price,
                ask_price=ask_price,
                mid_price=current_price
            )
            
            return forex_data
            
        except Exception as e:
            self.logger.error(f"处理外汇数据失败: {e}")
            return None
    
    def merge_duplicate_data(self, data_list: List[Union[CommodityData, ForexData]]) -> List[Union[CommodityData, ForexData]]:
        """
        合并重复数据
        
        Args:
            data_list: 数据列表
            
        Returns:
            List: 去重后的数据列表
        """
        if not data_list:
            return []
        
        # 按名称和符号分组
        data_groups = {}
        
        for data_item in data_list:
            if isinstance(data_item, CommodityData):
                key = (data_item.name, data_item.symbol)
            elif isinstance(data_item, ForexData):
                key = (data_item.pair, data_item.base_currency, data_item.quote_currency)
            else:
                key = (data_item.name, data_item.source)
            
            if key not in data_groups:
                data_groups[key] = []
            data_groups[key].append(data_item)
        
        # 合并每组数据
        merged_data = []
        for group in data_groups.values():
            if len(group) == 1:
                merged_data.append(group[0])
            else:
                # 合并逻辑：选择最新的数据，或者合并多个数据源的信息
                latest_item = max(group, key=lambda x: x.timestamp)
                
                # 更新数据源信息
                sources = [item.source for item in group if item.source]
                if len(sources) > 1:
                    latest_item.source = ",".join(set(sources))
                
                merged_data.append(latest_item)
        
        self.logger.info(f"数据去重：{len(data_list)} -> {len(merged_data)}")
        return merged_data 