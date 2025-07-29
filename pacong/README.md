# 🚀 Pacong 爬虫系统

**配置驱动的智能数据爬取系统** - 无需编程即可添加新数据源

## ⚡ 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行系统
python main.py

# 3. 查看结果
ls reports/
```

## 🎯 核心功能

- ✅ **内置4个数据源**：Business Insider、新浪财经、世界银行、CoinGecko
- ✅ **零代码扩展**：配置文件添加新网站
- ✅ **自动化处理**：数据清洗、验证、分类、去重
- ✅ **多格式输出**：CSV、Excel、控制台摘要

## 📝 添加新数据源

编辑 `config/settings.yaml`：

```yaml
simple_scrapers:
  my_api:
    enabled: true
    name: "我的API"
    urls: "https://api.example.com/data"
    method: "requests"
```

就这么简单！

## 🔧 常用命令

```bash
# 查看所有数据源
python main.py --list-scrapers

# 运行特定数据源
python main.py --scrapers business_insider

# 调试模式
python main.py --log-level DEBUG

# 测试通用爬虫
python main.py --scrapers simple_coingecko_test
```

## 📊 输出文件

运行后在 `reports/` 目录查看：
- 📄 `commodity_data_YYYYMMDD_HHMMSS.csv` - 数据表格
- 📈 `commodity_data_YYYYMMDD_HHMMSS.xlsx` - 详细报表

## 🔍 问题排查

**没有数据？** 使用调试模式：
```bash
python main.py --log-level DEBUG --scrapers your_scraper_name
```

**需要浏览器？** 改为selenium模式：
```yaml
your_scraper:
  method: "selenium"
```

## 📁 项目结构

```
pacong/
├── main.py              # 🚀 启动文件
├── config/settings.yaml # ⚙️ 配置文件（重要）
├── reports/             # 📊 输出目录
├── scrapers/            # 🕷️ 爬虫模块
├── core/                # 🔧 核心模块
└── requirements.txt     # 📦 依赖包
```

---

**🎯 让数据爬取变得简单！** 