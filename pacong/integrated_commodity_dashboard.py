#!/usr/bin/env python3
"""
集成商品价格仪表板
结合Chrome Headless和Commodity Price API，创建完整的数据获取和分析系统
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time
import subprocess
import threading
import websocket
from typing import Dict, List, Optional, Union
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class IntegratedCommodityDashboard:
    def __init__(self, api_key: str, chrome_debug_port: int = 9222):
        """
        初始化集成商品价格仪表板
        
        Args:
            api_key: Commodity Price API密钥
            chrome_debug_port: Chrome调试端口
        """
        self.api_key = api_key
        self.chrome_debug_port = chrome_debug_port
        self.base_url = "https://api.commoditypriceapi.com/v2"
        self.chrome_base_url = f"http://localhost:{chrome_debug_port}"
        
        # 创建数据存储目录
        self.data_dir = Path("commodity_data")
        self.data_dir.mkdir(exist_ok=True)
        
        print(f"📊 商品价格仪表板初始化完成")
        print(f"🔑 API密钥: {api_key}")
        print(f"🌐 Chrome端口: {chrome_debug_port}")
        print(f"📁 数据目录: {self.data_dir}")
    
    def check_systems_status(self) -> Dict[str, bool]:
        """检查所有系统状态"""
        
        status = {
            'commodity_api': False,
            'chrome_headless': False
        }
        
        print("🔍 检查系统状态...")
        
        # 检查Commodity API
        try:
            response = requests.get(
                f"{self.base_url}/usage",
                params={"apiKey": self.api_key},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print("✅ Commodity API连接成功")
                print(f"  📊 计划: {data.get('plan', 'Unknown')}")
                print(f"  📈 配额: {data.get('quota', 'Unknown')}")
                print(f"  📉 已使用: {data.get('used', 'Unknown')}")
                status['commodity_api'] = True
            else:
                print(f"❌ Commodity API连接失败: {response.status_code}")
        except Exception as e:
            print(f"❌ Commodity API异常: {e}")
        
        # 检查Chrome Headless
        try:
            response = requests.get(f"{self.chrome_base_url}/json/version", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Chrome Headless连接成功")
                print(f"  🌐 浏览器: {data.get('Browser', 'Unknown')}")
                status['chrome_headless'] = True
            else:
                print(f"❌ Chrome Headless连接失败: {response.status_code}")
        except Exception as e:
            print(f"❌ Chrome Headless异常: {e}")
        
        return status
    
    def start_chrome_headless(self) -> bool:
        """启动Chrome Headless"""
        
        print("🚀 启动Chrome Headless...")
        
        # 检查是否已经运行
        try:
            response = requests.get(f"{self.chrome_base_url}/json/version", timeout=5)
            if response.status_code == 200:
                print("✅ Chrome Headless已经在运行")
                return True
        except:
            pass
        
        # 启动Chrome Headless
        chrome_cmd = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "--headless",
            f"--remote-debugging-port={self.chrome_debug_port}",
            "--no-sandbox",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--user-data-dir=/tmp/chrome-commodity-dashboard"
        ]
        
        try:
            subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            
            # 验证启动
            response = requests.get(f"{self.chrome_base_url}/json/version", timeout=5)
            if response.status_code == 200:
                print("✅ Chrome Headless启动成功")
                return True
            else:
                print("❌ Chrome Headless启动失败")
                return False
        except Exception as e:
            print(f"❌ Chrome启动异常: {e}")
            return False
    
    def get_commodity_data(self, symbols: List[str], days: int = 30) -> Dict:
        """获取商品数据"""
        
        print(f"📊 获取商品数据: {', '.join(symbols)} (过去{days}天)")
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        data = {
            'symbols': symbols,
            'period': f"{start_date} to {end_date}",
            'latest_prices': {},
            'timeseries': {},
            'fluctuations': {},
            'analysis': {}
        }
        
        # 获取最新价格
        try:
            response = requests.get(
                f"{self.base_url}/latest",
                params={
                    "apiKey": self.api_key,
                    "symbols": ','.join(symbols)
                },
                timeout=15
            )
            
            if response.status_code == 200:
                latest_data = response.json()
                data['latest_prices'] = latest_data
                print("✅ 最新价格获取成功")
            else:
                print(f"❌ 最新价格获取失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 最新价格异常: {e}")
        
        # 获取时间序列数据
        try:
            response = requests.get(
                f"{self.base_url}/timeseries",
                params={
                    "apiKey": self.api_key,
                    "symbols": ','.join(symbols),
                    "startDate": start_date,
                    "endDate": end_date
                },
                timeout=15
            )
            
            if response.status_code == 200:
                timeseries_data = response.json()
                data['timeseries'] = timeseries_data
                print("✅ 时间序列数据获取成功")
            else:
                print(f"❌ 时间序列数据获取失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 时间序列数据异常: {e}")
        
        # 获取波动数据
        try:
            response = requests.get(
                f"{self.base_url}/fluctuation",
                params={
                    "apiKey": self.api_key,
                    "symbols": ','.join(symbols),
                    "startDate": start_date,
                    "endDate": end_date
                },
                timeout=15
            )
            
            if response.status_code == 200:
                fluctuation_data = response.json()
                data['fluctuations'] = fluctuation_data
                print("✅ 波动数据获取成功")
            else:
                print(f"❌ 波动数据获取失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 波动数据异常: {e}")
        
        # 生成分析
        data['analysis'] = self._analyze_commodity_data(data)
        
        return data
    
    def _analyze_commodity_data(self, data: Dict) -> Dict:
        """分析商品数据"""
        
        analysis = {
            'summary': {},
            'trends': {},
            'volatility': {},
            'recommendations': {}
        }
        
        # 分析波动数据
        fluctuations = data.get('fluctuations', {}).get('rates', {})
        
        for symbol, fluc_data in fluctuations.items():
            change_percent = fluc_data.get('changePercent', 0)
            
            if isinstance(change_percent, (int, float)):
                # 趋势分析
                if change_percent > 10:
                    trend = "Strong Uptrend 🚀"
                    recommendation = "Consider taking profits"
                elif change_percent > 0:
                    trend = "Uptrend 📈"
                    recommendation = "Monitor for continuation"
                elif change_percent < -10:
                    trend = "Strong Downtrend 📉"
                    recommendation = "Potential buying opportunity"
                elif change_percent < 0:
                    trend = "Downtrend 📉"
                    recommendation = "Wait for stabilization"
                else:
                    trend = "Stable ➡️"
                    recommendation = "Hold current position"
                
                analysis['trends'][symbol] = trend
                analysis['recommendations'][symbol] = recommendation
                
                # 波动率分类
                volatility = abs(change_percent)
                if volatility > 15:
                    vol_level = "Very High"
                elif volatility > 10:
                    vol_level = "High"
                elif volatility > 5:
                    vol_level = "Medium"
                else:
                    vol_level = "Low"
                
                analysis['volatility'][symbol] = vol_level
        
        return analysis
    
    def scrape_commodity_websites(self, urls: List[str]) -> Dict:
        """使用Chrome Headless爬取商品相关网站"""
        
        print(f"🕷️ 爬取商品相关网站: {len(urls)} 个URL")
        
        scraped_data = {}
        
        try:
            # 创建新标签页
            response = requests.post(f"{self.chrome_base_url}/json/new")
            if response.status_code != 200:
                print("❌ 创建标签页失败")
                return scraped_data
            
            tab_info = response.json()
            tab_id = tab_info['id']
            
            print(f"✅ 创建标签页: {tab_id}")
            
            for i, url in enumerate(urls):
                print(f"📄 爬取 {i+1}/{len(urls)}: {url}")
                
                # 导航到URL（简化版本，实际需要WebSocket实现）
                # 这里提供框架，具体实现需要结合之前的Chrome控制代码
                scraped_data[url] = {
                    'status': 'simulated',
                    'timestamp': datetime.now().isoformat(),
                    'note': '实际实现需要WebSocket导航和数据提取'
                }
                
                time.sleep(2)  # 避免请求过快
            
            # 关闭标签页
            requests.post(f"{self.chrome_base_url}/json/close/{tab_id}")
            print(f"🧹 清理标签页 {tab_id}")
            
        except Exception as e:
            print(f"❌ 爬取异常: {e}")
        
        return scraped_data
    
    def create_data_visualization(self, data: Dict, output_dir: str = None) -> List[str]:
        """创建数据可视化图表"""
        
        if output_dir is None:
            output_dir = self.data_dir / "charts"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        generated_charts = []
        
        print("📈 创建数据可视化图表...")
        
        # 设置图表样式
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        try:
            # 1. 最新价格对比图
            latest_data = data.get('latest_prices', {}).get('rates', {})
            if latest_data:
                symbols = list(latest_data.keys())
                prices = [latest_data[symbol].get('rate', 0) for symbol in symbols]
                
                plt.figure(figsize=(12, 8))
                bars = plt.bar(symbols, prices)
                plt.title('最新商品价格对比', fontsize=16, fontweight='bold')
                plt.xlabel('商品符号')
                plt.ylabel('价格 (USD)')
                plt.xticks(rotation=45)
                
                # 添加数值标签
                for bar, price in zip(bars, prices):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(prices)*0.01,
                            f'{price:.2f}', ha='center', va='bottom')
                
                plt.tight_layout()
                chart_path = output_dir / 'latest_prices.png'
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                generated_charts.append(str(chart_path))
                print(f"✅ 最新价格图表: {chart_path}")
            
            # 2. 价格趋势图
            timeseries_data = data.get('timeseries', {}).get('rates', {})
            if timeseries_data:
                plt.figure(figsize=(15, 10))
                
                for i, (symbol, time_data) in enumerate(timeseries_data.items()):
                    if isinstance(time_data, dict):
                        dates = []
                        prices = []
                        
                        for date, price_data in sorted(time_data.items()):
                            dates.append(pd.to_datetime(date))
                            prices.append(price_data.get('close', 0))
                        
                        plt.subplot(len(timeseries_data), 1, i+1)
                        plt.plot(dates, prices, marker='o', linewidth=2, markersize=4)
                        plt.title(f'{symbol} 价格趋势', fontweight='bold')
                        plt.xlabel('日期')
                        plt.ylabel('价格 (USD)')
                        plt.grid(True, alpha=0.3)
                        plt.xticks(rotation=45)
                
                plt.tight_layout()
                chart_path = output_dir / 'price_trends.png'
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                generated_charts.append(str(chart_path))
                print(f"✅ 价格趋势图表: {chart_path}")
            
            # 3. 波动分析图
            fluctuation_data = data.get('fluctuations', {}).get('rates', {})
            if fluctuation_data:
                symbols = list(fluctuation_data.keys())
                changes = [fluctuation_data[symbol].get('changePercent', 0) for symbol in symbols]
                
                plt.figure(figsize=(12, 8))
                colors = ['green' if x > 0 else 'red' for x in changes]
                bars = plt.bar(symbols, changes, color=colors, alpha=0.7)
                
                plt.title('商品价格波动分析 (%)', fontsize=16, fontweight='bold')
                plt.xlabel('商品符号')
                plt.ylabel('变化率 (%)')
                plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                plt.xticks(rotation=45)
                
                # 添加数值标签
                for bar, change in zip(bars, changes):
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2, 
                            height + (0.5 if height > 0 else -1),
                            f'{change:.1f}%', ha='center', 
                            va='bottom' if height > 0 else 'top')
                
                plt.tight_layout()
                chart_path = output_dir / 'fluctuation_analysis.png'
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                generated_charts.append(str(chart_path))
                print(f"✅ 波动分析图表: {chart_path}")
            
        except Exception as e:
            print(f"❌ 图表生成异常: {e}")
        
        return generated_charts
    
    def generate_html_report(self, data: Dict, charts: List[str]) -> str:
        """生成HTML报告"""
        
        print("📄 生成HTML报告...")
        
        report_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>商品价格分析报告</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                }}
                .summary {{
                    background: #ecf0f1;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .chart {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .chart img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #3498db;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                .timestamp {{
                    text-align: center;
                    color: #7f8c8d;
                    font-style: italic;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏆 商品价格分析报告</h1>
                
                <div class="summary">
                    <h2>📊 报告概要</h2>
                    <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>分析周期:</strong> {data.get('period', 'N/A')}</p>
                    <p><strong>商品数量:</strong> {len(data.get('symbols', []))}</p>
                    <p><strong>分析商品:</strong> {', '.join(data.get('symbols', []))}</p>
                </div>
        """
        
        # 添加最新价格表
        latest_data = data.get('latest_prices', {}).get('rates', {})
        if latest_data:
            report_html += """
                <h2>💰 最新价格</h2>
                <table>
                    <tr>
                        <th>商品符号</th>
                        <th>最新价格</th>
                        <th>计价单位</th>
                    </tr>
            """
            
            metadata = data.get('latest_prices', {}).get('metaData', {})
            for symbol, rate_info in latest_data.items():
                meta = metadata.get(symbol, {})
                rate = rate_info.get('rate', 'N/A')
                unit = meta.get('unit', 'Unknown')
                quote = meta.get('quote', 'USD')
                
                report_html += f"""
                    <tr>
                        <td>{symbol}</td>
                        <td>{rate}</td>
                        <td>{quote}/{unit}</td>
                    </tr>
                """
            
            report_html += "</table>"
        
        # 添加分析结果
        analysis = data.get('analysis', {})
        if analysis:
            report_html += """
                <h2>📈 趋势分析</h2>
                <table>
                    <tr>
                        <th>商品符号</th>
                        <th>趋势</th>
                        <th>波动性</th>
                        <th>建议</th>
                    </tr>
            """
            
            trends = analysis.get('trends', {})
            volatility = analysis.get('volatility', {})
            recommendations = analysis.get('recommendations', {})
            
            for symbol in data.get('symbols', []):
                trend = trends.get(symbol, 'N/A')
                vol = volatility.get(symbol, 'N/A')
                rec = recommendations.get(symbol, 'N/A')
                
                report_html += f"""
                    <tr>
                        <td>{symbol}</td>
                        <td>{trend}</td>
                        <td>{vol}</td>
                        <td>{rec}</td>
                    </tr>
                """
            
            report_html += "</table>"
        
        # 添加图表
        for chart_path in charts:
            chart_name = Path(chart_path).stem.replace('_', ' ').title()
            report_html += f"""
                <h2>📊 {chart_name}</h2>
                <div class="chart">
                    <img src="{chart_path}" alt="{chart_name}">
                </div>
            """
        
        report_html += """
                <div class="timestamp">
                    <p>📅 报告生成于 {timestamp}</p>
                    <p>🔑 数据来源: Commodity Price API</p>
                </div>
            </div>
        </body>
        </html>
        """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 保存HTML报告
        report_path = self.data_dir / f"commodity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        print(f"✅ HTML报告已生成: {report_path}")
        return str(report_path)
    
    def run_full_analysis(self, symbols: List[str], days: int = 30) -> str:
        """运行完整分析流程"""
        
        print("🚀 启动完整商品价格分析")
        print("=" * 60)
        
        # 1. 检查系统状态
        print("\n1️⃣ 检查系统状态")
        status = self.check_systems_status()
        
        if not status['commodity_api']:
            print("❌ Commodity API不可用，无法继续")
            return None
        
        if not status['chrome_headless']:
            print("⚠️ Chrome Headless不可用，将跳过网页爬取")
        
        # 2. 获取商品数据
        print("\n2️⃣ 获取商品数据")
        data = self.get_commodity_data(symbols, days)
        
        # 3. 创建可视化图表
        print("\n3️⃣ 创建可视化图表")
        charts = self.create_data_visualization(data)
        
        # 4. 生成HTML报告
        print("\n4️⃣ 生成HTML报告")
        report_path = self.generate_html_report(data, charts)
        
        # 5. 保存原始数据
        print("\n5️⃣ 保存原始数据")
        data_path = self.data_dir / f"raw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ 原始数据已保存: {data_path}")
        
        print("\n✅ 完整分析完成!")
        print(f"📄 报告文件: {report_path}")
        print(f"📊 图表数量: {len(charts)}")
        print(f"💾 数据文件: {data_path}")
        
        return report_path

# ===== 使用示例 =====

def main():
    """主函数演示"""
    
    # 你的API密钥
    API_KEY = "689cf612-8665-4ce8-b1af-3823908a07f6"
    
    # 创建仪表板
    dashboard = IntegratedCommodityDashboard(API_KEY)
    
    # 要分析的商品
    symbols = ['GOLD', 'SILVER', 'COPPER', 'CRUDE_OIL', 'NATURAL_GAS']
    
    # 运行完整分析
    report_path = dashboard.run_full_analysis(symbols, days=30)
    
    if report_path:
        print(f"\n🎉 分析完成！请查看报告: {report_path}")
    else:
        print("\n❌ 分析失败")

if __name__ == "__main__":
    main() 