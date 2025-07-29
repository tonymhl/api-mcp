#!/usr/bin/env python3
"""
测试Ragflow API配置的脚本
"""

import requests
import json

def test_ragflow_api():
    """测试Ragflow API调用"""
    
    # API配置
    url = "http://192.168.100.103/api/v1/chats/fa0a4cf26b6311f08c29a6065f182a90/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer ragflow-k4ZGJjYjg0NmI2NTExZjA4NDRmYTYwNj"
    }
    
    # 请求数据
    payload = {
        "question": "万国数据的经营策略",
        "stream": False,
        "session_id": "19af53fcebef44a297545b5edba1a9e1"
    }
    
    print("🧪 测试Ragflow API...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("-" * 50)
    
    try:
        # 发送POST请求
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 测试提取data.answer路径
            if "data" in result and "answer" in result["data"]:
                answer = result["data"]["answer"]
                print(f"\n📝 提取的答案: {answer}")
            else:
                print("⚠️ 未找到data.answer路径")
                
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误，请检查网络和API地址")
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")

if __name__ == "__main__":
    test_ragflow_api()