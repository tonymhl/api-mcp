#!/usr/bin/env python3
"""
测试修复后的MCP工具是否能正确调用Ragflow API
"""

import subprocess
import json
import time

def test_mcp_ragflow_api():
    """测试MCP工具调用Ragflow API"""
    print("=== 测试MCP工具调用Ragflow API ===")
    
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
        
        # 1. 发送初始化请求
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        init_json = json.dumps(init_request) + "\n"
        print(f"发送初始化请求: {init_json.strip()}")
        
        process.stdin.write(init_json)
        process.stdin.flush()
        
        # 读取初始化响应
        init_response = process.stdout.readline()
        print(f"初始化响应: {init_response.strip()}")
        
        # 2. 发送initialized通知
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        initialized_json = json.dumps(initialized_notification) + "\n"
        print(f"发送initialized通知: {initialized_json.strip()}")
        
        process.stdin.write(initialized_json)
        process.stdin.flush()
        
        # 3. 获取可用工具列表
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        tools_json = json.dumps(tools_request) + "\n"
        print(f"发送工具列表请求: {tools_json.strip()}")
        
        process.stdin.write(tools_json)
        process.stdin.flush()
        
        # 读取工具列表响应
        tools_response = process.stdout.readline()
        print(f"工具列表响应: {tools_response.strip()}")
        
        # 4. 调用Ragflow API
        api_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "GDS万国数据相关知识",
                "arguments": {
                    "question": "万国数据的经营策略",
                    "stream": False,
                    "session_id": "19af53fcebef44a297545b5edba1a9e1"
                }
            }
        }
        
        api_json = json.dumps(api_request) + "\n"
        print(f"发送API调用请求: {api_json.strip()}")
        
        process.stdin.write(api_json)
        process.stdin.flush()
        
        # 读取API调用响应
        api_response = process.stdout.readline()
        print(f"API调用响应: {api_response.strip()}")
        
        # 解析响应
        if api_response.strip():
            try:
                response = json.loads(api_response.strip())
                print(f"解析后的响应: {json.dumps(response, indent=2, ensure_ascii=False)}")
                
                if "result" in response and "content" in response["result"]:
                    content = response["result"]["content"]
                    if isinstance(content, list) and len(content) > 0:
                        text_content = content[0].get("text", "")
                        print(f"提取的答案: {text_content}")
                    else:
                        print(f"响应内容: {content}")
                elif "error" in response:
                    print(f"API调用出错: {response['error']}")
                else:
                    print("响应格式不符合预期")
                    
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
        
        # 关闭进程
        process.stdin.close()
        process.wait(timeout=5)
        
        return True
        
    except subprocess.TimeoutExpired:
        print("请求超时")
        process.kill()
        return False
    except Exception as e:
        print(f"测试过程中出错: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_ragflow_api()
    if success:
        print("\n✅ MCP工具测试完成！")
    else:
        print("\n❌ MCP工具测试失败！")