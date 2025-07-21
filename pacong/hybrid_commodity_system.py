#!/usr/bin/env python3
"""
混合式商品数据获取系统
结合API调用和网页抓取，提供最全面的数据覆盖
"""

import requests
import json
import re
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import logging

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebScrapingDataSource:
    """
    网页抓取数据源
    使用Selenium驱动的无头浏览器进行数据抓取
    """
    
    def __init__(self):
        try:
            options = uc.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            self.driver.set_page_load_timeout(60) # 延长页面加载超时到60秒
        except WebDriverException as e:
            logger.error(f"初始化WebDriver失败: {e}")
            logger.error("请确保您的系统已安装Chrome浏览器。")
            self.driver = None

    def _get_page_source(self, url: str, wait_for_element: tuple = None) -> str:
        """获取页面源代码，并可选择等待特定元素加载完成"""
        if not self.driver:
            return ""
        try:
            self.driver.get(url)
            if wait_for_element:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(wait_for_element)
                )
            else:
                time.sleep(5) 
            return self.driver.page_source
        except TimeoutException:
            logger.error(f"等待元素 {wait_for_element} 超时。页面: {url}")
            return self.driver.page_source # 即使超时，也尝试返回已加载内容
        except Exception as e:
            logger.error(f"使用Selenium加载页面 {url} 失败: {e}")
            return ""

    def scrape_investing_com(self) -> list:
        """从Investing.com获取商品价格"""
        url = "https://www.investing.com/commodities/"
        logger.info(f"正在使用Selenium抓取: {url}")
        
        # 等待数据表格的容器出现
        html_content = self._get_page_source(url, wait_for_element=(By.CSS_SELECTOR, "table[data-test='commodities-table']"))
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        commodities = []
        
        table = soup.find('table', attrs={'data-test': 'commodities-table'})
        if not table:
            logger.warning("在Investing.com上未找到商品数据表。")
            return []

        rows = table.find_all('tr', attrs={'data-test': re.compile(r'row-')})
        for row in rows:
            try:
                name_cell = row.find('td', attrs={'data-test': 'cell-name'})
                price_cell = row.find('td', attrs={'data-test': 'cell-last'})
                change_cell = row.find('td', attrs={'data-test': 'cell-change_percentage'})

                if name_cell and price_cell and change_cell:
                    name = name_cell.get_text(strip=True)
                    price = float(price_cell.get_text(strip=True).replace(',', ''))
                    change_pct_text = change_cell.get_text(strip=True).replace('%', '')
                    change = float(change_pct_text)
                    
                    commodities.append({
                        'name': name,
                        'price': price,
                        'change': change,
                        'source': 'investing.com',
                        'timestamp': datetime.now()
                    })
            except (ValueError, AttributeError) as e:
                continue

        logger.info(f"从Investing.com获取了 {len(commodities)} 个商品价格")
        return commodities
    
    def scrape_yahoo_finance_commodities(self) -> list:
        """从Yahoo Finance获取商品数据"""
        commodities = []
        yahoo_symbols = {
            'GC=F': '黄金期货', 'SI=F': '白银期货', 'CL=F': 'WTI原油',
            'BZ=F': '布伦特原油', 'NG=F': '天然气', 'HG=F': '铜期货'
        }
        
        for symbol, name in yahoo_symbols.items():
            url = f"https://finance.yahoo.com/quote/{symbol}"
            logger.info(f"正在使用Selenium抓取: {url}")
            # 等待价格元素出现
            html_content = self._get_page_source(url, wait_for_element=(By.CSS_SELECTOR, f"fin-streamer[data-symbol='{symbol}']"))
            if not html_content:
                continue

            soup = BeautifulSoup(html_content, 'html.parser')
            
            try:
                # 使用更精确的选择器
                price_elem = soup.find('fin-streamer', {'data-symbol': symbol, 'data-field': 'regularMarketPrice'})
                change_elem = soup.find('fin-streamer', {'data-symbol': symbol, 'data-field': 'regularMarketChangePercent'})

                if price_elem and change_elem:
                    price = float(price_elem.get('value'))
                    change = float(change_elem.get('value'))
                    
                    commodities.append({
                        'name': name,
                        'symbol': symbol,
                        'price': price,
                        'change': change,
                        'source': 'yahoo.com',
                        'timestamp': datetime.now()
                    })
            except (ValueError, AttributeError, TypeError) as e:
                logger.warning(f"解析 {symbol} 数据失败: {e}")
                continue

        logger.info(f"从Yahoo Finance获取了 {len(commodities)} 个商品价格")
        return commodities

    def scrape_bloomberg_commodities(self) -> list:
        """从Bloomberg.com获取商品数据"""
        url = "https://www.bloomberg.com/markets/commodities"
        logger.info(f"正在使用Selenium抓取: {url}")
        # 等待表格容器出现
        html_content = self._get_page_source(url, wait_for_element=(By.XPATH, '//div[contains(@class, "table-container")]'))
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        commodities = []

        # Bloomberg的页面结构非常复杂，XPath是更好的选择
        # 注意：这个XPath是示例，可能随时失效
        try:
            # 直接从已经加载的soup对象中查找，而不是再次驱动driver
            table_container = soup.find('div', class_=re.compile(r"table-container"))
            if not table_container:
                logger.warning("在Bloomberg页面上未找到table-container。")
                return []
                
            rows = table_container.find_all('div', class_=re.compile(r"data-table-row"))
            for row in rows:
                cells = row.find_all('div', class_=re.compile(r"data-table-cell"))
                if len(cells) > 4:
                    name = cells[0].get_text(strip=True)
                    price_text = cells[1].get_text(strip=True)
                    change_text = cells[3].get_text(strip=True)

                    price = float(price_text.replace(',', ''))
                    change = float(change_text.replace('%', ''))
                    
                    if name and price:
                        commodities.append({
                            'name': name,
                            'price': price,
                            'change': change,
                            'source': 'bloomberg.com',
                            'timestamp': datetime.now()
                        })
        except Exception as e:
            logger.error(f"在Bloomberg页面上解析数据失败: {e}")

        logger.info(f"从Bloomberg获取了 {len(commodities)} 个商品价格")
        return commodities

    def close(self):
        """关闭WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver已关闭。")


class HybridCommoditySystem:
    """
    混合式商品数据系统
    通过网页抓取，提供全面的数据
    """
    
    def __init__(self):
        self.web_scraper = WebScrapingDataSource()
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)
    
    def collect_all_data(self) -> dict:
        """收集所有数据源的商品信息"""
        logger.info("🔍 开始收集多源商品数据...")
        
        all_data = {
            'web_data': [],
            'combined_data': [],
            'collection_time': datetime.now()
        }
        
        # 从网页抓取数据
        web_sources = [
            self.web_scraper.scrape_yahoo_finance_commodities,
            self.web_scraper.scrape_investing_com,
            self.web_scraper.scrape_bloomberg_commodities,
        ]
        
        for scraper_func in web_sources:
            try:
                scraped_data = scraper_func()
                all_data['web_data'].extend(scraped_data)
            except Exception as e:
                logger.error(f"网页抓取失败: {e}")
        
        # 合并和去重数据
        all_data['combined_data'] = self._merge_commodity_data(all_data['web_data'])
        
        logger.info(f"✅ 数据收集完成: 网页={len(all_data['web_data'])}, 合并后={len(all_data['combined_data'])}")
        
        return all_data
    
    def _merge_commodity_data(self, commodity_list: list) -> list:
        """合并和去重商品数据"""
        commodity_dict = {}
        
        for commodity in commodity_list:
            name = commodity['name'].lower()
            
            # 标准化商品名称
            name_mapping = {
                '黄金': 'gold',
                '黄金期货': 'gold',
                'gold futures': 'gold',
                '白银': 'silver',
                '白银期货': 'silver',
                'silver futures': 'silver',
                '原油': 'crude_oil',
                'wti原油': 'crude_oil',
                'crude oil': 'crude_oil',
                '天然气': 'natural_gas',
                'natural gas': 'natural_gas',
                '小麦': 'wheat',
                '小麦期货': 'wheat',
                'wheat futures': 'wheat',
                '玉米': 'corn',
                '玉米期货': 'corn',
                'corn futures': 'corn',
                '铜': 'copper',
                '铜期货': 'copper',
                'copper futures': 'copper',
            }
            
            standard_name = name_mapping.get(name, name)
            
            # 使用第一个抓取到的数据源
            if standard_name not in commodity_dict:
                commodity_dict[standard_name] = commodity
        
        return list(commodity_dict.values())
    
    def generate_comprehensive_report(self, data: dict) -> str:
        """生成综合数据报告"""
        report = []
        report.append("📊 混合式商品数据综合报告")
        report.append(f"🕐 生成时间: {data['collection_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        # 数据源统计
        report.append(f"\n📈 数据源统计:")
        report.append(f"   网页抓取: {len(data['web_data'])} 个原始条目")
        report.append(f"   合并后: {len(data['combined_data'])} 个独立商品")
        
        # 主要商品价格
        report.append(f"\n💰 主要商品价格:")
        report.append("-" * 50)
        report.append(f"{'商品':15} {'价格':>12} {'变化':>10} {'数据源':>15}")
        report.append("-" * 50)
        
        for commodity in sorted(data['combined_data'], key=lambda x: x['name']):
            name = commodity['name']
            price = commodity['price']
            change = commodity.get('change', 0)
            source = commodity['source']
            
            change_str = f"{change:+.2f}" if change != 0 else "N/A"
            trend = "↗️" if change > 0 else "↘️" if change < 0 else "➡️"
            
            report.append(f"{name:15} ${price:>11.2f} {change_str:>9} {source:>15} {trend}")
        
        # 数据质量分析
        web_count = len(data['web_data'])
        
        if web_count > 0:
            report.append(f"\n📊 数据质量分析:")
            report.append(f"   数据来源: Yahoo Finance, Investing.com, Bloomberg.com")
            report.append(f"   数据新鲜度: 实时 (抓取时)")
        
        return "\n".join(report)
    
    def create_comparison_chart(self, data: dict):
        """创建数据源对比图表"""
        if not data['combined_data']:
            return None
        
        # 准备数据
        commodities = data['combined_data']
        names = [c['name'] for c in commodities]
        prices = [c['price'] for c in commodities]
        sources = [c['source'] for c in commodities]
        changes = [c.get('change', 0) for c in commodities]
        
        # 创建图表
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=['商品当前价格', '价格变化'],
            vertical_spacing=0.1
        )
        
        # 价格柱状图
        fig.add_trace(
            go.Bar(
                x=names,
                y=prices,
                name='当前价格',
                marker_color='orange',
                text=[f"${p:.2f}" for p in prices],
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # 变化散点图
        change_colors = ['green' if c > 0 else 'red' if c < 0 else 'gray' for c in changes]
        
        fig.add_trace(
            go.Scatter(
                x=names,
                y=changes,
                mode='markers+text',
                name='价格变化',
                marker=dict(
                    size=10,
                    color=change_colors
                ),
                text=[f"{c:+.2f}" for c in changes],
                textposition='top center'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="混合式商品数据对比",
            height=800,
            template='plotly_white'
        )
        
        # 保存图表
        chart_file = self.output_dir / f"hybrid_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(chart_file)
        logger.info(f"对比图表已保存: {chart_file}")
        
        return chart_file
    
    def save_data_to_csv(self, data: dict):
        """保存数据到CSV文件"""
        if not data['combined_data']:
            return None
        
        df = pd.DataFrame(data['combined_data'])
        csv_file = self.output_dir / f"hybrid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f"数据已保存到CSV: {csv_file}")
        
        return csv_file
    
    def run_comprehensive_analysis(self):
        """运行综合分析"""
        logger.info("🚀 启动混合式商品数据分析系统")
        
        # 收集数据
        data = self.collect_all_data()
        
        # 生成报告
        report = self.generate_comprehensive_report(data)
        print(report)
        
        # 保存报告
        report_file = self.output_dir / f"hybrid_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 创建图表
        self.create_comparison_chart(data)
        
        # 保存CSV
        self.save_data_to_csv(data)
        
        logger.info(f"✅ 综合分析完成，文件保存在: {self.output_dir}")
        
        # 关闭浏览器驱动
        self.web_scraper.close()

        return data

def main():
    """主函数"""
    print("🎯 网页抓取商品数据系统")
    print("=" * 50)
    print("通过抓取多个网站，提供最全面的商品数据")
    print()
    
    # 创建系统
    system = HybridCommoditySystem()
    
    print("\n🚀 开始收集和分析数据...")
    
    # 运行分析
    try:
        data = system.run_comprehensive_analysis()
        
        print(f"\n🎉 分析完成!")
        print(f"📊 共获取 {len(data['combined_data'])} 个商品的数据")
        print(f"📁 报告文件保存在: {system.output_dir}")
        
    except Exception as e:
        logger.error(f"❌ 系统运行失败: {e}")

if __name__ == "__main__":
    main() 