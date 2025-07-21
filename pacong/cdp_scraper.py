import asyncio
import json
import requests
import websockets
import logging
import subprocess
import time
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def scrape_with_patience(url: str):
    """
    通过CDP连接到浏览器，耐心等待动态内容加载完毕后，获取最终页面HTML，并使用BeautifulSoup解析商品数据。
    """
    tab = None
    try:
        response = requests.put('http://localhost:9222/json/new')
        response.raise_for_status()
        tab = response.json()
        ws_url = tab['webSocketDebuggerUrl']
        
        logger.info(f"新标签页已创建. WebSocket URL: {ws_url}")
        
        async with websockets.connect(ws_url, max_size=None) as websocket:
            await websocket.send(json.dumps({"id": 1, "method": "Page.enable"}))
            await websocket.send(json.dumps({"id": 2, "method": "Runtime.enable"}))
            await websocket.recv() # ack 1
            await websocket.recv() # ack 2

            logger.info(f"正在导航到: {url}...")
            await websocket.send(json.dumps({"id": 3, "method": "Page.navigate", "params": {"url": url}}))

            load_event_received = False
            while not load_event_received:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    if data.get("method") == "Page.loadEventFired":
                        load_event_received = True
                        logger.info("页面初始加载事件已触发。")
                except asyncio.TimeoutError:
                    logger.warning("等待页面加载事件超时，但仍将继续...")
                    break
            
            # 核心改动：不再尝试点击，而是给予充分的等待时间
            wait_seconds = 15
            logger.info(f"页面加载完毕. 现在将耐心等待 {wait_seconds} 秒，让所有动态数据加载...")
            await asyncio.sleep(wait_seconds)

            logger.info("等待结束. 正在获取最终的页面HTML...")
            await websocket.send(json.dumps({
                "id": 4, "method": "Runtime.evaluate",
                "params": {"expression": "document.documentElement.outerHTML"}
            }))

            html_content = ""
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                if data.get('id') == 4 and 'result' in data:
                    html_content = data['result']['result'].get('value', '')
                    logger.info(f"成功获取到 {len(html_content)} 字节的最终HTML内容。")
                    break

            if not html_content:
                logger.error("未能获取到任何HTML内容。")
                return []
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'lxml')
            all_commodities = []

            price_cells = soup.find_all('td', class_='data-table-row-cell', attrs={'data-type': 'value'})
            logger.info(f"找到 {len(price_cells)} 个潜在的价格单元格。")

            for i, cell in enumerate(price_cells):
                row = cell.find_parent('tr')
                if not row:
                    logger.warning(f"第 {i+1} 个价格单元格没有找到父级 <tr>，跳过。")
                    continue

                logger.info(f"--- 正在处理第 {i+1} 行 ---")
                
                # 关键修正：同时查找 'td' 和 'th' 作为名称单元格
                name_cell = row.find(['td', 'th'], class_='data-table-row-cell', attrs={'data-type': 'name'})
                price_span = cell.find('span', class_='data-table-row-cell__value')
                
                if not name_cell:
                    logger.warning(f"第 {i+1} 行: 未找到名称单元格。行HTML: {row.prettify()}")
                    continue
                if not price_span:
                    logger.warning(f"第 {i+1} 行: 未找到价格span。行HTML: {row.prettify()}")
                    continue
                
                try:
                    name_div = name_cell.find('div', class_='data-table-row-cell__link-block')
                    name = name_div.get_text(strip=True) if name_div else name_cell.get_text(strip=True)
                    logger.info(f"第 {i+1} 行: 提取到名称 '{name}'")
                    
                    price_str = price_span.get_text(strip=True).replace(',', '')
                    logger.info(f"第 {i+1} 行: 提取到价格字符串 '{price_str}'")
                    price = float(price_str)
                    
                    change_cell = row.find('td', class_='data-table-row-cell', attrs={'data-type': 'percentChange'})
                    change_percent = 0.0
                    if change_cell:
                        change_span = change_cell.find('span', class_='data-table-row-cell__value')
                        if change_span:
                            change_str = change_span.get_text(strip=True).replace('%', '').replace('+', '')
                            change_percent = float(change_str)
                            logger.info(f"第 {i+1} 行: 提取到涨跌幅 {change_percent}%")

                    if name and price is not None:
                        all_commodities.append({
                            'name': name,
                            'price': price,
                            'change_percent': change_percent,
                            'source': 'bloomberg.com (HTML)',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        logger.info(f"第 {i+1} 行: 成功添加数据。")
                except (ValueError, TypeError) as e:
                    logger.error(f"第 {i+1} 行解析时发生错误: {e}", exc_info=True)
                    logger.error(f"问题行HTML: {row.prettify()}")
                    continue
            
            return all_commodities

    except Exception as e:
        logger.error(f"在抓取过程中发生严重错误: {e}", exc_info=True)
        return None
    finally:
        if tab and tab.get('id'):
            requests.get(f"http://localhost:9222/json/close/{tab['id']}")
            logger.info(f"已关闭标签页: {tab['id']}")


async def main():
    """
    主函数：启动一个有界面的Chrome，耐心等待页面加载数据，然后抓取并解析。
    """
    chrome_process = None
    temp_dir = tempfile.mkdtemp()
    
    try:
        command = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            # "--headless", # 关键改动：移除无头模式，以模拟真实用户浏览器
            "--remote-debugging-port=9222",
            f"--user-data-dir={temp_dir}"
        ]
        
        logger.info("正在启动无头Chrome...")
        chrome_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"无头Chrome已启动, PID: {chrome_process.pid}")

        max_wait_seconds = 15
        for i in range(max_wait_seconds):
            try:
                requests.put('http://localhost:9222/json/new', timeout=1)
                logger.info("Chrome调试端口已就绪。")
                break
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        else:
            raise RuntimeError(f"在 {max_wait_seconds} 秒内无法连接到Chrome调试端口。")

        target_url = "https://www.bloomberg.com/markets/commodities"
        logger.info(f"--- 开始“耐心”抓取: {target_url} ---")
        
        scraped_data = await scrape_with_patience(target_url)
        
        # 关键修正：检查是否为None，而不是检查列表是否为空
        if scraped_data is not None:
            logger.info(f"成功抓取并解析到 {len(scraped_data)} 条商品数据。")
            
            if scraped_data: # 仅当列表不为空时才打印和保存
                df = pd.DataFrame(scraped_data)
                print("\n--- 抓取到的商品数据 ---")
                print(df.to_string())
                print("--------------------------\n")

                output_dir = Path("reports")
                output_dir.mkdir(exist_ok=True)
                csv_path = output_dir / f"bloomberg_commodities_patience_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                logger.info(f"数据已保存到: {csv_path}")
            else:
                logger.warning("抓取过程成功，但在页面上未找到符合条件的数据行。")
        else:
            logger.error("\n--- 未能通过“耐心等待”策略获取到任何商品数据（抓取过程发生错误）。 ---")

    finally:
        if chrome_process:
            logger.info(f"正在终止Chrome进程 (PID: {chrome_process.pid})...")
            chrome_process.terminate()
            chrome_process.wait()
            logger.info("Chrome进程已终止。")
        
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
            logger.info(f"临时目录 {temp_dir} 已清理。")


if __name__ == "__main__":
    asyncio.run(main()) 