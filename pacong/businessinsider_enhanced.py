#!/usr/bin/env python3
"""
Business Insider 商品数据爬虫增强版
包含中文翻译和美观的表格展示功能
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BusinessInsiderEnhancedScraper:
    def __init__(self):
        self.url = "https://markets.businessinsider.com/commodities"
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)
        
        # 商品中文翻译对照表
        self.commodity_translations = {
            # 贵金属
            'Gold': '黄金',
            'Silver': '白银', 
            'Platinum': '铂金',
            'Palladium': '钯金',
            
            # 能源
            'Natural Gas': '天然气',
            'Natural Gas (Henry Hub)': '天然气(亨利中心)',
            'Heating Oil': '取暖油',
            'Coal': '煤炭',
            'RBOB Gasoline': 'RBOB汽油',
            'Oil (Brent)': '布伦特原油',
            'Oil (WTI)': 'WTI原油',
            'Crude Oil': '原油',
            
            # 工业金属
            'Aluminium': '铝',
            'Aluminum': '铝',
            'Lead': '铅',
            'Copper': '铜',
            'Nickel': '镍',
            'Zinc': '锌',
            'Tin': '锡',
            
            # 农产品
            'Cotton': '棉花',
            'Oats': '燕麦',
            'Lumber': '木材',
            'Coffee': '咖啡',
            'Cocoa': '可可',
            'Live Cattle': '活牛',
            'Lean Hog': '瘦肉猪',
            'Corn': '玉米',
            'Feeder Cattle': '饲料牛',
            'Milk': '牛奶',
            'Orange Juice': '橙汁',
            'Palm Oil': '棕榈油',
            'Rapeseed': '油菜籽',
            'Rice': '大米',
            'Soybean Meal': '豆粕',
            'Soybeans': '大豆',
            'Soybean Oil': '豆油',
            'Wheat': '小麦',
            'Sugar': '糖',
        }
        
        # 商品分类
        self.commodity_categories = {
            '贵金属': ['黄金', '白银', '铂金', '钯金'],
            '能源': ['天然气', '天然气(亨利中心)', '取暖油', '煤炭', 'RBOB汽油', '布伦特原油', 'WTI原油', '原油'],
            '工业金属': ['铝', '铅', '铜', '镍', '锌', '锡'],
            '农产品': ['棉花', '燕麦', '木材', '咖啡', '可可', '活牛', '瘦肉猪', '玉米', '饲料牛', '牛奶', '橙汁', '棕榈油', '油菜籽', '大米', '豆粕', '大豆', '豆油', '小麦', '糖']
        }

    def get_commodity_data(self):
        """获取商品数据"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        try:
            logger.info(f"正在获取Business Insider商品数据...")
            response = requests.get(self.url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                commodities = []
                
                # 查找表格数据
                tables = soup.find_all('table')
                logger.info(f"发现 {len(tables)} 个数据表格")
                
                for table in tables:
                    rows = table.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            cell_texts = [cell.get_text(strip=True) for cell in cells]
                            
                            # 提取商品名称
                            name = cell_texts[0]
                            if (name and len(name) > 2 and not name.isdigit() and
                                'commodity' not in name.lower() and 'price' not in name.lower()):
                                
                                # 提取价格和变化
                                price = None
                                change = None
                                unit = "USD"
                                
                                for text in cell_texts[1:]:
                                    # 解析价格
                                    if re.search(r'\d+\.?\d*', text) and price is None:
                                        price_match = re.search(r'(\d+,?\d*\.?\d*)', text.replace(',', ''))
                                        if price_match:
                                            try:
                                                price = float(price_match.group(1))
                                            except ValueError:
                                                continue
                                    
                                    # 解析变化百分比
                                    if ('%' in text or '+' in text or '-' in text) and change is None:
                                        change = text
                                
                                if name and price is not None:
                                    # 添加中文翻译
                                    chinese_name = self.commodity_translations.get(name, name)
                                    
                                    # 确定商品类别
                                    category = "其他"
                                    for cat, items in self.commodity_categories.items():
                                        if chinese_name in items:
                                            category = cat
                                            break
                                    
                                    commodities.append({
                                        'english_name': name,
                                        'chinese_name': chinese_name,
                                        'category': category,
                                        'price': price,
                                        'change': change,
                                        'unit': unit,
                                        'source': 'Business Insider',
                                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
                
                logger.info(f"成功获取 {len(commodities)} 条商品数据")
                return commodities
            else:
                logger.error(f"访问失败，状态码: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return []

    def create_formatted_display(self, commodities):
        """创建格式化的数据展示"""
        if not commodities:
            print("❌ 没有可显示的数据")
            return
        
        print("\n" + "="*80)
        print("🏆 Business Insider 商品价格实时数据")
        print("="*80)
        print(f"📅 更新时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        print(f"📊 数据来源: Business Insider")
        print(f"📈 商品总数: {len(commodities)} 个")
        
        # 按类别分组显示
        df = pd.DataFrame(commodities)
        
        for category in self.commodity_categories.keys():
            category_data = df[df['category'] == category]
            if not category_data.empty:
                print(f"\n📋 {category} ({len(category_data)}个)")
                print("-" * 70)
                
                # 创建显示表格
                display_data = []
                for _, row in category_data.iterrows():
                    change_emoji = "📈" if row['change'] and '+' in str(row['change']) else "📉" if row['change'] and '-' in str(row['change']) else "➡️"
                    display_data.append({
                        '商品': f"{row['chinese_name']} ({row['english_name']})",
                        '当前价格': f"${row['price']:.2f}" if row['price'] else "N/A",
                        '涨跌幅': f"{row['change']}" if row['change'] else "N/A",
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
        csv_file = self.output_dir / f"businessinsider_enhanced_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        saved_files.append(csv_file)
        logger.info(f"CSV数据已保存: {csv_file}")
        
        # 保存Excel文件
        excel_file = self.output_dir / f"businessinsider_enhanced_{timestamp}.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 总表
            df.to_excel(writer, sheet_name='全部商品', index=False)
            
            # 分类表
            for category in self.commodity_categories.keys():
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
                <title>Business Insider 商品价格报告</title>
                <style>
                    body {{
                        font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 10px;
                        margin-bottom: 30px;
                        border-left: 5px solid #667eea;
                    }}
                    .category-section {{
                        margin-bottom: 40px;
                    }}
                    .category-title {{
                        font-size: 1.5em;
                        color: #333;
                        border-bottom: 2px solid #667eea;
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
                        background: #667eea;
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
                        <h1>🏆 Business Insider 商品价格报告</h1>
                        <p>实时商品市场数据分析</p>
                    </div>
                    
                    <div class="content">
                        <div class="summary">
                            <h3>📊 报告摘要</h3>
                            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                            <p><strong>数据来源:</strong> Business Insider Markets</p>
                            <p><strong>商品总数:</strong> {len(commodities)} 个</p>
                            <p><strong>覆盖类别:</strong> {', '.join(self.commodity_categories.keys())}</p>
                        </div>
            """
            
            # 为每个类别生成表格
            for category in self.commodity_categories.keys():
                category_data = df[df['category'] == category]
                if not category_data.empty:
                    html_content += f"""
                        <div class="category-section">
                            <h2 class="category-title">{category} ({len(category_data)} 个商品)</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th>商品名称</th>
                                        <th>英文名称</th>
                                        <th>当前价格</th>
                                        <th>涨跌幅</th>
                                        <th>趋势</th>
                                    </tr>
                                </thead>
                                <tbody>
                    """
                    
                    for _, row in category_data.iterrows():
                        change_class = "change-neutral"
                        trend_emoji = "➡️"
                        
                        if row['change']:
                            if '+' in str(row['change']):
                                change_class = "change-positive"
                                trend_emoji = "📈"
                            elif '-' in str(row['change']):
                                change_class = "change-negative"
                                trend_emoji = "📉"
                        
                        html_content += f"""
                            <tr>
                                <td><strong>{row['chinese_name']}</strong></td>
                                <td>{row['english_name']}</td>
                                <td class="price">${row['price']:.2f}</td>
                                <td class="{change_class}">{row['change'] if row['change'] else 'N/A'}</td>
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
                        <p>🔗 数据来源: <a href="{self.url}" target="_blank">Business Insider Markets</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_file = self.output_dir / f"businessinsider_report_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML报告已生成: {html_file}")
            return html_file
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            return None

    def run_enhanced_scraping(self):
        """运行增强版爬取"""
        print("🚀 启动Business Insider增强版商品数据爬取")
        print("="*60)
        
        # 获取数据
        commodities = self.get_commodity_data()
        
        if commodities:
            # 格式化显示
            self.create_formatted_display(commodities)
            
            # 保存文件
            print(f"\n💾 正在保存数据文件...")
            saved_files = self.save_to_files(commodities)
            
            print(f"\n✅ 数据爬取完成！")
            print(f"📊 获取商品数据: {len(commodities)} 条")
            print(f"💾 已保存文件:")
            for file_path in saved_files:
                print(f"   📄 {file_path}")
            
            return True
        else:
            print("❌ 数据爬取失败")
            return False

def main():
    """主函数"""
    scraper = BusinessInsiderEnhancedScraper()
    scraper.run_enhanced_scraping()

if __name__ == "__main__":
    main() 