#!/usr/bin/env python3
"""
启动脚本 - 同时运行MCP服务和Web界面
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

def run_mcp_service():
    """运行MCP服务"""
    print("🚀 启动MCP服务...")
    try:
        # 运行MCP服务
        process = subprocess.Popen([
            sys.executable, 'src/core/mcp_pipe.py', 'src/core/universal_mcp_tool.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 监控输出
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[MCP] {line.strip()}")
        
        process.wait()
        
    except Exception as e:
        print(f"❌ MCP服务启动失败: {e}")

def run_web_interface():
    """运行Web界面"""
    print("🌐 启动Web界面...")
    try:
        # 等待一下让MCP服务先启动
        time.sleep(2)
        
        # 运行Web界面
        process = subprocess.Popen([
            # sys.executable, 'src/web/knowledge_web.py'
            sys.executable, 'src/web/simple_web.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 监控输出
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[WEB] {line.strip()}")
        
        process.wait()
        
    except Exception as e:
        print(f"❌ Web界面启动失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 知识库MCP工具启动器")
    print("=" * 60)
    
    # 检查依赖
    print("📋 检查依赖...")
    
    # 切换到项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    required_files = [
        'src/core/universal_mcp_tool.py',
        'src/knowledge/knowledge_base.py',
        'src/knowledge/knowledge_mcp_tool.py',
        'src/knowledge/document_uploader.py',
        'src/web/knowledge_web.py',
        'src/core/mcp_pipe.py',
        'src/core/config_manager.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return
    
    print("✅ 所有必要文件都存在")
    
    # 创建必要目录
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('src/web/templates', exist_ok=True)
    
    print("\n🔧 启动服务...")
    
    # 创建线程运行服务
    mcp_thread = threading.Thread(target=run_mcp_service, daemon=True)
    web_thread = threading.Thread(target=run_web_interface, daemon=True)
    
    try:
        # 启动MCP服务
        mcp_thread.start()
        
        # 启动Web界面
        web_thread.start()
        
        print("\n✅ 服务启动完成!")
        print("📱 MCP服务: 已连接到小智AI终端")
        print("🌐 Web界面: http://localhost:5000")
        print("\n按 Ctrl+C 停止服务...")
        
        # 等待线程
        while True:
            time.sleep(1)
            if not mcp_thread.is_alive() and not web_thread.is_alive():
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
        print("👋 再见!")

if __name__ == '__main__':
    main()