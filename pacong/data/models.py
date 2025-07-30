"""
数据模型模块
定义标准的数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union, List
from datetime import datetime
from decimal import Decimal
import json


@dataclass
class DataPoint:
    """基础数据点"""
    name: str
    value: Union[float, Decimal, str]
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'value': float(self.value) if isinstance(self.value, (int, float, Decimal)) else self.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataPoint':
        """从字典创建"""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            name=data['name'],
            value=data['value'],
            timestamp=timestamp,
            source=data.get('source', ''),
            metadata=data.get('metadata', {})
        )


@dataclass
class CommodityData(DataPoint):
    """商品数据"""
    symbol: str = ""
    chinese_name: str = ""
    category: str = ""
    unit: str = ""
    currency: str = "USD"
    
    # 价格信息
    current_price: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    previous_close: Optional[float] = None
    
    # 变化信息
    change_amount: Optional[float] = None
    change_percent: Optional[float] = None
    
    # 交易信息
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    
    def __post_init__(self):
        """后处理"""
        if self.current_price is not None:
            self.value = self.current_price
        
        # 如果有变化金额但没有变化百分比，尝试计算
        if (self.change_amount is not None and 
            self.change_percent is None and 
            self.previous_close is not None and 
            self.previous_close != 0):
            self.change_percent = (self.change_amount / self.previous_close) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'symbol': self.symbol,
            'chinese_name': self.chinese_name,
            'category': self.category,
            'unit': self.unit,
            'currency': self.currency,
            'current_price': self.current_price,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'previous_close': self.previous_close,
            'change_amount': self.change_amount,
            'change_percent': self.change_percent,
            'volume': self.volume,
            'market_cap': self.market_cap
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommodityData':
        """从字典创建"""
        # 处理时间戳
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            name=data.get('name', ''),
            value=data.get('value', data.get('current_price', 0)),
            timestamp=timestamp,
            source=data.get('source', ''),
            metadata=data.get('metadata', {}),
            symbol=data.get('symbol', ''),
            chinese_name=data.get('chinese_name', ''),
            category=data.get('category', ''),
            unit=data.get('unit', ''),
            currency=data.get('currency', 'USD'),
            current_price=data.get('current_price'),
            open_price=data.get('open_price'),
            high_price=data.get('high_price'),
            low_price=data.get('low_price'),
            previous_close=data.get('previous_close'),
            change_amount=data.get('change_amount'),
            change_percent=data.get('change_percent'),
            volume=data.get('volume'),
            market_cap=data.get('market_cap')
        )


@dataclass 
class ForexData(DataPoint):
    """外汇数据"""
    base_currency: str = ""
    quote_currency: str = ""
    pair: str = ""
    
    # 价格信息
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    mid_price: Optional[float] = None
    
    # 变化信息
    change_amount: Optional[float] = None
    change_percent: Optional[float] = None
    
    # 其他信息
    spread: Optional[float] = None
    
    def __post_init__(self):
        """后处理"""
        # 设置货币对
        if not self.pair and self.base_currency and self.quote_currency:
            self.pair = f"{self.base_currency}/{self.quote_currency}"
        
        # 计算中间价
        if (self.bid_price is not None and 
            self.ask_price is not None and 
            self.mid_price is None):
            self.mid_price = (self.bid_price + self.ask_price) / 2
        
        # 计算点差
        if (self.bid_price is not None and 
            self.ask_price is not None and 
            self.spread is None):
            self.spread = self.ask_price - self.bid_price
        
        # 设置主要价格
        if self.value is None:
            self.value = self.mid_price or self.bid_price or self.ask_price
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'base_currency': self.base_currency,
            'quote_currency': self.quote_currency,
            'pair': self.pair,
            'bid_price': self.bid_price,
            'ask_price': self.ask_price,
            'mid_price': self.mid_price,
            'change_amount': self.change_amount,
            'change_percent': self.change_percent,
            'spread': self.spread
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForexData':
        """从字典创建"""
        # 处理时间戳
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            name=data.get('name', ''),
            value=data.get('value', data.get('mid_price', data.get('bid_price'))),
            timestamp=timestamp,
            source=data.get('source', ''),
            metadata=data.get('metadata', {}),
            base_currency=data.get('base_currency', ''),
            quote_currency=data.get('quote_currency', ''),
            pair=data.get('pair', ''),
            bid_price=data.get('bid_price'),
            ask_price=data.get('ask_price'),
            mid_price=data.get('mid_price'),
            change_amount=data.get('change_amount'),
            change_percent=data.get('change_percent'),
            spread=data.get('spread')
        )


@dataclass
class ScrapingResult:
    """爬取结果"""
    scraper_name: str
    data_points: List[Union[DataPoint, CommodityData, ForexData]]
    start_time: datetime
    end_time: datetime
    success_count: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def execution_time(self) -> float:
        """执行时间（秒）"""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.success_count + self.error_count
        return self.success_count / total if total > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'scraper_name': self.scraper_name,
            'data_points': [dp.to_dict() for dp in self.data_points],
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'execution_time': self.execution_time,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': self.success_rate,
            'errors': self.errors,
            'metadata': self.metadata
        }
    
    def save_to_json(self, filepath: str):
        """保存为JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False) 