#!/usr/bin/env python3
"""
使用示例
"""

from commodity_report_system import CommodityReportSystem
import config

def example_basic_usage():
    """基本使用示例"""
    # 创建系统实例
    system = CommodityReportSystem(
        api_key=config.API_KEY,
        commodities=['gold', 'silver', 'crude_oil']
    )
    
    # 手动收集一次数据
    system.collect_current_prices()
    
    # 生成报告
    system.generate_reports()

def example_custom_commodities():
    """自定义商品列表示例"""
    custom_commodities = ['gold', 'silver', 'wheat', 'corn']
    
    system = CommodityReportSystem(
        api_key=config.API_KEY,
        commodities=custom_commodities
    )
    
    system.collect_current_prices()
    system.generate_reports()

def example_scheduled_run():
    """定时运行示例"""
    system = CommodityReportSystem(
        api_key=config.API_KEY,
        commodities=config.DEFAULT_COMMODITIES
    )
    
    # 启动定时任务（这会一直运行）
    system.run_scheduled_tasks()

if __name__ == "__main__":
    print("选择运行模式:")
    print("1. 基本使用（手动执行一次）")
    print("2. 自定义商品列表")
    print("3. 定时任务模式")
    
    choice = input("请输入选择 (1-3): ")
    
    if choice == "1":
        example_basic_usage()
    elif choice == "2":
        example_custom_commodities()
    elif choice == "3":
        example_scheduled_run()
    else:
        print("无效选择")