#!/usr/bin/env python3

import os
os.environ["PYTHONIOENCODING"] = "utf-8"

"""
Simplified Universal MCP Tool - 简化版万能MCP工具
仅支持API调用功能的MCP服务器
"""

from fastmcp import FastMCP
import requests
import json
import logging
import sys
import io
import os
import time
from typing import Dict, Any, List, Optional, Union

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入模块
try:
    from src.core.config_manager import load_config
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    sys.path.insert(0, os.path.join(project_root, 'src'))
    from core.config_manager import load_config

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.FileHandler("universal_mcp.log", encoding='utf-8'),
                             logging.StreamHandler()])
logger = logging.getLogger('universal_mcp')

# DO NOT modify sys.stdout/sys.stderr here - let MCP handle it

class UniversalMCPTool:
    def __init__(self):
        self.mcp = FastMCP("universal_mcps")
        self.api_configs = []
        self.config = load_config()
        logger.info(f"配置加载完成，MCP端点: {self.config.get('MCP_ENDPOINT', '未设置')}")
        
        # 设置MCP环境变量
        self._setup_mcp_environment()
        
        self._load_api_configs()
        self._register_apis_as_tools()
    
    def _setup_mcp_environment(self):
        """设置MCP所需的环境变量"""
        # 确保MCP_ENDPOINT环境变量被正确设置
        mcp_endpoint = self.config.get("MCP_ENDPOINT")
        if mcp_endpoint:
            os.environ["MCP_ENDPOINT"] = mcp_endpoint
            logger.info(f"已设置MCP_ENDPOINT环境变量: {mcp_endpoint}")
        else:
            logger.error("未找到MCP_ENDPOINT配置，请先在GUI中配置")
            raise ValueError("MCP_ENDPOINT未配置")
    
    def _load_api_configs(self):
        """Load API configurations from file"""
        try:
            # 尝试从项目根目录加载
            api_config_path = os.path.join(project_root, 'data', 'api_configs.json')
            with open(api_config_path, 'r', encoding='utf-8') as f:
                self.api_configs = json.load(f)
                logger.info(f"从 {api_config_path} 加载了 {len(self.api_configs)} 个API配置")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"无法加载API配置: {e}")
            # 尝试从当前目录加载
            try:
                with open('api_configs.json', 'r', encoding='utf-8') as f:
                    self.api_configs = json.load(f)
                    logger.info(f"从当前目录加载了 {len(self.api_configs)} 个API配置")
            except (FileNotFoundError, json.JSONDecodeError):
                logger.warning("未找到API配置或格式无效")
                self.api_configs = []
    
    def _save_api_configs(self):
        """Save API configurations to file"""
        # 保存到项目根目录的data目录下
        api_config_path = os.path.join(project_root, 'data', 'api_configs.json')
        os.makedirs(os.path.dirname(api_config_path), exist_ok=True)
        
        with open(api_config_path, 'w', encoding='utf-8') as f:
            json.dump(self.api_configs, f, indent=2, ensure_ascii=False)
        logger.info(f"已保存 {len(self.api_configs)} 个API配置到 {api_config_path}")
    
    def add_api(self, api_name: str, api_url: str, method: str, 
                request_format: Dict[str, Any], response_format: Dict[str, Any],
                description: str):
        """Add a new API configuration"""
        api_config = {
            "api_name": api_name,
            "api_url": api_url,
            "method": method.upper(),
            "request_format": request_format,
            "response_format": response_format,
            "description": description
        }
        
        # Check if API with this name already exists
        for i, config in enumerate(self.api_configs):
            if config["api_name"] == api_name:
                # Update existing config
                self.api_configs[i] = api_config
                logger.info(f"Updated API configuration: {api_name}")
                self._save_api_configs()
                return True
        
        # Add new API config
        self.api_configs.append(api_config)
        logger.info(f"Added new API configuration: {api_name}")
        self._save_api_configs()
        return True
    
    def remove_api(self, api_name: str):
        """Remove an API configuration by name"""
        initial_length = len(self.api_configs)
        self.api_configs = [config for config in self.api_configs if config["api_name"] != api_name]
        
        if len(self.api_configs) < initial_length:
            logger.info(f"Removed API configuration: {api_name}")
            self._save_api_configs()
            return True
        else:
            logger.warning(f"API configuration not found: {api_name}")
            return False
    
    def list_apis(self):
        """List all registered API configurations"""
        return self.api_configs
    
    def _register_apis_as_tools(self):
        """Register all APIs as MCP tools"""
        for api_config in self.api_configs:
            self._register_single_api(api_config)
    
    def _register_single_api(self, api_config):
        """Register a single API as an MCP tool"""
        api_name = api_config["api_name"]
        api_url = api_config["api_url"]
        method = api_config["method"]
        request_format = api_config["request_format"]
        description = api_config["description"]
        
        # 获取headers配置
        headers_config = api_config.get("headers", {})
        
        # 获取response_extract_path配置
        response_extract_path = api_config.get("response_extract_path", None)
        
        # 获取request_format配置，用于提取默认参数值
        request_format = api_config.get("request_format", {})
        
        # 为每个API创建一个专门的函数，而不是使用动态签名
        # 这样FastMCP可以更好地处理参数验证
        
        if api_name == "日记":
            @self.mcp.tool()
            def 日记(content: str = "") -> Dict[str, Any]:
                """记录日记"""
                return self._call_api_with_retry(api_name, api_url, method, {"content": content}, headers_config, response_extract_path)
        
        elif api_name == "绕口令":
            @self.mcp.tool()
            def 绕口令(difficulty: str = "简单") -> Dict[str, Any]:
                """生成绕口令"""
                return self._call_api_with_retry(api_name, api_url, method, {"difficulty": difficulty}, headers_config, response_extract_path)
        
        elif api_name == "GDS万国数据相关知识":
            # 从配置中获取默认的session_id
            default_session_id = request_format.get("session_id", "")
            default_stream = request_format.get("stream", False)
            
            @self.mcp.tool()
            def GDS万国数据相关知识(question: str = "", stream: bool = None, session_id: str = None) -> Dict[str, Any]:
                """查询GDS万国数据相关知识"""
                # 使用配置中的默认值
                final_stream = stream if stream is not None else default_stream
                final_session_id = session_id if session_id is not None else "19af53fcebef44a297545b5edba1a9e1"
                
                return self._call_api_with_retry(api_name, api_url, method, {
                    "question": question, 
                    "stream": final_stream, 
                    "session_id": final_session_id
                }, headers_config, response_extract_path)
        
        elif api_name == "GDS万国数据财报问答知识":
            @self.mcp.tool()
            def GDS万国数据财报问答知识(question: str = "", stream: bool = False, session_id: str = "") -> Dict[str, Any]:
                """查询GDS万国数据财报问答知识"""
                return self._call_api_with_retry(api_name, api_url, method, {
                    "question": question, 
                    "stream": stream, 
                    "session_id": session_id
                }, headers_config, response_extract_path)
        
        else:
            # 对于其他API，使用通用的处理方式
            def create_api_function():
                def api_caller(**kwargs) -> Dict[str, Any]:
                    return self._call_api_with_retry(api_name, api_url, method, kwargs, headers_config, response_extract_path)
                
                # 设置函数名和文档
                function_name = api_name.replace(" ", "_").replace("-", "_").replace("（", "_").replace("）", "_")
                api_caller.__name__ = function_name
                api_caller.__doc__ = description
                return api_caller
            
            # 注册通用API函数
            generic_func = create_api_function()
            self.mcp.tool()(generic_func)
        
        logger.info(f"Registered API as tool: {api_name}")
    
    def _call_api_with_retry(self, api_name: str, api_url: str, method: str, request_params: Dict[str, Any], 
                           headers_config: Dict[str, str], response_extract_path: str = None) -> Dict[str, Any]:
        """统一的API调用方法，包含超时和重试机制"""
        logger.info(f"Calling API: {api_name} with params: {request_params}")
        try:
            # 准备请求参数
            headers = dict(headers_config)  # 复制配置的headers
            url = api_url
            
            logger.info(f"Final request params: {request_params}")
            logger.info(f"Final request headers: {headers}")
            
            # 智能超时设置：根据API类型和特征设置不同的超时时间
            timeout_seconds = 30  # 默认超时时间
            
            # 知识库问答类API需要更长的超时时间
            if any(keyword in api_name.lower() for keyword in ['知识', 'knowledge', 'qa', 'question', 'answer', 'chat', 'ragflow']):
                timeout_seconds = 120  # 知识库问答API：2分钟
                logger.info(f"Detected knowledge-based API, using extended timeout: {timeout_seconds}s")
            elif any(keyword in api_name.lower() for keyword in ['ai', 'gpt', 'llm', 'generate']):
                timeout_seconds = 90   # AI生成类API：1.5分钟
                logger.info(f"Detected AI generation API, using extended timeout: {timeout_seconds}s")
            elif method == "POST":
                timeout_seconds = 60   # POST请求通常比GET耗时更长
                logger.info(f"POST request detected, using extended timeout: {timeout_seconds}s")
            else:
                logger.info(f"Using default timeout: {timeout_seconds}s")
            
            # 添加重试机制，特别是对于可能因网络波动导致的超时
            max_retries = 2
            retry_count = 0
            last_exception = None
            
            while retry_count <= max_retries:
                try:
                    logger.info(f"Attempt {retry_count + 1}/{max_retries + 1} for API: {api_name}")
                    
                    # 发送请求
                    if method == "GET":
                        response = requests.get(
                            url, 
                            params=request_params, 
                            headers=headers, 
                            timeout=timeout_seconds
                        )
                    elif method == "POST":
                        response = requests.post(
                            url, 
                            json=request_params, 
                            headers=headers, 
                            timeout=timeout_seconds
                        )
                    else:
                        return {
                            "success": False,
                            "error": f"Unsupported method: {method}"
                        }
                    
                    response.raise_for_status()
                    result_data = response.json()
                    
                    logger.info(f"API call successful for {api_name} on attempt {retry_count + 1}")
                    
                    # 如果配置了response_extract_path，提取指定路径的数据
                    if response_extract_path:
                        try:
                            # 支持点号分隔的路径，如 "data.answer"
                            path_parts = response_extract_path.split('.')
                            extracted_data = result_data
                            for part in path_parts:
                                extracted_data = extracted_data[part]
                            
                            return {
                                "success": True,
                                "result": extracted_data,
                                "full_response": result_data,  # 保留完整响应以备调试
                                "api_name": api_name,
                                "timeout_used": timeout_seconds,
                                "attempts": retry_count + 1
                            }
                        except (KeyError, TypeError) as e:
                            logger.warning(f"Failed to extract path {response_extract_path}: {e}")
                            # 如果提取失败，返回完整响应
                            return {
                                "success": True,
                                "result": result_data,
                                "api_name": api_name,
                                "timeout_used": timeout_seconds,
                                "attempts": retry_count + 1
                            }
                    
                    return {
                        "success": True,
                        "result": result_data,
                        "api_name": api_name,
                        "timeout_used": timeout_seconds,
                        "attempts": retry_count + 1
                    }
                    
                except requests.exceptions.Timeout as e:
                    last_exception = e
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = 2 ** retry_count  # 指数退避：2, 4, 8秒
                        logger.warning(f"Timeout on attempt {retry_count}/{max_retries + 1} for {api_name}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed due to timeout for {api_name}")
                        return {
                            "success": False,
                            "error": f"API调用超时 (超过{timeout_seconds}秒)，已重试{max_retries}次仍然失败",
                            "error_type": "timeout",
                            "timeout_seconds": timeout_seconds,
                            "attempts": retry_count,
                            "api_name": api_name
                        }
                
                except requests.exceptions.RequestException as e:
                    # 对于非超时的网络错误，也进行有限重试
                    last_exception = e
                    if retry_count < max_retries and "Connection" in str(e):
                        retry_count += 1
                        wait_time = 1 + retry_count  # 线性退避：2, 3秒
                        logger.warning(f"Connection error on attempt {retry_count}/{max_retries + 1} for {api_name}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Request error for {api_name}: {str(e)}")
                        return {
                            "success": False,
                            "error": f"网络请求失败: {str(e)}",
                            "error_type": "request_error",
                            "api_name": api_name,
                            "attempts": retry_count + 1
                        }
            
            # 如果所有重试都失败了
            return {
                "success": False,
                "error": f"API调用失败，已重试{max_retries}次: {str(last_exception)}",
                "error_type": "max_retries_exceeded",
                "api_name": api_name,
                "attempts": retry_count
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in API call for {api_name}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"API调用过程中发生意外错误: {str(e)}",
                "error_type": "unexpected_error",
                "api_name": api_name
            }
    
    def reload_apis(self):
        """Reload APIs from configuration file and register them as tools"""
        self._load_api_configs()
        self._register_apis_as_tools()
        return True
    
    def run(self):
        """Run the MCP server"""
        # Register management tools
        @self.mcp.tool()
        def register_api(api_name: str, api_url: str, method: str, 
                      request_format: str, response_format: str,
                      description: str, api_key: str = "", 
                      key_location: str = "header", 
                      key_name: str = "Authorization") -> Dict[str, Any]:
            """
            Register a new API as an MCP tool
            :param api_name: Name of the API (will be the tool name)
            :param api_url: URL of the API endpoint
            :param method: HTTP method (GET or POST)
            :param request_format: JSON string describing request format
            :param response_format: JSON string describing response format
            :param description: Description of the API
            :param api_key: Optional API key for authentication
            :param key_location: Where to put the API key (header, query, body)
            :param key_name: Name of the API key parameter
            :return: Success status
            """
            try:
                req_format = json.loads(request_format)
                resp_format = json.loads(response_format)
                
                # 创建API配置
                api_config = {
                    "api_name": api_name,
                    "api_url": api_url,
                    "method": method,
                    "request_format": req_format,
                    "response_format": resp_format,
                    "description": description
                }
                
                # 如果提供了API密钥，添加到配置中
                if api_key:
                    api_config["api_key"] = api_key
                    api_config["key_location"] = key_location
                    api_config["key_name"] = key_name
                
                # 添加或更新API
                result = True
                for i, config in enumerate(self.api_configs):
                    if config["api_name"] == api_name:
                        self.api_configs[i] = api_config
                        self._save_api_configs()
                        break
                else:
                    self.api_configs.append(api_config)
                    self._save_api_configs()
                
                # Reload APIs to register the new one
                self.reload_apis()
                
                return {
                    "success": True,
                    "message": f"API {api_name} registered successfully"
                }
            except Exception as e:
                logger.error(f"Error registering API: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp.tool()
        def list_registered_apis() -> Dict[str, Any]:
            """
            List all registered APIs
            :return: List of registered APIs
            """
            apis = self.list_apis()
            return {
                "success": True,
                "apis": apis
            }
        
        @self.mcp.tool()
        def remove_registered_api(api_name: str) -> Dict[str, Any]:
            """
            Remove a registered API
            :param api_name: Name of the API to remove
            :return: Success status
            """
            result = self.remove_api(api_name)
            # Reload APIs to update registered tools
            self.reload_apis()
            return {
                "success": result,
                "message": f"API {api_name} removed successfully" if result else f"API {api_name} not found"
            }
        
        # Start the MCP server
        logger.info("Starting Universal MCP Tool server")
        logger.info(f"Using MCP_ENDPOINT: {os.environ.get('MCP_ENDPOINT', 'Not set')}")
        try:
            self.mcp.run(transport="stdio")
        except Exception as e:
            logger.error(f"启动MCP服务失败: {str(e)}", exc_info=True)
            raise

    def test_api(self, api_name, api_url, method, params):
        import requests
        try:
            if method.lower() == 'get':
                response = requests.get(api_url, params=params)
            elif method.lower() == 'post':
                response = requests.post(api_url, json=params)
            else:
                raise ValueError('Unsupported method: {}'.format(method))

            # Check if the response is valid
            if response.status_code == 200:
                print(f'API {api_name} is available. Response: {response.json()}')
            else:
                print(f'API {api_name} returned an error: {response.status_code} - {response.text}')
        except Exception as e:
            print(f'Failed to test API {api_name}: {str(e)}')

if __name__ == "__main__":
    logger.debug("Main block started")
    try:
        logger.info("=== 启动 Universal MCP Tool ===")
        tool = UniversalMCPTool()
        tool.run()
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}", exc_info=True)
        input("按Enter退出...")
        sys.exit(1)
    finally:
        logger.debug("Main block ended")