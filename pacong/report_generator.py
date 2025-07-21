from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义数据源和板块
SOURCE_FILE = Path("pacong/claude_bloomberg_source.html")
SECTIONS = {
    "📊 商品指数总览": 5,
    "⚡ 能源板块": 5,
    "🥇 金属板块": 5,
    "🌾 农产品板块": 5
}

def parse_and_format_report(file_path: Path) -> str:
    """
    解析本地的HTML文件，并生成格式化的文本报告。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'lxml')
        report_lines = []
        
        all_rows = soup.find_all('tr')
        row_counter = 0

        for title, count in SECTIONS.items():
            report_lines.append(f"\n{title}")
            report_lines.append("-" * (len(title) + 2))
            
            # 获取当前板块的行
            section_rows = all_rows[row_counter : row_counter + count]
            row_counter += count

            for row in section_rows:
                name_tag = row.find('th', attrs={'data-type': 'name'})
                value_tag = row.find('td', attrs={'data-type': 'value'})
                change_tag = row.find('td', attrs={'data-type': 'change'})
                pct_change_tag = row.find('td', attrs={'data-type': 'percentChange'})

                if not all([name_tag, value_tag, pct_change_tag]):
                    continue
                
                # 清洗数据
                name = name_tag.get_text(separator=" ", strip=True)
                price = value_tag.get_text(strip=True)
                pct_change_str = pct_change_tag.get_text(strip=True)
                
                try:
                    pct_change = float(pct_change_str.replace('%', '').replace('+', ''))
                    arrow = "↗️" if pct_change >= 0 else "↘️"
                except ValueError:
                    pct_change = 0.0
                    arrow = ""
                
                # 格式化输出行
                report_lines.append(f"{name}: {price} ({pct_change_str}) {arrow}")

        return "\n".join(report_lines)

    except FileNotFoundError:
        logger.error(f"源文件未找到: {file_path}")
        return None
    except Exception as e:
        logger.error(f"生成报告时发生错误: {e}")
        return None

def main():
    """
    主函数：执行报告生成流程。
    """
    logger.info(f"--- 从源文件 '{SOURCE_FILE}' 生成商品报告 ---")
    
    report_content = parse_and_format_report(SOURCE_FILE)

    if report_content:
        print(report_content)
        
        # 保存报告到文件
        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = output_dir / f"human_readable_report_{timestamp}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        logger.info(f"\n报告已成功保存到: {report_path}")
    else:
        logger.error("\n--- 未能生成报告 ---")

if __name__ == "__main__":
    main() 