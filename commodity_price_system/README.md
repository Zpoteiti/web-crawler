# 商品价格报告生成系统

这是一个基于 Python 的商品价格监控和报告生成系统，支持实时获取商品价格数据并生成可视化报告。

## 功能特性

- 🔄 实时获取商品价格数据
- 📊 生成价格走势图表
- 📈 多商品价格对比
- 📋 汇总报告（CSV 和 HTML 格式）
- ⏰ 定时任务调度
- 💾 数据持久化存储
- 🚦 API 限流控制

## 支持的商品

- 贵金属：gold（黄金）、silver（白银）
- 能源：crude_oil（原油）、natural_gas（天然气）
- 农产品：wheat（小麦）、corn（玉米）、soybeans（大豆）
- 工业金属：copper（铜）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

1. 注册 API Ninjas 账户并获取 API 密钥：https://api.api-ninjas.com/
2. 修改 `config.py` 文件中的 `API_KEY`

```python
API_KEY = "your_actual_api_key_here"
```

## 快速开始

### 1. 基本使用

```python
from commodity_report_system import CommodityReportSystem

# 创建系统实例
system = CommodityReportSystem(
    api_key="your_api_key",
    commodities=['gold', 'silver', 'crude_oil']
)

# 收集数据
system.collect_current_prices()


# 生成报告
system.generate_reports()
```

### 2. 定时任务模式

```python
# 启动定时任务（每小时收集数据，每天8:00和18:00生成报告）
system.run_scheduled_tasks()
```

### 3. 运行示例

```bash
python example_usage.py
```

## 文件结构

```
commodity_price_system/
├── commodity_report_system.py  # 主系统文件
├── config.py                   # 配置文件
├── example_usage.py           # 使用示例
├── requirements.txt           # 依赖包
├── README.md                 # 说明文档
├── commodity_data.json       # 数据存储文件（自动生成）
└── reports/                  # 报告输出目录（自动生成）
    ├── *.csv                # CSV 格式报告
    ├── *.html               # HTML 格式报告和图表
    └── *_chart_*.html       # 价格走势图
```

## 生成的报告类型

1. **价格走势图**：单个商品的价格变化趋势
2. **对比图表**：多个商品的价格对比
3. **汇总报告**：包含当前价格、变化幅度、最高/最低价等信息

## 定时任务设置

默认调度计划：
- 数据收集：每小时执行一次
- 报告生成：每天 08:00 和 18:00

可在 `config.py` 中修改：

```python
REPORT_SCHEDULE_TIMES = ["08:00", "18:00"]
DATA_COLLECTION_INTERVAL_HOURS = 1
```

## API 限制

API Ninjas 免费版限制：
- 100 次/小时
- 系统自动进行限流控制

## 注意事项

1. 确保网络连接稳定
2. API 密钥保密，不要提交到版本控制
3. 定时任务模式会持续运行，按 Ctrl+C 停止
4. 数据文件会自动清理 30 天前的数据

## 错误处理

系统包含完善的错误处理机制：
- API 请求失败时会记录错误并跳过
- 数据文件损坏时会重新创建
- 网络问题时会自动重试

## 扩展功能

可以轻松扩展的功能：
- 添加更多商品类型
- 支持其他数据源 API
- 增加邮件通知功能
- 添加价格预警机制