# 综合商品数据分析系统

本项目提供了一个完整的解决方案，用于获取、分析和可视化来自 Commodity Price API 的商品数据。它集成了数据抓取、分析、报告生成和与 Chrome Headless 的交互。

## 解决方案包含

| 组件 | 描述 |
| --- | --- |
| **API测试脚本 (`api_test_script.py`)** | ✅ 快速验证API连接<br>✅ 测试基本功能<br>✅ 获取使用情况和配额信息 |
| **完整API客户端 (`commodity_price_system/`)** | ✅ 获取最新价格、历史数据、时间序列<br>✅ 价格波动分析<br>✅ DataFrame数据处理<br>✅ 130+种商品支持 |
| **集成仪表板 (`pacong/`)** | ✅ 结合Chrome Headless和API数据<br>✅ 自动生成可视化图表<br>✅ HTML报告生成<br>✅ 网页数据爬取集成 |

## 🚀 快速开始

### 1. 安装依赖
```bash
# 安装 commodity_price_system 所需依赖
pip install -r commodity_price_system/requirements.txt

# 安装 pacong (集成仪表板) 所需依赖
pip install -r pacong/requirements.txt
```

### 2. 测试API连接
在运行主程序之前，建议先测试您的API密钥是否有效。
```bash
python api_test_script.py
```
如果连接成功，您会看到您的账户配额信息。

### 3. 运行完整分析
这将获取数据，进行分析，并生成图表和HTML报告。
```bash
python pacong/integrated_commodity_dashboard.py
```

### 4. (可选) Chrome Headless 管理
*注意: 这些脚本需要根据您的操作系统和 Chrome 安装路径进行配置。*
```bash
# 启动 Chrome Headless (示例)
# ./oneclick_setup.sh

# 停止 Chrome Headless (示例)
# ./stop_chrome.sh
```

---

## 📊 主要功能

| 功能 | 描述 | 示例 |
| --- | --- | --- |
| **实时价格获取** | 130+种商品最新价格 | 黄金: $2,021.50/盎司 |
| **历史数据** | 1990年至今的历史价格 | 查看过去30天金价走势 |
| **趋势分析** | 价格波动和趋势判断 | 黄金强势上涨🚀 |
| **可视化** | 自动生成图表和报告 | PNG图表 + HTML报告 |
| **网页集成** | 结合Chrome获取更多数据 | 爬取相关金融网站 |


## 🎯 支持的商品类型

- **贵金属**: 黄金、白银、铂金、钯金
- **能源**: 原油、天然气、汽油
- **农产品**: 小麦、玉米、大豆、咖啡
- **工业金属**: 铜、铝、锌、镍
- **其他**: 130+种商品全覆盖

## 📈 输出示例

运行 `integrated_commodity_dashboard.py` 后会生成：

- **📄 HTML分析报告**: 位于 `commodity_data/` 目录，包含价格表、趋势图、投资建议。
- **📊 可视化图表**: 位于 `commodity_data/charts/` 目录，PNG格式。
- **💾 原始数据**: JSON格式，位于 `commodity_data/` 目录，便于进一步分析。

## 🔧 API端点概览 (Python示例)

以下是如何在您的代码中使用 `CommodityPriceAPIClient` 的示例。

```python
from commodity_price_system.commodity_api_client import CommodityPriceAPIClient

# 使用您的API密钥初始化客户端
# 建议将密钥存储在环境变量中，而不是硬编码
API_KEY = "15f8909b-e4ae-48f0-adc8-4dfa89725992" 
client = CommodityPriceAPIClient(API_KEY)

# 获取最新价格
latest_prices = client.get_latest_prices(['GOLD', 'SILVER'])
print(latest_prices)

# 获取历史价格  
historical_prices = client.get_historical_prices(['GOLD'], '2024-01-01')
print(historical_prices)

# 获取时间序列数据
timeseries_data = client.get_timeseries(['GOLD'], '2024-01-01', '2024-01-07')
print(timeseries_data)

# 获取价格波动
fluctuation_data = client.get_fluctuation(['GOLD'], '2024-01-01', '2024-01-07')
print(fluctuation_data)
``` 