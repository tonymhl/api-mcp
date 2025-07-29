#!/usr/bin/env python3
"""
简化的MCP工具测试脚本
"""

import subprocess
import json

def test_mcp_simple():
    """简化的MCP工具测试"""
    print("=== 简化的MCP工具测试 ===")
    
    try:
        # 启动MCP工具进程
        process = subprocess.Popen(
            ["python", "src/core/universal_mcp_tool.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/Users/honglima/Desktop/Workspace/api-mcp"
        )
        
        # 发送所有必要的请求
        requests = [
            # 1. 初始化
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                }
            },
            # 2. 初始化完成通知
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            },
            # 3. 获取工具列表
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            },
            # 4. 调用Ragflow API
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "GDS万国数据相关知识",
                    "arguments": {
                        "question": "万国数据的主要业务是什么？",
                        "stream": False,
                        "session_id": "19af53fcebef44a297545b5edba1a9e1"
                    }
                }
            }
        ]
        
        # 发送所有请求
        for i, req in enumerate(requests):
            req_json = json.dumps(req) + "\n"
            print(f"发送请求 {i+1}: {req.get('method', 'notification')}")
            process.stdin.write(req_json)
            process.stdin.flush()
            
            # 只读取有ID的请求的响应
            if "id" in req:
                response = process.stdout.readline()
                print(f"响应 {req['id']}: {response.strip()}")
                
                # 如果是API调用响应，解析并显示结果
                if req["id"] == 3:
                    try:
                        resp_data = json.loads(response.strip())
                        if "result" in resp_data:
                            result = resp_data["result"]
                            if "content" in result and isinstance(result["content"], list):
                                for content_item in result["content"]:
                                    if "text" in content_item:
                                        print(f"\n✅ API调用成功！")
                                        print(f"问题: 万国数据的主要业务是什么？")
                                        print(f"回答: {content_item['text'][:200]}...")
                                        break
                        elif "error" in resp_data:
                            print(f"❌ API调用失败: {resp_data['error']}")
                    except json.JSONDecodeError:
                        print("❌ 响应解析失败")
        
        # 关闭进程
        process.stdin.close()
        process.wait(timeout=5)
        
        return True
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_simple()
    if success:
        print("\n🎉 MCP工具测试完成！")
    else:
        print("\n💥 MCP工具测试失败！")