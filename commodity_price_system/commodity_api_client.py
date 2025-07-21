#!/usr/bin/env python3
"""
Commodity Price API 完整客户端
使用你的API密钥连接到CommodityPriceAPI获取商品价格数据
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import time

class CommodityPriceAPIClient:
    def __init__(self, api_key: str):
        """
        初始化商品价格API客户端
        
        Args:
            api_key: 你的API密钥
        """
        self.api_key = api_key
        self.base_url = "https://api.commoditypriceapi.com/v2"
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'x-api-key': self.api_key,
            'User-Agent': 'CommodityPriceAPI-Client/1.0',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        发送API请求
        
        Args:
            endpoint: API端点
            params: 查询参数
            
        Returns:
            API响应数据
        """
        if params is None:
            params = {}
        
        # 添加API密钥到查询参数作为备用
        params['apiKey'] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('success', False):
                error_msg = data.get('message', 'Unknown error')
                print(f"❌ API错误: {error_msg}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            return None
    
    def check_api_status(self) -> bool:
        """检查API连接状态和使用情况"""
        print("🔍 检查API状态...")
        
        usage_data = self._make_request('usage')
        
        if usage_data:
            print("✅ API连接成功!")
            print(f"📊 当前计划: {usage_data.get('plan', 'Unknown')}")
            print(f"📈 配额限制: {usage_data.get('quota', 'Unknown')}")
            print(f"📉 已使用: {usage_data.get('used', 'Unknown')}")
            return True
        else:
            print("❌ API连接失败")
            return False
    
    def get_supported_symbols(self) -> Optional[Dict]:
        """获取支持的商品符号"""
        print("📋 获取支持的商品符号...")
        
        symbols_data = self._make_request('symbols')
        
        if symbols_data:
            symbols = symbols_data.get('symbols', {})
            print(f"✅ 找到 {len(symbols)} 个支持的商品")
            
            # 按类别分组显示
            categories = {}
            for symbol, info in symbols.items():
                category = info.get('category', 'Other')
                if category not in categories:
                    categories[category] = []
                categories[category].append({
                    'symbol': symbol,
                    'name': info.get('name', 'Unknown'),
                    'unit': info.get('unit', 'Unknown')
                })
            
            for category, items in categories.items():
                print(f"\n📂 {category} ({len(items)} 个商品):")
                for item in items[:5]:  # 只显示前5个
                    print(f"  • {item['symbol']}: {item['name']} ({item['unit']})")
                if len(items) > 5:
                    print(f"  ... 还有 {len(items) - 5} 个商品")
            
            return symbols_data
        
        return None
    
    def get_latest_prices(self, symbols: Union[str, List[str]], quote_currency: str = None) -> Optional[Dict]:
        """
        获取最新价格
        
        Args:
            symbols: 商品符号列表
            quote_currency: 报价货币（可选）
            
        Returns:
            最新价格数据
        """
        if isinstance(symbols, list):
            symbols_str = ','.join(symbols)
        else:
            symbols_str = symbols
        
        print(f"💰 获取最新价格: {symbols_str}")
        
        params = {'symbols': symbols_str}
        if quote_currency:
            params['quote'] = quote_currency
        
        data = self._make_request('latest', params)
        
        if data:
            print("✅ 最新价格获取成功!")
            
            rates = data.get('rates', {})
            metadata = data.get('metaData', {})
            timestamp = data.get('timestamp', 0)
            
            print(f"📅 数据时间: {datetime.fromtimestamp(timestamp)}")
            
            for symbol, rate_info in rates.items():
                meta = metadata.get(symbol, {})
                rate = rate_info.get('rate', 'N/A')
                unit = meta.get('unit', 'Unknown')
                quote = meta.get('quote', 'USD')
                
                print(f"📈 {symbol}: {rate} {quote}/{unit}")
            
            return data
        
        return None
    
    def get_historical_prices(self, symbols: Union[str, List[str]], date: str) -> Optional[Dict]:
        """
        获取历史价格
        
        Args:
            symbols: 商品符号列表
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            历史价格数据
        """
        if isinstance(symbols, list):
            symbols_str = ','.join(symbols)
        else:
            symbols_str = symbols
        
        print(f"📊 获取历史价格: {symbols_str} ({date})")
        
        params = {
            'symbols': symbols_str,
            'date': date
        }
        
        data = self._make_request('historical', params)
        
        if data:
            print("✅ 历史价格获取成功!")
            
            rates = data.get('rates', {})
            request_date = data.get('date', date)
            
            print(f"📅 请求日期: {request_date}")
            
            for symbol, price_data in rates.items():
                actual_date = price_data.get('date', 'Unknown')
                open_price = price_data.get('open', 'N/A')
                high_price = price_data.get('high', 'N/A')
                low_price = price_data.get('low', 'N/A')
                close_price = price_data.get('close', 'N/A')
                
                print(f"📈 {symbol} ({actual_date}):")
                print(f"  开盘: {open_price}, 最高: {high_price}")
                print(f"  最低: {low_price}, 收盘: {close_price}")
            
            return data
        
        return None
    
    def get_timeseries(self, symbols: Union[str, List[str]], start_date: str, end_date: str) -> Optional[Dict]:
        """
        获取时间序列数据
        
        Args:
            symbols: 商品符号列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            时间序列数据
        """
        if isinstance(symbols, list):
            symbols_str = ','.join(symbols)
        else:
            symbols_str = symbols
        
        print(f"📈 获取时间序列: {symbols_str} ({start_date} 到 {end_date})")
        
        params = {
            'symbols': symbols_str,
            'startDate': start_date,
            'endDate': end_date
        }
        
        data = self._make_request('timeseries', params)
        
        if data:
            print("✅ 时间序列获取成功!")
            
            rates = data.get('rates', {})
            start = data.get('startDate', start_date)
            end = data.get('endDate', end_date)
            
            print(f"📅 数据范围: {start} 到 {end}")
            
            # 统计数据点数量
            for symbol, time_data in rates.items():
                data_points = len(time_data)
                print(f"📊 {symbol}: {data_points} 个数据点")
                
                # 显示最新几个数据点
                if isinstance(time_data, dict):
                    recent_dates = sorted(time_data.keys())[-3:]  # 最近3天
                    print(f"  最近数据:")
                    for date in recent_dates:
                        close_price = time_data[date].get('close', 'N/A')
                        print(f"    {date}: {close_price}")
            
            return data
        
        return None
    
    def get_fluctuation(self, symbols: Union[str, List[str]], start_date: str, end_date: str) -> Optional[Dict]:
        """
        获取价格波动数据
        
        Args:
            symbols: 商品符号列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            波动数据
        """
        if isinstance(symbols, list):
            symbols_str = ','.join(symbols)
        else:
            symbols_str = symbols
        
        print(f"📉 获取价格波动: {symbols_str} ({start_date} 到 {end_date})")
        
        params = {
            'symbols': symbols_str,
            'startDate': start_date,
            'endDate': end_date
        }
        
        data = self._make_request('fluctuation', params)
        
        if data:
            print("✅ 价格波动获取成功!")
            
            rates = data.get('rates', {})
            start = data.get('startDate', start_date)
            end = data.get('endDate', end_date)
            
            print(f"📅 波动分析: {start} 到 {end}")
            
            for symbol, fluctuation_data in rates.items():
                start_rate = fluctuation_data.get('startRate', 'N/A')
                end_rate = fluctuation_data.get('endRate', 'N/A')
                change = fluctuation_data.get('change', 'N/A')
                change_percent = fluctuation_data.get('changePercent', 'N/A')
                
                # 判断涨跌
                if isinstance(change, (int, float)):
                    trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                else:
                    trend = "❓"
                
                print(f"{trend} {symbol}:")
                print(f"  起始价格: {start_rate}")
                print(f"  结束价格: {end_rate}")
                print(f"  变化量: {change}")
                print(f"  变化率: {change_percent}%")
            
            return data
        
        return None
    
    def create_price_dataframe(self, timeseries_data: Dict, symbol: str) -> Optional[pd.DataFrame]:
        """
        将时间序列数据转换为DataFrame
        
        Args:
            timeseries_data: 时间序列API响应数据
            symbol: 商品符号
            
        Returns:
            pandas DataFrame
        """
        try:
            rates = timeseries_data.get('rates', {}).get(symbol, {})
            
            if not rates:
                print(f"❌ 没有找到 {symbol} 的数据")
                return None
            
            # 转换为DataFrame
            data_list = []
            for date, price_data in rates.items():
                row = {
                    'date': pd.to_datetime(date),
                    'open': price_data.get('open'),
                    'high': price_data.get('high'),
                    'low': price_data.get('low'),
                    'close': price_data.get('close')
                }
                data_list.append(row)
            
            df = pd.DataFrame(data_list)
            df = df.sort_values('date')
            df = df.set_index('date')
            
            print(f"✅ {symbol} DataFrame创建成功: {len(df)} 行数据")
            return df
            
        except Exception as e:
            print(f"❌ DataFrame创建失败: {e}")
            return None

# ===== 实际使用示例 =====

def demo_commodity_api():
    """演示完整的API使用流程"""
    
    print("🚀 Commodity Price API 演示")
    print("=" * 60)
    
    # 你的API密钥
    API_KEY = "15f8909b-e4ae-48f0-adc8-4dfa89725992"
    
    # 创建客户端
    client = CommodityPriceAPIClient(API_KEY)
    
    # 1. 检查API状态
    print("\n1️⃣ 检查API状态和使用情况")
    if not client.check_api_status():
        return
    
    # 2. 获取支持的商品符号
    print("\n2️⃣ 获取支持的商品符号")
    symbols_data = client.get_supported_symbols()
    
    # 3. 获取热门商品的最新价格
    print("\n3️⃣ 获取热门商品最新价格")
    popular_symbols = ['GOLD', 'SILVER', 'COPPER', 'CRUDE_OIL', 'NATURAL_GAS']
    latest_data = client.get_latest_prices(popular_symbols, quote_currency='USD')
    
    # 4. 获取黄金的历史价格
    print("\n4️⃣ 获取黄金历史价格")
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    historical_data = client.get_historical_prices(['GOLD'], yesterday)
    
    # 5. 获取过去一周的时间序列数据
    print("\n5️⃣ 获取过去一周的时间序列数据")
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    timeseries_data = client.get_timeseries(['GOLD', 'SILVER'], start_date, end_date)
    
    # 6. 分析价格波动
    print("\n6️⃣ 分析价格波动")
    fluctuation_data = client.get_fluctuation(['GOLD', 'SILVER'], start_date, end_date)
    
    # 7. 创建DataFrame进行数据分析
    print("\n7️⃣ 创建DataFrame进行数据分析")
    if timeseries_data:
        gold_df = client.create_price_dataframe(timeseries_data, 'GOLD')
        if gold_df is not None:
            print("📊 黄金价格统计:")
            print(f"  平均收盘价: {gold_df['close'].mean():.2f}")
            print(f"  最高价: {gold_df['high'].max():.2f}")
            print(f"  最低价: {gold_df['low'].min():.2f}")
            print(f"  价格波动率: {gold_df['close'].std():.2f}")
    
    print("\n✅ API演示完成!")

# ===== 与Chrome Headless集成的高级用法 =====

class CommodityDataDashboard:
    """结合Chrome Headless和Commodity API的高级仪表板"""
    
    def __init__(self, api_key: str):
        self.api_client = CommodityPriceAPIClient(api_key)
        self.chrome_controller = None  # 可以集成之前的Chrome控制器
    
    def generate_market_report(self, symbols: List[str], days: int = 7) -> Dict:
        """生成市场报告"""
        
        print(f"📋 生成市场报告: {', '.join(symbols)}")
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'period': f"{start_date} to {end_date}",
            'symbols': symbols,
            'latest_prices': {},
            'fluctuations': {},
            'summary': {}
        }
        
        # 获取最新价格
        latest_data = self.api_client.get_latest_prices(symbols)
        if latest_data:
            report['latest_prices'] = latest_data.get('rates', {})
        
        # 获取波动数据
        fluctuation_data = self.api_client.get_fluctuation(symbols, start_date, end_date)
        if fluctuation_data:
            report['fluctuations'] = fluctuation_data.get('rates', {})
        
        # 生成摘要
        summary = {}
        for symbol in symbols:
            if symbol in report['fluctuations']:
                change_percent = report['fluctuations'][symbol].get('changePercent', 0)
                if isinstance(change_percent, (int, float)):
                    if change_percent > 5:
                        summary[symbol] = "Strong Uptrend"
                    elif change_percent > 0:
                        summary[symbol] = "Uptrend"
                    elif change_percent < -5:
                        summary[symbol] = "Strong Downtrend"
                    elif change_percent < 0:
                        summary[symbol] = "Downtrend"
                    else:
                        summary[symbol] = "Stable"
        
        report['summary'] = summary
        
        return report
    
    def export_to_csv(self, timeseries_data: Dict, filename: str = None):
        """导出时间序列数据到CSV"""
        
        if filename is None:
            filename = f"commodity_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            all_data = []
            rates = timeseries_data.get('rates', {})
            
            for symbol, time_data in rates.items():
                for date, price_data in time_data.items():
                    row = {
                        'symbol': symbol,
                        'date': date,
                        'open': price_data.get('open'),
                        'high': price_data.get('high'),
                        'low': price_data.get('low'),
                        'close': price_data.get('close')
                    }
                    all_data.append(row)
            
            df = pd.DataFrame(all_data)
            df.to_csv(filename, index=False)
            
            print(f"✅ 数据已导出到: {filename}")
            print(f"📊 总共 {len(df)} 行数据")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")

# ===== 快速启动函数 =====

def quick_start():
    """快速开始使用API"""
    
    print("⚡ Commodity Price API 快速开始")
    print("API密钥: 15f8909b-e4ae-48f0-adc8-4dfa89725992")
    print()
    
    # 创建客户端
    client = CommodityPriceAPIClient("15f8909b-e4ae-48f0-adc8-4dfa89725992")
    
    # 检查连接
    if client.check_api_status():
        print("\n🎯 API连接成功！你可以开始使用以下功能:")
        print("1. client.get_latest_prices(['GOLD', 'SILVER'])  # 获取最新价格")
        print("2. client.get_historical_prices(['GOLD'], '2024-01-01')  # 获取历史价格")
        print("3. client.get_timeseries(['GOLD'], '2024-01-01', '2024-01-07')  # 时间序列")
        print("4. client.get_fluctuation(['GOLD'], '2024-01-01', '2024-01-07')  # 价格波动")
        
        return client
    else:
        print("\n❌ API连接失败，请检查密钥")
        return None

if __name__ == "__main__":
    # 运行演示
    demo_commodity_api()
    
    # 或者使用快速开始
    # client = quick_start()