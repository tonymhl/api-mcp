"""
文档上传和处理工具
支持多种文档格式的上传和处理
"""

import os
import sys
import shutil
import logging
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入知识库模块
try:
    from .knowledge_base import KnowledgeBase
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    sys.path.insert(0, os.path.join(project_root, 'src'))
    from knowledge.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

class DocumentUploader:
    """文档上传处理类"""
    
    def __init__(self, upload_dir: str = "uploads", knowledge_base: Optional[KnowledgeBase] = None):
        self.upload_dir = upload_dir
        self.knowledge_base = knowledge_base or KnowledgeBase()
        
        # 创建上传目录
        os.makedirs(upload_dir, exist_ok=True)
        
        # 支持的文件格式
        self.supported_formats = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv'
        }
    
    def is_supported_format(self, filename: str) -> bool:
        """检查文件格式是否支持"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return ext in self.supported_formats
    
    def upload_file(self, file_path: str, target_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        上传文件到知识库
        :param file_path: 源文件路径
        :param target_filename: 目标文件名（可选）
        :return: 上传结果
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"文件不存在: {file_path}"
                }
            
            filename = target_filename or os.path.basename(file_path)
            
            if not self.is_supported_format(filename):
                return {
                    "success": False,
                    "error": f"不支持的文件格式: {filename}"
                }
            
            # 复制文件到上传目录
            target_path = os.path.join(self.upload_dir, filename)
            shutil.copy2(file_path, target_path)
            
            # 添加到知识库
            success = self.knowledge_base.add_document_from_file(target_path)
            
            if success:
                logger.info(f"成功上传文件到知识库: {filename}")
                return {
                    "success": True,
                    "message": f"成功上传文件: {filename}",
                    "filename": filename,
                    "file_path": target_path
                }
            else:
                # 如果添加到知识库失败，删除已复制的文件
                if os.path.exists(target_path):
                    os.remove(target_path)
                return {
                    "success": False,
                    "error": f"添加文件到知识库失败: {filename}"
                }
                
        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_text_content(self, content: str, filename: str) -> Dict[str, Any]:
        """
        直接上传文本内容到知识库
        :param content: 文本内容
        :param filename: 文件名
        :return: 上传结果
        """
        try:
            # 保存文本到文件
            file_path = os.path.join(self.upload_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 添加到知识库
            success = self.knowledge_base.add_document_from_text(content, filename)
            
            if success:
                logger.info(f"成功上传文本内容到知识库: {filename}")
                return {
                    "success": True,
                    "message": f"成功上传文本内容: {filename}",
                    "filename": filename,
                    "file_path": file_path
                }
            else:
                # 如果添加到知识库失败，删除已保存的文件
                if os.path.exists(file_path):
                    os.remove(file_path)
                return {
                    "success": False,
                    "error": f"添加文本内容到知识库失败: {filename}"
                }
                
        except Exception as e:
            logger.error(f"上传文本内容失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def batch_upload(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        批量上传文件
        :param file_paths: 文件路径列表
        :return: 批量上传结果
        """
        results = []
        success_count = 0
        
        for file_path in file_paths:
            result = self.upload_file(file_path)
            results.append({
                "file_path": file_path,
                "result": result
            })
            if result["success"]:
                success_count += 1
        
        return {
            "success": success_count > 0,
            "message": f"批量上传完成，成功: {success_count}/{len(file_paths)}",
            "success_count": success_count,
            "total_count": len(file_paths),
            "results": results
        }
    
    def get_uploaded_files(self) -> List[Dict[str, Any]]:
        """获取已上传的文件列表"""
        try:
            files = []
            if os.path.exists(self.upload_dir):
                for filename in os.listdir(self.upload_dir):
                    file_path = os.path.join(self.upload_dir, filename)
                    if os.path.isfile(file_path):
                        stat = os.stat(file_path)
                        files.append({
                            "filename": filename,
                            "file_path": file_path,
                            "size": stat.st_size,
                            "modified_time": stat.st_mtime,
                            "is_supported": self.is_supported_format(filename)
                        })
            return files
        except Exception as e:
            logger.error(f"获取上传文件列表失败: {e}")
            return []
    
    def delete_uploaded_file(self, filename: str) -> Dict[str, Any]:
        """删除已上传的文件"""
        try:
            file_path = os.path.join(self.upload_dir, filename)
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"文件不存在: {filename}"
                }
            
            # 从知识库中删除
            kb_result = self.knowledge_base.delete_document(filename)
            
            # 删除物理文件
            os.remove(file_path)
            
            logger.info(f"成功删除文件: {filename}")
            return {
                "success": True,
                "message": f"成功删除文件: {filename}",
                "knowledge_base_deleted": kb_result
            }
            
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_formats(self) -> Dict[str, str]:
        """获取支持的文件格式"""
        return self.supported_formats.copy()

# 创建全局实例
document_uploader = DocumentUploader()

def get_document_uploader() -> DocumentUploader:
    """获取文档上传器实例"""
    return document_uploader