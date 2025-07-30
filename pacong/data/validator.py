"""
数据验证器模块
提供数据有效性验证功能
"""

import re
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from ..core import get_logger
from .models import DataPoint, CommodityData, ForexData


class ValidationRule:
    """验证规则基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        验证值
        
        Args:
            value: 待验证的值
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        raise NotImplementedError


class NotNullRule(ValidationRule):
    """非空验证规则"""
    
    def __init__(self):
        super().__init__("not_null", "值不能为空")
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None or value == "":
            return False, f"{self.description}"
        return True, None


class NumericRangeRule(ValidationRule):
    """数值范围验证规则"""
    
    def __init__(self, min_val: Optional[float] = None, max_val: Optional[float] = None):
        self.min_val = min_val
        self.max_val = max_val
        super().__init__("numeric_range", f"数值范围验证 [{min_val}, {max_val}]")
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        try:
            num_val = float(value)
            
            if self.min_val is not None and num_val < self.min_val:
                return False, f"值 {num_val} 小于最小值 {self.min_val}"
            
            if self.max_val is not None and num_val > self.max_val:
                return False, f"值 {num_val} 大于最大值 {self.max_val}"
            
            return True, None
            
        except (ValueError, TypeError):
            return False, f"无法转换为数值: {value}"


class RegexRule(ValidationRule):
    """正则表达式验证规则"""
    
    def __init__(self, pattern: str, description: str):
        self.pattern = re.compile(pattern)
        super().__init__("regex", description)
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        str_val = str(value)
        if self.pattern.match(str_val):
            return True, None
        return False, f"值 '{str_val}' 不匹配模式: {self.description}"


class TimestampRule(ValidationRule):
    """时间戳验证规则"""
    
    def __init__(self, max_age_hours: int = 24):
        self.max_age_hours = max_age_hours
        super().__init__("timestamp", f"时间戳验证 (最大年龄: {max_age_hours}小时)")
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        try:
            if isinstance(value, str):
                timestamp = datetime.fromisoformat(value)
            elif isinstance(value, datetime):
                timestamp = value
            else:
                return False, f"无效的时间戳类型: {type(value)}"
            
            # 检查时间戳是否过旧
            age = datetime.now() - timestamp
            if age.total_seconds() > self.max_age_hours * 3600:
                return False, f"时间戳过旧: {age}"
            
            # 检查时间戳是否是未来时间
            if timestamp > datetime.now() + timedelta(hours=1):
                return False, f"时间戳是未来时间: {timestamp}"
            
            return True, None
            
        except Exception as e:
            return False, f"时间戳验证失败: {e}"


class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._setup_validation_rules()
    
    def _setup_validation_rules(self):
        """设置验证规则"""
        self.commodity_rules = {
            'name': [NotNullRule()],
            'current_price': [NumericRangeRule(min_val=0, max_val=1000000)],  # 价格可选，但如果存在必须有效
            'change_percent': [NumericRangeRule(min_val=-100, max_val=1000)],
            'timestamp': [TimestampRule(max_age_hours=48)]
        }
        
        self.forex_rules = {
            'pair': [
                NotNullRule(),
                RegexRule(r'^[A-Z]{3}/[A-Z]{3}$', '货币对格式 (例: USD/EUR)')
            ],
            'bid_price': [NumericRangeRule(min_val=0)],
            'ask_price': [NumericRangeRule(min_val=0)],
            'timestamp': [TimestampRule(max_age_hours=24)]
        }
        
        self.general_rules = {
            'source': [NotNullRule()],
            'timestamp': [TimestampRule()]
        }
    
    def validate_commodity_data(self, data: CommodityData) -> Tuple[bool, List[str]]:
        """
        验证商品数据
        
        Args:
            data: 商品数据对象
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        return self._validate_data_with_rules(data, self.commodity_rules)
    
    def validate_forex_data(self, data: ForexData) -> Tuple[bool, List[str]]:
        """
        验证外汇数据
        
        Args:
            data: 外汇数据对象
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        return self._validate_data_with_rules(data, self.forex_rules)
    
    def validate_data_point(self, data: DataPoint) -> Tuple[bool, List[str]]:
        """
        验证数据点
        
        Args:
            data: 数据点对象
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        return self._validate_data_with_rules(data, self.general_rules)
    
    def _validate_data_with_rules(self, data: Union[DataPoint, CommodityData, ForexData], rules: Dict[str, List[ValidationRule]]) -> Tuple[bool, List[str]]:
        """
        使用规则验证数据
        
        Args:
            data: 数据对象
            rules: 验证规则字典
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        for field_name, field_rules in rules.items():
            # 获取字段值
            field_value = getattr(data, field_name, None)
            
            # 应用每个规则
            for rule in field_rules:
                is_valid, error_msg = rule.validate(field_value)
                if not is_valid:
                    errors.append(f"{field_name}: {error_msg}")
        
        # 执行业务逻辑验证
        business_errors = self._validate_business_logic(data)
        errors.extend(business_errors)
        
        return len(errors) == 0, errors
    
    def _validate_business_logic(self, data: Union[DataPoint, CommodityData, ForexData]) -> List[str]:
        """
        业务逻辑验证
        
        Args:
            data: 数据对象
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        if isinstance(data, CommodityData):
            errors.extend(self._validate_commodity_business_logic(data))
        elif isinstance(data, ForexData):
            errors.extend(self._validate_forex_business_logic(data))
        
        return errors
    
    def _validate_commodity_business_logic(self, data: CommodityData) -> List[str]:
        """验证商品数据的业务逻辑"""
        errors = []
        
        # 价格一致性检查
        if data.current_price and data.value and abs(data.current_price - data.value) > 0.001:
            errors.append(f"当前价格与主值不一致: {data.current_price} vs {data.value}")
        
        # 价格范围检查
        if data.high_price and data.low_price and data.high_price < data.low_price:
            errors.append(f"最高价不能低于最低价: {data.high_price} < {data.low_price}")
        
        if data.current_price:
            if data.high_price and data.current_price > data.high_price:
                errors.append(f"当前价格超过最高价: {data.current_price} > {data.high_price}")
            if data.low_price and data.current_price < data.low_price:
                errors.append(f"当前价格低于最低价: {data.current_price} < {data.low_price}")
        
        # 变化幅度合理性检查
        if data.change_percent and abs(data.change_percent) > 50:
            errors.append(f"变化幅度过大: {data.change_percent}%")
        
        return errors
    
    def _validate_forex_business_logic(self, data: ForexData) -> List[str]:
        """验证外汇数据的业务逻辑"""
        errors = []
        
        # 买卖价格检查
        if data.bid_price and data.ask_price:
            if data.bid_price > data.ask_price:
                errors.append(f"买入价不能高于卖出价: {data.bid_price} > {data.ask_price}")
            
            # 点差合理性检查
            spread = data.ask_price - data.bid_price
            if spread > data.bid_price * 0.1:  # 点差不应超过买入价的10%
                errors.append(f"点差过大: {spread}")
        
        # 中间价检查
        if data.mid_price and data.bid_price and data.ask_price:
            expected_mid = (data.bid_price + data.ask_price) / 2
            if abs(data.mid_price - expected_mid) > 0.0001:
                errors.append(f"中间价计算错误: {data.mid_price} vs {expected_mid}")
        
        return errors
    
    def validate_data_list(self, data_list: List[Union[DataPoint, CommodityData, ForexData]]) -> Tuple[List[Union[DataPoint, CommodityData, ForexData]], List[Dict[str, Any]]]:
        """
        批量验证数据
        
        Args:
            data_list: 数据列表
            
        Returns:
            Tuple: (有效数据列表, 无效数据信息列表)
        """
        valid_data = []
        invalid_data = []
        
        for i, data_item in enumerate(data_list):
            try:
                if isinstance(data_item, CommodityData):
                    is_valid, errors = self.validate_commodity_data(data_item)
                elif isinstance(data_item, ForexData):
                    is_valid, errors = self.validate_forex_data(data_item)
                else:
                    is_valid, errors = self.validate_data_point(data_item)
                
                if is_valid:
                    valid_data.append(data_item)
                else:
                    invalid_data.append({
                        'index': i,
                        'data': data_item,
                        'errors': errors
                    })
                    self.logger.warning(f"数据验证失败 [索引 {i}]: {errors}")
            
            except Exception as e:
                invalid_data.append({
                    'index': i,
                    'data': data_item,
                    'errors': [f"验证异常: {e}"]
                })
                self.logger.error(f"数据验证异常 [索引 {i}]: {e}")
        
        self.logger.info(f"数据验证完成: 有效 {len(valid_data)}, 无效 {len(invalid_data)}")
        return valid_data, invalid_data
    
    def get_validation_summary(self, invalid_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取验证摘要
        
        Args:
            invalid_data: 无效数据列表
            
        Returns:
            Dict: 验证摘要
        """
        if not invalid_data:
            return {"status": "all_valid", "total_errors": 0}
        
        error_counts = {}
        for item in invalid_data:
            for error in item['errors']:
                error_type = error.split(':')[0] if ':' in error else error
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "status": "has_errors",
            "total_errors": len(invalid_data),
            "error_breakdown": error_counts,
            "most_common_error": max(error_counts.items(), key=lambda x: x[1]) if error_counts else None
        } 