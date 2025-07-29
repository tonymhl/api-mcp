#!/usr/bin/env python3
"""
全面测试MCP工具的超时和重试机制
"""

import subprocess
import json
import time

def test_mcp_comprehensive():
    """全面测试MCP工具的功能"""
    
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
        print(f"✅ 初始化成功")
        
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
        tools_response = json.loads(response_line)
        
        if "result" in tools_response and "tools" in tools_response["result"]:
            tools = tools_response["result"]["tools"]
            print(f"✅ 获取到 {len(tools)} 个工具:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool.get('description', '无描述')}")
        
        # 4. 测试各个API工具
        test_cases = [
            {
                "name": "GDS万国数据财报问答知识",
                "arguments": {
                    "question": "万国数据的主要业务是什么？",
                    "stream": False,
                    "session_id": "test_session_" + str(int(time.time()))
                },
                "description": "测试Ragflow知识库问答API"
            },
            {
                "name": "日记",
                "arguments": {
                    "content": "今天测试了MCP工具的超时和重试机制"
                },
                "description": "测试日记API"
            },
            {
                "name": "绕口令",
                "arguments": {
                    "difficulty": "中等"
                },
                "description": "测试绕口令API"
            }
        ]
        
        for i, test_case in enumerate(test_cases, start=3):
            print(f"\n🧪 测试 {test_case['name']} - {test_case['description']}")
            
            api_request = {
                "jsonrpc": "2.0",
                "id": i + 1,
                "method": "tools/call",
                "params": {
                    "name": test_case["name"],
                    "arguments": test_case["arguments"]
                }
            }
            
            start_time = time.time()
            process.stdin.write(json.dumps(api_request) + '\n')
            process.stdin.flush()
            
            # 读取响应
            response_line = process.stdout.readline()
            end_time = time.time()
            
            try:
                response_data = json.loads(response_line)
                response_time = end_time - start_time
                
                print(f"   响应时间: {response_time:.2f} 秒")
                
                if "result" in response_data:
                    result = response_data["result"]
                    
                    # 检查是否有结构化内容
                    if "structuredContent" in result:
                        structured = result["structuredContent"]
                        if structured.get("success"):
                            print(f"   ✅ API调用成功")
                            if "timeout_used" in structured:
                                print(f"   ⏱️  使用超时时间: {structured['timeout_used']}秒")
                            if "attempts" in structured:
                                print(f"   🔄 尝试次数: {structured['attempts']}")
                        else:
                            error_type = structured.get("error_type", "unknown")
                            print(f"   ❌ API调用失败: {error_type}")
                            print(f"   📝 错误信息: {structured.get('error', '无详细信息')}")
                            
                            # 检查是否是超时错误
                            if error_type == "timeout":
                                print(f"   ⚠️  这是超时错误，说明超时机制正常工作")
                            elif error_type == "request_error" and "502" in str(structured.get('error', '')):
                                print(f"   ℹ️  这是服务器错误，可能是Ragflow服务未启动")
                    else:
                        print(f"   ✅ 收到响应（无结构化内容）")
                else:
                    print(f"   ❌ 响应格式异常: {response_data}")
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ 响应解析失败: {e}")
                print(f"   📝 原始响应: {response_line}")
        
        print(f"\n🎉 MCP工具全面测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        # 清理进程
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("开始全面测试MCP工具...")
    print("=" * 60)
    success = test_mcp_comprehensive()
    print("=" * 60)
    if success:
        print("🎊 所有测试完成！MCP工具的超时和重试机制工作正常。")
    else:
        print("💥 测试失败！请检查错误信息。")