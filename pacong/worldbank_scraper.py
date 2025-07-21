import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 直接指向最新的月度价格数据Excel文件链接 (Pink Sheet)
# 注意：这个链接可能会随时间变化，需要定期检查更新
DATA_URL = "https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Historical-Data-Monthly.xlsx"

def download_and_parse_worldbank_data():
    """
    从世界银行网站下载最新的商品月度价格Excel文件，并用Pandas进行解析。
    """
    try:
        logger.info(f"正在从以下链接下载世界银行商品数据: {DATA_URL}")
        response = requests.get(DATA_URL, timeout=30)
        response.raise_for_status()  # 如果下载失败则抛出异常

        # 将下载内容直接读入Pandas
        # Excel文件通常有多个工作表(sheet)，我们需要先检查一下
        xls = pd.ExcelFile(response.content)
        logger.info(f"文件下载成功. 包含的工作表: {xls.sheet_names}")

        # 修正：直接读取 'Monthly Indices' 工作表，因为这才是指数数据的存放地
        sheet_name_to_read = 'Monthly Indices'
        
        if sheet_name_to_read not in xls.sheet_names:
            logger.error(f"错误：Excel文件中未找到名为 '{sheet_name_to_read}' 的工作表。")
            # 备选方案：如果 'Monthly Indices' 不存在，再尝试之前的逻辑
            for name in xls.sheet_names:
                if 'monthly' in name.lower() and 'indices' in name.lower():
                    sheet_name_to_read = name
                    break
            else: # 如果循环正常结束（没找到）
                 logger.error("也未能找到任何包含 'monthly' 和 'indices' 的工作表。")
                 return None

        # 读取数据，通常这类文件头部有一些说明性文字，需要跳过
        # 我们用 header=6 作为一个初始猜测值，这在很多报告中很常见
        df = pd.read_excel(xls, sheet_name=sheet_name_to_read, header=6)
        
        logger.info(f"成功将Excel数据从 '{sheet_name_to_read}' 工作表解析到DataFrame中。")

        # 数据清洗和处理
        # 我们可以筛选出'Energy'指数
        # 首先需要找到包含'Energy'的行, 修正：不区分大小写
        energy_index_data = df[df.iloc[:, 0].str.contains('Energy', na=False, case=False)]

        return energy_index_data

    except requests.exceptions.RequestException as e:
        logger.error(f"下载文件时发生错误: {e}")
        return None
    except Exception as e:
        logger.error(f"解析Excel文件时发生错误: {e}")
        return None

def main():
    """
    主函数：执行世界银行数据抓取、解析和保存。
    """
    logger.info("--- 开始从世界银行抓取商品价格指数 ---")
    
    data = download_and_parse_worldbank_data()

    if data is not None and not data.empty:
        logger.info("成功提取到能源价格指数数据。")
        print("\n--- 世界银行能源价格指数 ---")
        print(data.to_string())
        print("-----------------------------\n")

        # 保存到文件
        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = output_dir / f"worldbank_energy_index_{timestamp}.csv"
        data.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"数据已保存到: {csv_path}")

    else:
        logger.error("\n--- 未能从世界银行获取到能源价格指数数据 ---")


if __name__ == "__main__":
    main() 