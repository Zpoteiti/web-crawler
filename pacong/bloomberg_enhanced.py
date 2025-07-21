#!/usr/bin/env python3
"""
Bloomberg 商品数据爬虫增强版
使用AppleScript控制Chrome，包含中文翻译和美观的表格展示功能
"""

import subprocess
import time
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BloombergEnhancedScraper:
    def __init__(self):
        self.url = "https://www.bloomberg.com/markets/commodities"
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)
        
        # Bloomberg商品代码中文翻译对照表
        self.bloomberg_translations = {
            # 商品指数
            'BCOMTR:IND': '彭博商品指数',
            'CMCITR:IND': 'UBS彭博CMCI指数',
            'CRYTR:IND': '路透/杰富瑞CRB指数',
            'RICIGLTR:IND': '罗杰斯国际商品指数',
            'SPGSCITR:IND': '标普GSCI指数',
            
            # 能源
            'CL1:COM': 'WTI原油期货',
            'CO1:COM': '布伦特原油期货',
            'XB1:COM': 'RBOB汽油期货',
            'NG1:COM': '天然气期货',
            'HO1:COM': '取暖油期货',
            
            # 贵金属
            'GC1:COM': '黄金期货',
            'XAUUSD:CUR': '黄金现货',
            'SI1:COM': '白银期货',
            'HG1:COM': '铜期货',
            'XPTUSD:CUR': '铂金现货',
            'XPDUSD:CUR': '钯金现货',
            
            # 农产品
            'C 1:COM': '玉米期货',
            'W 1:COM': '小麦期货',
            'CC1:COM': '可可期货',
            'CT1:COM': '棉花期货',
            'LC1:COM': '活牛期货',
            'S 1:COM': '大豆期货',
            'SB1:COM': '糖期货',
            'KC1:COM': '咖啡期货',
            'LH1:COM': '瘦肉猪期货',
            'FC1:COM': '饲料牛期货',
        }
        
        # 商品分类
        self.bloomberg_categories = {
            '商品指数': ['彭博商品指数', 'UBS彭博CMCI指数', '路透/杰富瑞CRB指数', '罗杰斯国际商品指数', '标普GSCI指数'],
            '能源': ['WTI原油期货', '布伦特原油期货', 'RBOB汽油期货', '天然气期货', '取暖油期货'],
            '贵金属': ['黄金期货', '黄金现货', '白银期货', '铂金现货', '钯金现货'],
            '工业金属': ['铜期货'],
            '农产品': ['玉米期货', '小麦期货', '可可期货', '棉花期货', '活牛期货', '大豆期货', '糖期货', '咖啡期货', '瘦肉猪期货', '饲料牛期货']
        }

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

    def scrape_bloomberg_data(self):
        """使用AppleScript控制Chrome爬取Bloomberg数据"""
        try:
            logger.info("🚀 启动Bloomberg数据爬取...")
            
            # 1. 打开URL
            logger.info(f"正在使用Chrome打开: {self.url}")
            open_script = f'tell application "Google Chrome" to open location "{self.url}"'
            self.execute_applescript(open_script)

            # 2. 调整窗口大小（最小化干扰）
            time.sleep(2)
            logger.info("调整Chrome窗口大小...")
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
                logger.info("窗口大小调整完成")
            except Exception as e:
                logger.warning(f"窗口调整失败，继续使用默认窗口: {e}")

            # 3. 等待页面加载
            wait_seconds = 15
            logger.info(f"等待页面加载 ({wait_seconds}秒)...")
            time.sleep(wait_seconds)

            # 4. 滚动页面加载所有数据
            logger.info("滚动页面加载完整数据...")
            try:
                scroll_iterations = 5
                for i in range(scroll_iterations):
                    scroll_script = 'tell application "Google Chrome" to execute active tab of front window javascript "window.scrollBy(0, window.innerHeight);"'
                    self.execute_applescript(scroll_script)
                    logger.info(f"第 {i+1}/{scroll_iterations} 次滚动完成")
                    time.sleep(2)

                logger.info("再等待5秒确保数据加载完毕...")
                time.sleep(5)

            except Exception as e:
                logger.warning(f"滚动失败，可能只获取到部分数据: {e}")

            # 5. 获取页面HTML
            logger.info("获取页面HTML内容...")
            get_html_script = 'tell application "Google Chrome" to execute active tab of front window javascript "document.documentElement.outerHTML"'
            html_content = self.execute_applescript(get_html_script)
            
            if not html_content:
                logger.error("未能获取到HTML内容")
                return []
            
            logger.info(f"成功获取 {len(html_content)} 字节的HTML内容")

            # 6. 解析HTML数据
            soup = BeautifulSoup(html_content, 'lxml')
            commodities = []

            # 查找价格单元格
            price_cells = soup.find_all('td', class_='data-table-row-cell', attrs={'data-type': 'value'})
            logger.info(f"找到 {len(price_cells)} 个价格单元格")

            for cell in price_cells:
                row = cell.find_parent('tr')
                if not row:
                    continue

                name_cell = row.find(['td', 'th'], class_='data-table-row-cell', attrs={'data-type': 'name'})
                price_span = cell.find('span', class_='data-table-row-cell__value')
                
                if not (name_cell and price_span):
                    continue
                
                try:
                    # 提取商品名称
                    name_div = name_cell.find('div', class_='data-table-row-cell__link-block')
                    symbol = name_div.get_text(strip=True) if name_div else name_cell.get_text(strip=True)
                    
                    # 提取价格
                    price_str = price_span.get_text(strip=True).replace(',', '')
                    price = float(price_str)

                    # 提取涨跌幅（改进版）
                    change_value = 0.0
                    change_percent = 0.0
                    
                    change_cells = row.find_all('td', class_=lambda c: c and 'data-table-row-cell' in c and ('better' in c or 'worse' in c))
                    
                    if len(change_cells) >= 2:
                        try:
                            change_val_span = change_cells[0].find('span', class_='data-table-row-cell__value')
                            if change_val_span:
                                change_val_str = change_val_span.get_text(strip=True)
                                change_value = float(change_val_str.replace('+', '').replace(',', ''))
                            
                            change_pct_span = change_cells[1].find('span', class_='data-table-row-cell__value')
                            if change_pct_span:
                                change_pct_str = change_pct_span.get_text(strip=True)
                                change_percent = float(change_pct_str.replace('%', '').replace('+', ''))
                        except (ValueError, AttributeError):
                            pass

                    if symbol and price is not None:
                        # 添加中文翻译
                        chinese_name = self.bloomberg_translations.get(symbol, symbol)
                        
                        # 确定商品类别
                        category = "其他"
                        for cat, items in self.bloomberg_categories.items():
                            if chinese_name in items:
                                category = cat
                                break
                        
                        commodities.append({
                            'symbol': symbol,
                            'chinese_name': chinese_name,
                            'category': category,
                            'price': price,
                            'change_value': change_value,
                            'change_percent': change_percent,
                            'source': 'Bloomberg (AppleScript)',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"解析数据行失败: {e}")
                    continue
            
            logger.info(f"✅ 成功提取 {len(commodities)} 条Bloomberg商品数据")
            return commodities

        except Exception as e:
            logger.error(f"Bloomberg数据爬取失败: {e}")
            return []

    def create_formatted_display(self, commodities):
        """创建格式化的数据展示"""
        if not commodities:
            print("❌ 没有可显示的数据")
            return
        
        print("\n" + "="*80)
        print("🏆 Bloomberg 商品价格实时数据")
        print("="*80)
        print(f"📅 更新时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        print(f"📊 数据来源: Bloomberg Markets")
        print(f"📈 商品总数: {len(commodities)} 个")
        
        # 按类别分组显示
        df = pd.DataFrame(commodities)
        
        for category in self.bloomberg_categories.keys():
            category_data = df[df['category'] == category]
            if not category_data.empty:
                print(f"\n📋 {category} ({len(category_data)}个)")
                print("-" * 70)
                
                # 创建显示表格
                display_data = []
                for _, row in category_data.iterrows():
                    change_emoji = "📈" if row['change_percent'] > 0 else "📉" if row['change_percent'] < 0 else "➡️"
                    display_data.append({
                        '商品': f"{row['chinese_name']} ({row['symbol']})",
                        '当前价格': f"${row['price']:.2f}" if row['price'] else "N/A",
                        '涨跌': f"{row['change_value']:+.2f}" if row['change_value'] else "N/A",
                        '涨跌幅': f"{row['change_percent']:+.2f}%" if row['change_percent'] else "N/A",
                        '趋势': change_emoji
                    })
                
                display_df = pd.DataFrame(display_data)
                print(display_df.to_string(index=False))
        
        # 统计信息
        print(f"\n📊 数据统计:")
        for category, count in df['category'].value_counts().items():
            print(f"   {category}: {count} 个商品")

    def save_to_files(self, commodities):
        """保存数据到多种格式"""
        if not commodities:
            return []
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_files = []
        
        df = pd.DataFrame(commodities)
        
        # 保存CSV文件
        csv_file = self.output_dir / f"bloomberg_enhanced_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        saved_files.append(csv_file)
        logger.info(f"CSV数据已保存: {csv_file}")
        
        # 保存Excel文件
        excel_file = self.output_dir / f"bloomberg_enhanced_{timestamp}.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 总表
            df.to_excel(writer, sheet_name='全部商品', index=False)
            
            # 分类表
            for category in self.bloomberg_categories.keys():
                category_data = df[df['category'] == category]
                if not category_data.empty:
                    category_data.to_excel(writer, sheet_name=category, index=False)
        
        saved_files.append(excel_file)
        logger.info(f"Excel数据已保存: {excel_file}")
        
        # 生成HTML报告
        html_file = self.create_html_report(commodities, timestamp)
        if html_file:
            saved_files.append(html_file)
        
        return saved_files

    def create_html_report(self, commodities, timestamp):
        """生成HTML报告"""
        try:
            df = pd.DataFrame(commodities)
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Bloomberg 商品价格报告</title>
                <style>
                    body {{
                        font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                        min-height: 100vh;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 20px;
                        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 2.5em;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }}
                    .content {{
                        padding: 30px;
                    }}
                    .summary {{
                        background: #ecf0f1;
                        padding: 20px;
                        border-radius: 10px;
                        margin-bottom: 30px;
                        border-left: 5px solid #3498db;
                    }}
                    .category-section {{
                        margin-bottom: 40px;
                    }}
                    .category-title {{
                        font-size: 1.5em;
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                        border-radius: 10px;
                        overflow: hidden;
                    }}
                    th {{
                        background: #3498db;
                        color: white;
                        padding: 15px;
                        text-align: left;
                        font-weight: bold;
                    }}
                    td {{
                        padding: 12px 15px;
                        border-bottom: 1px solid #eee;
                    }}
                    tr:hover {{
                        background-color: #f8f9fa;
                    }}
                    .price {{
                        font-weight: bold;
                        color: #2c3e50;
                    }}
                    .change-positive {{
                        color: #27ae60;
                        font-weight: bold;
                    }}
                    .change-negative {{
                        color: #e74c3c;
                        font-weight: bold;
                    }}
                    .change-neutral {{
                        color: #7f8c8d;
                    }}
                    .footer {{
                        text-align: center;
                        padding: 20px;
                        color: #7f8c8d;
                        border-top: 1px solid #eee;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🏆 Bloomberg 商品价格报告</h1>
                        <p>专业金融市场数据分析</p>
                    </div>
                    
                    <div class="content">
                        <div class="summary">
                            <h3>📊 报告摘要</h3>
                            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                            <p><strong>数据来源:</strong> Bloomberg Markets (通过AppleScript)</p>
                            <p><strong>商品总数:</strong> {len(commodities)} 个</p>
                            <p><strong>覆盖类别:</strong> {', '.join(self.bloomberg_categories.keys())}</p>
                        </div>
            """
            
            # 为每个类别生成表格
            for category in self.bloomberg_categories.keys():
                category_data = df[df['category'] == category]
                if not category_data.empty:
                    html_content += f"""
                        <div class="category-section">
                            <h2 class="category-title">{category} ({len(category_data)} 个商品)</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th>商品名称</th>
                                        <th>Bloomberg代码</th>
                                        <th>当前价格</th>
                                        <th>涨跌</th>
                                        <th>涨跌幅</th>
                                        <th>趋势</th>
                                    </tr>
                                </thead>
                                <tbody>
                    """
                    
                    for _, row in category_data.iterrows():
                        change_class = "change-neutral"
                        trend_emoji = "➡️"
                        
                        if row['change_percent'] > 0:
                            change_class = "change-positive"
                            trend_emoji = "📈"
                        elif row['change_percent'] < 0:
                            change_class = "change-negative"
                            trend_emoji = "📉"
                        
                        html_content += f"""
                            <tr>
                                <td><strong>{row['chinese_name']}</strong></td>
                                <td>{row['symbol']}</td>
                                <td class="price">${row['price']:.2f}</td>
                                <td class="{change_class}">{row['change_value']:+.2f}</td>
                                <td class="{change_class}">{row['change_percent']:+.2f}%</td>
                                <td>{trend_emoji}</td>
                            </tr>
                        """
                    
                    html_content += """
                                </tbody>
                            </table>
                        </div>
                    """
            
            html_content += f"""
                    </div>
                    
                    <div class="footer">
                        <p>📅 数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p>🔗 数据来源: <a href="{self.url}" target="_blank">Bloomberg Markets</a></p>
                        <p>🤖 获取方式: AppleScript + Chrome自动化</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_file = self.output_dir / f"bloomberg_report_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML报告已生成: {html_file}")
            return html_file
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            return None

    def run_enhanced_scraping(self):
        """运行增强版Bloomberg爬取"""
        print("🚀 启动Bloomberg增强版商品数据爬取")
        print("="*60)
        print("⚠️ 请确保Google Chrome浏览器正在运行")
        print()
        
        # 获取数据
        commodities = self.scrape_bloomberg_data()
        
        if commodities:
            # 格式化显示
            self.create_formatted_display(commodities)
            
            # 保存文件
            print(f"\n💾 正在保存数据文件...")
            saved_files = self.save_to_files(commodities)
            
            print(f"\n✅ Bloomberg数据爬取完成！")
            print(f"📊 获取商品数据: {len(commodities)} 条")
            print(f"💾 已保存文件:")
            for file_path in saved_files:
                print(f"   📄 {file_path}")
            
            return True
        else:
            print("❌ Bloomberg数据爬取失败")
            print("💡 请确保:")
            print("   1. Google Chrome浏览器正在运行")
            print("   2. 网络连接正常")
            print("   3. 具有Automation权限")
            return False

def main():
    """主函数"""
    scraper = BloombergEnhancedScraper()
    scraper.run_enhanced_scraping()

if __name__ == "__main__":
    main() 