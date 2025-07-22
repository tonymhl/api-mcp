#!/usr/bin/env python3
"""
Universal MCP Tool - 主启动脚本
支持多种启动模式：GUI、完整服务、单独服务
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Universal MCP Tool 启动器')
    parser.add_argument('--mode', choices=['gui', 'full', 'mcp', 'web', 'simple-web'], 
                       default='gui', help='启动模式')
    parser.add_argument('--port', type=int, default=5001, 
                       help='Web界面端口 (默认: 5001)')
    
    args = parser.parse_args()
    
    # 确保在项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("=" * 60)
    print("🎯 Universal MCP Tool - 万能MCP工具")
    print("=" * 60)
    
    if args.mode == 'gui':
        print("🖥️  启动GUI管理界面...")
        subprocess.run([sys.executable, 'src/web/universal_mcp_gui.py'])
        
    elif args.mode == 'full':
        print("🚀 启动完整服务 (MCP + Web界面)...")
        subprocess.run([sys.executable, 'scripts/start_services.py'])
        
    elif args.mode == 'mcp':
        print("🔧 启动MCP服务...")
        subprocess.run([sys.executable, 'src/core/mcp_pipe.py', 'src/core/universal_mcp_tool.py'])
        
    elif args.mode == 'web':
        print(f"🌐 启动Web界面 (端口: {args.port})...")
        os.environ['FLASK_PORT'] = str(args.port)
        try:
            # 尝试启动完整版知识库Web界面
            subprocess.run([sys.executable, 'src/web/knowledge_web.py'])
        except Exception as e:
            print(f"完整版Web界面启动失败: {e}")
            print("尝试启动简化版Web界面...")
            # 如果失败，启动简化版Web界面
            subprocess.run([sys.executable, 'src/web/simple_web.py'])
            
    elif args.mode == 'simple-web':
        print(f"🌐 启动简化版Web界面 (端口: {args.port})...")
        os.environ['FLASK_PORT'] = str(args.port)
        subprocess.run([sys.executable, 'src/web/simple_web.py'])

if __name__ == '__main__':
    main()