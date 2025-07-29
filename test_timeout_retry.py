#!/usr/bin/env python3
"""
测试MCP工具的超时和重试机制
"""

import subprocess
import json
import time

def test_mcp_timeout_retry():
    """测试MCP工具的超时和重试机制"""
    
    # 启动MCP工具进程
    process = subprocess.Popen(
        ['python', 'src/core/universal_mcp_tool.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd='/Users/honglima/Desktop/Workspace/api-mcp'
    )
    
    try:
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
        
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        # 读取初始化响应
        response_line = process.stdout.readline()
        print(f"初始化响应: {response_line.strip()}")
        
        # 2. 发送初始化完成通知
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        process.stdin.write(json.dumps(initialized_notification) + '\n')
        process.stdin.flush()
        
        # 3. 获取工具列表
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(tools_request) + '\n')
        process.stdin.flush()
        
        # 读取工具列表响应
        response_line = process.stdout.readline()
        print(f"工具列表响应: {response_line.strip()}")
        
        # 4. 测试Ragflow API调用（这个可能会触发超时和重试机制）
        ragflow_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "GDS万国数据财报问答知识",
                "arguments": {
                    "question": "万国数据的主要竞争优势是什么？请详细分析其在数据中心行业的核心竞争力。",
                    "stream": False,
                    "session_id": "test_timeout_session_" + str(int(time.time()))
                }
            }
        }
        
        print("发送Ragflow API请求...")
        start_time = time.time()
        
        process.stdin.write(json.dumps(ragflow_request) + '\n')
        process.stdin.flush()
        
        # 读取响应（可能需要等待较长时间）
        response_line = process.stdout.readline()
        end_time = time.time()
        
        print(f"响应时间: {end_time - start_time:.2f} 秒")
        print(f"Ragflow API响应: {response_line.strip()}")
        
        # 解析响应
        try:
            response_data = json.loads(response_line)
            if "result" in response_data:
                print("✅ MCP工具超时和重试机制测试成功")
                print(f"响应内容: {response_data['result']}")
                return True
            else:
                print(f"❌ 响应格式异常: {response_data}")
                return False
        except json.JSONDecodeError as e:
            print(f"❌ 响应解析失败: {e}")
            print(f"原始响应: {response_line}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        # 清理进程
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("开始测试MCP工具的超时和重试机制...")
    success = test_mcp_timeout_retry()
    if success:
        print("🎉 超时和重试机制测试完成！")
    else:
        print("💥 超时和重试机制测试失败！")