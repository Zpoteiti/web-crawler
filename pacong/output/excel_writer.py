"""
Excel输出模块
提供Excel格式的数据输出功能
"""

from typing import List, Union, Dict, Any
from pathlib import Path
import pandas as pd

from ..core import get_logger
from ..data import CommodityData, ForexData


class ExcelWriter:
    """Excel文件写入器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def write_commodity_data(self, commodities: List[CommodityData], filepath: Union[str, Path]):
        """
        写入商品数据到Excel文件
        
        Args:
            commodities: 商品数据列表
            filepath: 输出文件路径
        """
        if not commodities:
            self.logger.warning("无商品数据可写入")
            return
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 转换为DataFrame
            data_list = []
            for commodity in commodities:
                data_list.append({
                    '商品名称': commodity.name,
                    '中文名称': commodity.chinese_name,
                    '商品代码': commodity.symbol,
                    '分类': commodity.category,
                    '货币': commodity.currency,
                    '当前价格': commodity.current_price,
                    '变化金额': commodity.change_amount,
                    '变化百分比(%)': commodity.change_percent,
                    '开盘价': commodity.open_price,
                    '最高价': commodity.high_price,
                    '最低价': commodity.low_price,
                    '昨收价': commodity.previous_close,
                    '成交量': commodity.volume,
                    '市值': commodity.market_cap,
                    '数据源': commodity.source,
                    '更新时间': commodity.timestamp
                })
            
            df = pd.DataFrame(data_list)
            
            # 按分类分组数据
            categories = df['分类'].unique() if '分类' in df.columns else []
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 写入总表
                df.to_excel(writer, sheet_name='全部商品', index=False)
                
                # 按分类创建工作表
                for category in categories:
                    if category and category != '其他':
                        category_df = df[df['分类'] == category]
                        if not category_df.empty:
                            # 按价格排序
                            if '当前价格' in category_df.columns:
                                category_df = category_df.sort_values('当前价格', ascending=False)
                            category_df.to_excel(writer, sheet_name=category, index=False)
                
                # 创建摘要表
                summary_data = self._create_commodity_summary(commodities)
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='数据摘要', index=False)
            
            self.logger.info(f"成功写入 {len(commodities)} 条商品数据到 {filepath}")
            
        except Exception as e:
            self.logger.error(f"写入Excel文件失败: {e}")
            raise
    
    def write_forex_data(self, forex_data: List[ForexData], filepath: Union[str, Path]):
        """
        写入外汇数据到Excel文件
        
        Args:
            forex_data: 外汇数据列表
            filepath: 输出文件路径
        """
        if not forex_data:
            self.logger.warning("无外汇数据可写入")
            return
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 转换为DataFrame
            data_list = []
            for forex in forex_data:
                data_list.append({
                    '货币对': forex.pair,
                    '基础货币': forex.base_currency,
                    '报价货币': forex.quote_currency,
                    '买入价': forex.bid_price,
                    '卖出价': forex.ask_price,
                    '中间价': forex.mid_price,
                    '点差': forex.spread,
                    '变化金额': forex.change_amount,
                    '变化百分比(%)': forex.change_percent,
                    '数据源': forex.source,
                    '更新时间': forex.timestamp
                })
            
            df = pd.DataFrame(data_list)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 写入主表
                df.to_excel(writer, sheet_name='外汇数据', index=False)
                
                # 创建摘要表
                summary_data = self._create_forex_summary(forex_data)
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='数据摘要', index=False)
            
            self.logger.info(f"成功写入 {len(forex_data)} 条外汇数据到 {filepath}")
            
        except Exception as e:
            self.logger.error(f"写入Excel文件失败: {e}")
            raise
    
    def _create_commodity_summary(self, commodities: List[CommodityData]) -> List[Dict[str, Any]]:
        """创建商品数据摘要"""
        if not commodities:
            return []
        
        summary = []
        
        # 基本统计
        total_count = len(commodities)
        commodities_with_change = [c for c in commodities if c.change_percent is not None]
        
        summary.append({'指标': '总商品数', '数值': total_count})
        summary.append({'指标': '有涨跌数据的商品', '数值': len(commodities_with_change)})
        
        if commodities_with_change:
            avg_change = sum(c.change_percent for c in commodities_with_change) / len(commodities_with_change)
            gainers = len([c for c in commodities_with_change if c.change_percent > 0])
            losers = len([c for c in commodities_with_change if c.change_percent < 0])
            
            summary.append({'指标': '平均涨跌幅(%)', '数值': round(avg_change, 2)})
            summary.append({'指标': '上涨商品数', '数值': gainers})
            summary.append({'指标': '下跌商品数', '数值': losers})
        
        # 分类统计
        from collections import Counter
        categories = Counter(c.category for c in commodities if c.category)
        
        summary.append({'指标': '', '数值': ''})  # 空行
        summary.append({'指标': '=== 分类统计 ===', '数值': ''})
        
        for category, count in categories.most_common():
            summary.append({'指标': f'{category}商品数', '数值': count})
        
        return summary
    
    def _create_forex_summary(self, forex_data: List[ForexData]) -> List[Dict[str, Any]]:
        """创建外汇数据摘要"""
        if not forex_data:
            return []
        
        summary = []
        
        # 基本统计
        total_count = len(forex_data)
        summary.append({'指标': '总货币对数', '数值': total_count})
        
        # 点差统计
        spreads = [f.spread for f in forex_data if f.spread is not None]
        if spreads:
            avg_spread = sum(spreads) / len(spreads)
            summary.append({'指标': '平均点差', '数值': round(avg_spread, 4)})
        
        return summary 