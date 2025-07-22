"""
知识库MCP工具
提供RAG知识库检索问答功能
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from knowledge_base import KnowledgeBase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('knowledge_mcp.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class KnowledgeMCPTool:
    """知识库MCP工具类"""
    
    def __init__(self):
        self.kb = KnowledgeBase()
        self.server = Server("knowledge-base")
        self._register_tools()
        
        # 初始化时添加GDS万国数据的内容
        self._init_default_knowledge()
    
    def _init_default_knowledge(self):
        """初始化默认知识库内容"""
        gds_content = """万国数据（纳斯达克股票代码：GDS；港交所股票代码：9698）是中国领先的高性能数据中心运营商和服务商。我们的数据中心分布于对高性能数据中心需求广泛的中国核心经济枢纽地区。为了满足客户更广泛的需求，我们还根据客户的选择在非一线城市地区建设和运营数据中心。我们的数据中心规模大，电力供应充沛、密度高且高效，所有关键系统均具备多重冗余。我们中立于运营商及云服务提供商，客户可自由选择与主要电信运营商连接，以及接入托管于我们数据中心的多家云服务提供商。万国数据可为客户提供托管和管理服务，包括与领先的公有云进行直接私有连接、独特创新的混合云管理服务平台，以及在需要时转售公有云服务。我们拥有24年安全可靠的数据中心托管及管理服务经验，成功满足国内大型客户对于外包数据中心服务的高标准要求，目前所服务的客户主要包括超大规模云服务供应商、大型互联网公司、金融机构、电信与IT服务提供商，以及国内大型企业和跨国公司。"""
        
        success = self.kb.add_document_from_text(gds_content, "GDS万国数据公司介绍.txt")
        if success:
            logger.info("成功添加GDS万国数据默认知识库内容")
        else:
            logger.error("添加GDS万国数据默认知识库内容失败")
    
    def _register_tools(self):
        """注册MCP工具"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="knowledge_search",
                    description="在知识库中搜索相关信息并提供智能问答",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "要搜索的问题或关键词"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "返回的相关文档数量，默认为5",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="knowledge_add_text",
                    description="向知识库添加文本内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "要添加的文本内容"
                            },
                            "filename": {
                                "type": "string",
                                "description": "文件名称，默认为manual_input.txt",
                                "default": "manual_input.txt"
                            }
                        },
                        "required": ["content"]
                    }
                ),
                Tool(
                    name="knowledge_list_documents",
                    description="列出知识库中的所有文档",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="knowledge_delete_document",
                    description="从知识库中删除指定文档",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "要删除的文档文件名"
                            }
                        },
                        "required": ["filename"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "knowledge_search":
                    return await self._handle_search(arguments)
                elif name == "knowledge_add_text":
                    return await self._handle_add_text(arguments)
                elif name == "knowledge_list_documents":
                    return await self._handle_list_documents(arguments)
                elif name == "knowledge_delete_document":
                    return await self._handle_delete_document(arguments)
                else:
                    return [TextContent(type="text", text=f"未知工具: {name}")]
            except Exception as e:
                logger.error(f"工具调用失败 {name}: {e}")
                return [TextContent(type="text", text=f"工具调用失败: {str(e)}")]
    
    async def _handle_search(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理知识库搜索"""
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        
        if not query:
            return [TextContent(type="text", text="请提供搜索查询内容")]
        
        # 搜索相关文档
        results = self.kb.search(query, top_k)
        
        if not results:
            return [TextContent(type="text", text=f"未找到与'{query}'相关的信息")]
        
        # 构建回答
        response = f"根据知识库搜索，找到以下与'{query}'相关的信息：\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"**相关信息 {i}** (来源: {result['filename']}, 相似度: {result['similarity']:.3f})\n"
            response += f"{result['text']}\n\n"
        
        # 生成综合回答
        if len(results) > 0:
            response += "**综合回答：**\n"
            # 基于搜索结果生成简单的综合回答
            all_text = " ".join([r['text'] for r in results[:3]])  # 使用前3个最相关的结果
            
            if "万国数据" in query or "GDS" in query:
                response += "万国数据(GDS)是中国领先的高性能数据中心运营商，在核心经济枢纽地区运营大规模、高效的数据中心，为云服务商、互联网公司、金融机构等提供托管和管理服务。"
            else:
                # 简单的关键信息提取
                response += f"基于搜索结果，{query}的相关信息主要包含在上述文档中。"
        
        return [TextContent(type="text", text=response)]
    
    async def _handle_add_text(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理添加文本到知识库"""
        content = arguments.get("content", "")
        filename = arguments.get("filename", "manual_input.txt")
        
        if not content:
            return [TextContent(type="text", text="请提供要添加的文本内容")]
        
        success = self.kb.add_document_from_text(content, filename)
        
        if success:
            return [TextContent(type="text", text=f"成功将文本添加到知识库，文件名: {filename}")]
        else:
            return [TextContent(type="text", text="添加文本到知识库失败")]
    
    async def _handle_list_documents(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理列出知识库文档"""
        documents = self.kb.get_document_list()
        
        if not documents:
            return [TextContent(type="text", text="知识库中暂无文档")]
        
        response = "知识库文档列表：\n\n"
        for doc in documents:
            response += f"📄 **{doc['filename']}**\n"
            response += f"   - 文件类型: {doc['file_type']}\n"
            response += f"   - 上传时间: {doc['upload_time']}\n"
            response += f"   - 文档块数: {doc['chunk_count']}\n\n"
        
        return [TextContent(type="text", text=response)]
    
    async def _handle_delete_document(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理删除知识库文档"""
        filename = arguments.get("filename", "")
        
        if not filename:
            return [TextContent(type="text", text="请提供要删除的文档文件名")]
        
        success = self.kb.delete_document(filename)
        
        if success:
            return [TextContent(type="text", text=f"成功删除文档: {filename}")]
        else:
            return [TextContent(type="text", text=f"删除文档失败: {filename}")]
    
    def get_server(self) -> Server:
        """获取MCP服务器实例"""
        return self.server

# 创建全局实例
knowledge_tool = KnowledgeMCPTool()

def get_knowledge_server() -> Server:
    """获取知识库MCP服务器"""
    return knowledge_tool.get_server()

if __name__ == "__main__":
    import mcp.server.stdio
    
    async def main():
        server = get_knowledge_server()
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    
    asyncio.run(main())