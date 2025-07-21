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

def execute_applescript(script: str) -> str:
    """
    执行一段AppleScript脚本并返回其输出。
    """
    try:
        # 使用subprocess来运行osascript命令
        process = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )
        if process.stderr:
            logger.warning(f"AppleScript a-t-il produit une erreur standard: {process.stderr}")
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"AppleScript a échoué avec une erreur de code de retour : {e.stderr}")
        # 检查常见的权限错误
        if '(-1743)' in e.stderr or 'not allowed assistive access' in e.stderr:
            logger.error("Erreur de permission : le contrôle de Chrome nécessite des autorisations d'automatisation.")
            logger.error("Pour accorder la permission, allez dans Paramètres Système > Confidentialité et sécurité > Automatisation, trouvez votre terminal ou éditeur de code, et cochez 'Google Chrome'.")
        # 检查Chrome是否正在运行
        elif '(-600)' in e.stderr or "application isn't running" in e.stderr:
            logger.error("Google Chrome n'est pas en cours d'exécution. Veuillez lancer Chrome et réessayer.")
        raise
    except Exception as e:
        logger.error(f"Une erreur inattendue est survenue lors de l'exécution d'AppleScript : {e}")
        raise

def scrape_with_applescript(url: str):
    """
    使用AppleScript控制一个已在运行的Chrome实例来抓取数据。
    """
    try:
        # 1. 打开URL
        logger.info(f"正在使用AppleScript在Chrome中打开URL: {url}")
        open_script = f'tell application "Google Chrome" to open location "{url}"'
        execute_applescript(open_script)

        # 新增步骤：等待窗口出现并将其变得几乎不可见
        time.sleep(2) # 给窗口一点时间来响应
        logger.info("尝试将Chrome窗口调整为1x1像素并移至屏幕角落...")
        try:
            # 这段AppleScript会获取屏幕尺寸，然后将窗口移动到右下角并变得非常小
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
                    -- 如果获取屏幕尺寸失败，使用一个固定的很小的尺寸
                    set bounds of front window to {100, 100, 101, 101}
                end try
            end tell
            '''
            execute_applescript(resize_script)
            logger.info("窗口大小已成功调整，对用户干扰更小。")
        except Exception as e:
            logger.warning(f"调整窗口大小失败，但这不影响抓取。将使用可见窗口。错误: {e}")

        # 2. 耐心等待页面加载
        wait_seconds = 15
        logger.info(f"URL已打开. 等待 {wait_seconds} 秒让页面完全加载...")
        time.sleep(wait_seconds)

        # 新增步骤：通过多次滚动来加载所有数据
        logger.info("正在通过多次滚动加载所有商品...")
        try:
            # 循环滚动5次，模拟用户浏览行为
            scroll_iterations = 5
            for i in range(scroll_iterations):
                scroll_script = 'tell application "Google Chrome" to execute active tab of front window javascript "window.scrollBy(0, window.innerHeight);"'
                execute_applescript(scroll_script)
                logger.info(f"第 {i+1}/{scroll_iterations} 次滚动...")
                time.sleep(2)  # 每次滚动后等待2秒

            logger.info("滚动完成，再等待5秒确保所有内容加载完毕。")
            time.sleep(5)

        except Exception as e:
            logger.warning(f"滚动页面失败，可能只会抓取到部分数据。错误: {e}")

        # 3. 执行JavaScript获取HTML内容
        logger.info("正在获取页面HTML内容...")
        get_html_script = 'tell application "Google Chrome" to execute active tab of front window javascript "document.documentElement.outerHTML"'
        html_content = execute_applescript(get_html_script)
        
        if not html_content:
            logger.error("未能获取到任何HTML内容。")
            return None
        
        logger.info(f"成功获取到 {len(html_content)} 字节的HTML。正在使用BeautifulSoup解析...")

        # 4. 使用BeautifulSoup解析
        soup = BeautifulSoup(html_content, 'lxml')
        all_commodities = []

        price_cells = soup.find_all('td', class_='data-table-row-cell', attrs={'data-type': 'value'})
        logger.info(f"找到 {len(price_cells)} 个潜在的价格单元格。")

        for cell in price_cells:
            row = cell.find_parent('tr')
            if not row: continue

            name_cell = row.find(['td', 'th'], class_='data-table-row-cell', attrs={'data-type': 'name'})
            price_span = cell.find('span', class_='data-table-row-cell__value')
            
            if not (name_cell and price_span): continue
            
            try:
                name_div = name_cell.find('div', class_='data-table-row-cell__link-block')
                name = name_div.get_text(strip=True) if name_div else name_cell.get_text(strip=True)
                
                price_str = price_span.get_text(strip=True).replace(',', '')
                price = float(price_str)

                # --- 新增：提取涨跌幅 ---
                change_value = 0.0
                change_percent = 0.0
                
                # 涨跌幅通常在 class 包含 'better' (涨) 或 'worse' (跌) 的单元格里
                change_cells = row.find_all('td', class_=lambda c: c and 'data-table-row-cell' in c and ('better' in c or 'worse' in c))
                
                # 结构通常是 [绝对值变化, 百分比变化]
                if len(change_cells) >= 2:
                    # 提取绝对值变化
                    change_val_span = change_cells[0].find('span', class_='data-table-row-cell__value')
                    if change_val_span:
                        change_val_str = change_val_span.get_text(strip=True)
                        change_value = float(change_val_str.replace('+', '').replace(',', ''))
                    
                    # 提取百分比变化
                    change_pct_span = change_cells[1].find('span', class_='data-table-row-cell__value')
                    if change_pct_span:
                        change_pct_str = change_pct_span.get_text(strip=True)
                        change_percent = float(change_pct_str.replace('%', '').replace('+', ''))

                if name and price is not None:
                    all_commodities.append({
                        'name': name,
                        'price': price,
                        'change_value': change_value,
                        'change_percent': change_percent,
                        'source': 'bloomberg.com (AppleScript)',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            except (ValueError, TypeError, IndexError) as e:
                logger.warning(f"解析某行数据时跳过，错误: {e}. 行: {row.get_text(separator=' | ', strip=True)}")
                continue
        
        return all_commodities

    except Exception as e:
        logger.error(f"抓取过程中发生错误: {e}")
        return None

def main():
    """
    主函数：执行基于AppleScript的抓取流程。
    """
    logger.info("--- 开始使用AppleScript控制Chrome进行抓取 ---")
    logger.info("请确保Google Chrome正在运行。")

    target_url = "https://www.bloomberg.com/markets/commodities"
    scraped_data = scrape_with_applescript(target_url)

    if scraped_data is not None:
        logger.info(f"成功抓取并解析到 {len(scraped_data)} 条商品数据。")
        if scraped_data:
            df = pd.DataFrame(scraped_data)
            print("\n--- 抓取到的商品数据 (AppleScript) ---")
            print(df.to_string())
            print("---------------------------------------\n")

            output_dir = Path("reports")
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_path = output_dir / f"bloomberg_commodities_applescript_{timestamp}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            logger.info(f"数据已保存到: {csv_path}")
        else:
            logger.warning("抓取过程成功，但在页面上未找到符合条件的数据行。")
    else:
        logger.error("\n--- AppleScript抓取策略失败 ---")

if __name__ == "__main__":
    main() 