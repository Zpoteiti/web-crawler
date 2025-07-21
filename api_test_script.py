#!/usr/bin/env python3
"""
API Test Script
快速验证与Commodity Price API的连接并检查密钥状态。
"""

import requests
import os
import json

def test_api_connection(api_key: str):
    """
    测试API连接并打印状态。

    Args:
        api_key: 你的Commodity Price API密钥。
    """
    base_url = "https://api.commoditypriceapi.com/v2/latest"
    params = {
        'apiKey': api_key,
        'symbols': 'GOLD'
    }
    
    print(f"🔑 正在使用 API 密钥进行测试: ...{api_key[-4:]}")
    print(f"📡 正在连接到 API 端点: {base_url}")

    try:
        response = requests.get(base_url, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ API 连接成功!")
                print("-" * 30)
                print("数据获取成功，API 和密钥均有效。")
                print("示例数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print("-" * 30)
                return True
            else:
                error_info = data.get('error', {})
                error_code = error_info.get('code')
                error_message = error_info.get('info')
                print(f"❌ API 返回错误 (Code: {error_code}): {error_message}")
                return False
        else:
            print(f"❌ 连接失败，HTTP 状态码: {response.status_code}")
            try:
                error_data = response.json()
                print("--- API 返回的错误信息 ---")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
                print("-------------------------")
            except json.JSONDecodeError:
                print("无法解析返回的错误内容，原始响应:")
                print(response.text)
            return False

    except requests.exceptions.Timeout:
        print("❌ 连接超时: 请求花费时间过长。")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接异常: {e}")
        return False

if __name__ == "__main__":
    API_KEY = os.environ.get("COMMODITY_API_KEY", "689cf612-8665-4ce8-b1af-3823908a07f6")
    
    if API_KEY == "YOUR_API_KEY_HERE" or not API_KEY:
        print("🛑 请在脚本中或环境变量中设置您的API密钥。")
    else:
        test_api_connection(API_KEY) 