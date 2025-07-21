#!/usr/bin/env python3
"""
整合商品数据爬虫
同时从Business Insider和Bloomberg获取数据，并整合到一个Excel文件中
"""

import requests
import subprocess
import time
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegratedCommoditiesScraper:
    def __init__(self):
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)
        
        # 商品名称映射，用于匹配不同网站的同一商品
        self.commodity_mapping = {
            # Business Insider -> Bloomberg
            'Gold': ['GC1:COM', 'XAUUSD:CUR'],
            'Silver': ['SI1:COM'],
            'Platinum': ['XPTUSD:CUR'],
            'Copper': ['HG1:COM'],
            'Oil (WTI)': ['CL1:COM'],
            'Oil (Brent)': ['CO1:COM'],
            'Natural Gas': ['NG1:COM'],
            'Natural Gas (Henry Hub)': ['NG1:COM'],
            'RBOB Gasoline': ['XB1:COM'],
            'Heating Oil': ['HO1:COM'],
            'Corn': ['C 1:COM'],
            'Wheat': ['W 1:COM'],
            'Cocoa': ['CC1:COM'],
            'Cotton': ['CT1:COM'],
            'Live Cattle': ['LC1:COM'],
        }
        
        # 中文名称统一对照
        self.chinese_names = {
            'Gold': '黄金',
            'Silver': '白银',
            'Platinum': '铂金',
            'Palladium': '钯金',
            'Copper': '铜',
            'Oil (WTI)': 'WTI原油',
            'Oil (Brent)': '布伦特原油',
            'Natural Gas': '天然气',
            'Natural Gas (Henry Hub)': '天然气',
            'RBOB Gasoline': 'RBOB汽油',
            'Heating Oil': '取暖油',
            'Corn': '玉米',
            'Wheat': '小麦',
            'Cocoa': '可可',
            'Cotton': '棉花',
            'Live Cattle': '活牛',
            'Coffee': '咖啡',
            'Sugar': '糖',
            'Lumber': '木材',
        }

    def scrape_business_insider(self):
        """爬取Business Insider数据"""
        logger.info("🔍 开始爬取Business Insider数据...")
        
        url = "https://markets.businessinsider.com/commodities"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                commodities = []
                
                tables = soup.find_all('table')
                logger.info(f"Business Insider: 发现 {len(tables)} 个数据表格")
                
                for table in tables:
                    rows = table.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            cell_texts = [cell.get_text(strip=True) for cell in cells]
                            
                            name = cell_texts[0]
                            if (name and len(name) > 2 and not name.isdigit() and
                                'commodity' not in name.lower() and 'price' not in name.lower()):
                                
                                price = None
                                change = None
                                
                                for text in cell_texts[1:]:
                                    if re.search(r'\d+\.?\d*', text) and price is None:
                                        price_match = re.search(r'(\d+,?\d*\.?\d*)', text.replace(',', ''))
                                        if price_match:
                                            try:
                                                price = float(price_match.group(1))
                                            except ValueError:
                                                continue
                                    
                                    if ('%' in text or '+' in text or '-' in text) and change is None:
                                        change = text
                                
                                if name and price is not None:
                                    commodities.append({
                                        'name': name,
                                        'chinese_name': self.chinese_names.get(name, name),
                                        'price': price,
                                        'change': change,
                                        'source': 'Business Insider',
                                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
                
                logger.info(f"✅ Business Insider: 成功获取 {len(commodities)} 条数据")
                return commodities
            else:
                logger.error(f"❌ Business Insider访问失败: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Business Insider爬取失败: {e}")
            return []

    def execute_applescript(self, script: str) -> str:
        """执行AppleScript脚本"""
        try:
            process = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            if process.stderr:
                logger.warning(f"AppleScript警告: {process.stderr}")
            return process.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"AppleScript执行失败: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"AppleScript异常: {e}")
            raise

    def scrape_bloomberg(self):
        """爬取Bloomberg数据"""
        logger.info("🔍 开始爬取Bloomberg数据...")
        
        bloomberg_translations = {
            'BCOMTR:IND': '彭博商品指数',
            'CMCITR:IND': 'UBS彭博CMCI指数',
            'CRYTR:IND': '路透/杰富瑞CRB指数',
            'RICIGLTR:IND': '罗杰斯国际商品指数',
            'SPGSCITR:IND': '标普GSCI指数',
            'CL1:COM': 'WTI原油期货',
            'CO1:COM': '布伦特原油期货',
            'XB1:COM': 'RBOB汽油期货',
            'NG1:COM': '天然气期货',
            'HO1:COM': '取暖油期货',
            'GC1:COM': '黄金期货',
            'XAUUSD:CUR': '黄金现货',
            'SI1:COM': '白银期货',
            'HG1:COM': '铜期货',
            'XPTUSD:CUR': '铂金现货',
            'C 1:COM': '玉米期货',
            'W 1:COM': '小麦期货',
            'CC1:COM': '可可期货',
            'CT1:COM': '棉花期货',
            'LC1:COM': '活牛期货',
        }
        
        try:
            url = "https://www.bloomberg.com/markets/commodities"
            
            # 使用AppleScript控制Chrome
            logger.info("使用Chrome打开Bloomberg页面...")
            open_script = f'tell application "Google Chrome" to open location "{url}"'
            self.execute_applescript(open_script)

            # 调整窗口大小
            time.sleep(2)
            try:
                resize_script = '''
                tell application "Finder" to get bounds of window of desktop
                set screenDimensions to the result
                set screenWidth to item 3 of screenDimensions
                set screenHeight to item 4 of screenDimensions
                
                tell application "Google Chrome"
                    activate
                    try
                        set bounds of front window to {screenWidth - 1, screenHeight - 1, screenWidth, screenHeight}
                    on error
                        set bounds of front window to {100, 100, 101, 101}
                    end try
                end tell
                '''
                self.execute_applescript(resize_script)
            except Exception as e:
                logger.warning(f"窗口调整失败: {e}")

            # 等待页面加载
            logger.info("等待Bloomberg页面加载...")
            time.sleep(15)

            # 滚动页面
            try:
                for i in range(3):  # 减少滚动次数以加快速度
                    scroll_script = 'tell application "Google Chrome" to execute active tab of front window javascript "window.scrollBy(0, window.innerHeight);"'
                    self.execute_applescript(scroll_script)
                    time.sleep(1)
                time.sleep(3)
            except Exception as e:
                logger.warning(f"滚动失败: {e}")

            # 获取页面HTML
            logger.info("获取Bloomberg页面内容...")
            get_html_script = 'tell application "Google Chrome" to execute active tab of front window javascript "document.documentElement.outerHTML"'
            html_content = self.execute_applescript(get_html_script)
            
            if not html_content:
                logger.error("未能获取Bloomberg HTML内容")
                return []

            # 解析数据
            soup = BeautifulSoup(html_content, 'lxml')
            commodities = []

            price_cells = soup.find_all('td', class_='data-table-row-cell', attrs={'data-type': 'value'})
            logger.info(f"Bloomberg: 找到 {len(price_cells)} 个价格单元格")

            for cell in price_cells:
                row = cell.find_parent('tr')
                if not row:
                    continue

                name_cell = row.find(['td', 'th'], class_='data-table-row-cell', attrs={'data-type': 'name'})
                price_span = cell.find('span', class_='data-table-row-cell__value')
                
                if not (name_cell and price_span):
                    continue
                
                try:
                    name_div = name_cell.find('div', class_='data-table-row-cell__link-block')
                    symbol = name_div.get_text(strip=True) if name_div else name_cell.get_text(strip=True)
                    
                    price_str = price_span.get_text(strip=True).replace(',', '')
                    price = float(price_str)

                    if symbol and price is not None:
                        chinese_name = bloomberg_translations.get(symbol, symbol)
                        
                        commodities.append({
                            'name': symbol,
                            'chinese_name': chinese_name,
                            'price': price,
                            'change': None,  # Bloomberg涨跌幅提取较复杂，暂时设为None
                            'source': 'Bloomberg',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                except (ValueError, TypeError, AttributeError) as e:
                    continue
            
            logger.info(f"✅ Bloomberg: 成功获取 {len(commodities)} 条数据")
            return commodities

        except Exception as e:
            logger.error(f"❌ Bloomberg爬取失败: {e}")
            return []

    def create_integrated_excel(self, bi_data, bloomberg_data):
        """创建整合的Excel报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_file = self.output_dir / f"integrated_commodities_{timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                
                # 工作表1: Business Insider数据
                if bi_data:
                    bi_df = pd.DataFrame(bi_data)
                    bi_df.to_excel(writer, sheet_name='Business Insider', index=False)
                    logger.info(f"Business Insider数据写入Excel: {len(bi_data)}条")
                
                # 工作表2: Bloomberg数据
                if bloomberg_data:
                    bloomberg_df = pd.DataFrame(bloomberg_data)
                    bloomberg_df.to_excel(writer, sheet_name='Bloomberg', index=False)
                    logger.info(f"Bloomberg数据写入Excel: {len(bloomberg_data)}条")
                
                # 工作表3: 数据对比
                comparison_data = self.create_comparison_data(bi_data, bloomberg_data)
                if comparison_data:
                    comparison_df = pd.DataFrame(comparison_data)
                    comparison_df.to_excel(writer, sheet_name='价格对比', index=False)
                    logger.info(f"价格对比数据写入Excel: {len(comparison_data)}条")
                
                # 工作表4: 汇总统计
                summary_data = self.create_summary_data(bi_data, bloomberg_data)
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='数据汇总', index=False)
                    logger.info("数据汇总写入Excel")
                
                # 工作表5: 合并数据
                merged_data = self.merge_all_data(bi_data, bloomberg_data)
                if merged_data:
                    merged_df = pd.DataFrame(merged_data)
                    merged_df.to_excel(writer, sheet_name='全部数据', index=False)
                    logger.info(f"全部数据写入Excel: {len(merged_data)}条")
            
            logger.info(f"✅ 整合Excel文件已生成: {excel_file}")
            return excel_file
            
        except Exception as e:
            logger.error(f"❌ 生成Excel文件失败: {e}")
            return None

    def create_comparison_data(self, bi_data, bloomberg_data):
        """创建价格对比数据"""
        comparison = []
        
        # 创建Bloomberg数据的快速查找字典
        bloomberg_dict = {}
        for item in bloomberg_data:
            bloomberg_dict[item['name']] = item
        
        # 遍历Business Insider数据，寻找可对比的Bloomberg数据
        for bi_item in bi_data:
            bi_name = bi_item['name']
            
            # 查找对应的Bloomberg商品
            bloomberg_matches = self.commodity_mapping.get(bi_name, [])
            
            for bloomberg_symbol in bloomberg_matches:
                if bloomberg_symbol in bloomberg_dict:
                    bloomberg_item = bloomberg_dict[bloomberg_symbol]
                    
                    # 计算价格差异
                    bi_price = bi_item['price']
                    bloomberg_price = bloomberg_item['price']
                    price_diff = bi_price - bloomberg_price
                    price_diff_percent = (price_diff / bloomberg_price * 100) if bloomberg_price != 0 else 0
                    
                    comparison.append({
                        '商品名称': self.chinese_names.get(bi_name, bi_name),
                        'Business Insider英文名': bi_name,
                        'Bloomberg代码': bloomberg_symbol,
                        'BI价格': bi_price,
                        'Bloomberg价格': bloomberg_price,
                        '价格差异': round(price_diff, 2),
                        '差异百分比': f"{price_diff_percent:.2f}%",
                        'BI涨跌幅': bi_item.get('change', 'N/A'),
                        'BI时间': bi_item['timestamp'],
                        'Bloomberg时间': bloomberg_item['timestamp']
                    })
                    break  # 找到第一个匹配就跳出
        
        return comparison

    def create_summary_data(self, bi_data, bloomberg_data):
        """创建汇总统计数据"""
        summary = [
            {'指标': '数据源', 'Business Insider': 'Business Insider', 'Bloomberg': 'Bloomberg'},
            {'指标': '数据条数', 'Business Insider': len(bi_data), 'Bloomberg': len(bloomberg_data)},
            {'指标': '数据获取时间', 'Business Insider': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Bloomberg': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {'指标': '爬取方式', 'Business Insider': 'HTTP请求', 'Bloomberg': 'AppleScript+Chrome'},
            {'指标': '数据完整性', 'Business Insider': '包含价格和涨跌幅', 'Bloomberg': '仅包含价格'},
            {'指标': '技术难度', 'Business Insider': '简单', 'Bloomberg': '复杂'},
            {'指标': '可对比商品数', 'Business Insider': '-', 'Bloomberg': str(len(self.create_comparison_data(bi_data, bloomberg_data)))},
        ]
        
        # 计算价格统计
        if bi_data:
            bi_prices = [item['price'] for item in bi_data]
            summary.extend([
                {'指标': 'BI平均价格', 'Business Insider': f"${np.mean(bi_prices):.2f}", 'Bloomberg': '-'},
                {'指标': 'BI最高价格', 'Business Insider': f"${max(bi_prices):.2f}", 'Bloomberg': '-'},
                {'指标': 'BI最低价格', 'Business Insider': f"${min(bi_prices):.2f}", 'Bloomberg': '-'},
            ])
        
        if bloomberg_data:
            bloomberg_prices = [item['price'] for item in bloomberg_data]
            summary.extend([
                {'指标': 'Bloomberg平均价格', 'Business Insider': '-', 'Bloomberg': f"${np.mean(bloomberg_prices):.2f}"},
                {'指标': 'Bloomberg最高价格', 'Business Insider': '-', 'Bloomberg': f"${max(bloomberg_prices):.2f}"},
                {'指标': 'Bloomberg最低价格', 'Business Insider': '-', 'Bloomberg': f"${min(bloomberg_prices):.2f}"},
            ])
        
        return summary

    def merge_all_data(self, bi_data, bloomberg_data):
        """合并所有数据"""
        merged = []
        
        # 添加Business Insider数据
        for item in bi_data:
            merged.append({
                '数据源': 'Business Insider',
                '商品名称': item['name'],
                '中文名称': item['chinese_name'],
                '价格': item['price'],
                '涨跌幅': item.get('change', 'N/A'),
                '时间戳': item['timestamp']
            })
        
        # 添加Bloomberg数据
        for item in bloomberg_data:
            merged.append({
                '数据源': 'Bloomberg',
                '商品名称': item['name'],
                '中文名称': item['chinese_name'],
                '价格': item['price'],
                '涨跌幅': item.get('change', 'N/A'),
                '时间戳': item['timestamp']
            })
        
        return merged

    def run_integrated_scraping(self):
        """运行整合爬取"""
        print("🚀 启动整合商品数据爬取系统")
        print("="*60)
        print("📊 将同时从Business Insider和Bloomberg获取数据")
        print("💾 并整合到一个Excel文件中进行对比分析")
        print()
        
        # 1. 爬取Business Insider数据
        print("1️⃣ 爬取Business Insider数据...")
        bi_data = self.scrape_business_insider()
        
        # 2. 爬取Bloomberg数据
        print("\n2️⃣ 爬取Bloomberg数据...")
        print("⚠️ 请确保Google Chrome浏览器正在运行")
        bloomberg_data = self.scrape_bloomberg()
        
        # 3. 生成整合Excel
        print("\n3️⃣ 生成整合Excel报告...")
        excel_file = self.create_integrated_excel(bi_data, bloomberg_data)
        
        # 4. 显示结果摘要
        print("\n" + "="*60)
        print("📊 数据爬取结果摘要")
        print("="*60)
        print(f"📈 Business Insider: {len(bi_data)} 条数据")
        print(f"📈 Bloomberg: {len(bloomberg_data)} 条数据")
        print(f"📊 总计: {len(bi_data) + len(bloomberg_data)} 条数据")
        
        if excel_file:
            print(f"\n✅ 整合Excel文件已生成: {excel_file}")
            print("\n📋 Excel包含以下工作表:")
            print("   1. Business Insider - BI原始数据")
            print("   2. Bloomberg - Bloomberg原始数据") 
            print("   3. 价格对比 - 相同商品价格对比")
            print("   4. 数据汇总 - 统计信息汇总")
            print("   5. 全部数据 - 所有数据合并")
            
            # 显示可对比的商品
            comparison_data = self.create_comparison_data(bi_data, bloomberg_data)
            if comparison_data:
                print(f"\n🔍 发现 {len(comparison_data)} 个可对比的商品:")
                for comp in comparison_data[:5]:  # 显示前5个
                    print(f"   • {comp['商品名称']}: BI ${comp['BI价格']:.2f} vs Bloomberg ${comp['Bloomberg价格']:.2f}")
            
            return True
        else:
            print("❌ Excel文件生成失败")
            return False

def main():
    """主函数"""
    scraper = IntegratedCommoditiesScraper()
    scraper.run_integrated_scraping()

if __name__ == "__main__":
    import re  # 添加缺失的import
    main() 