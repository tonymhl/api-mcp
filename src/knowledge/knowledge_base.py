"""
知识库管理模块
支持多种文档格式的知识库构建和检索
"""

import os
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import jieba
import re

# 文档处理相关导入
try:
    import PyPDF2
    import docx
    import pandas as pd
    from openpyxl import load_workbook
except ImportError as e:
    logging.warning(f"某些文档处理库未安装: {e}")

class KnowledgeBase:
    """知识库管理类"""
    
    def __init__(self, db_path: str = "knowledge_base.db", model_name: str = "all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.model_name = model_name
        self.model = None
        self.logger = logging.getLogger(__name__)
        
        # 初始化数据库
        self._init_database()
        
        # 初始化向量模型
        self._init_model()
    
    def _init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建文档表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                file_type TEXT NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # 创建文档块表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding BLOB,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_model(self):
        """初始化向量模型"""
        try:
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"成功加载向量模型: {self.model_name}")
        except Exception as e:
            self.logger.error(f"加载向量模型失败: {e}")
            # 使用简单的TF-IDF作为备选方案
            self.model = None
    
    def _calculate_file_hash(self, content: str) -> str:
        """计算文件内容的哈希值"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """从不同格式的文件中提取文本"""
        try:
            if file_type.lower() == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_type.lower() == 'pdf':
                text = ""
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                return text
            
            elif file_type.lower() in ['doc', 'docx']:
                doc = docx.Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            
            elif file_type.lower() in ['xls', 'xlsx']:
                df = pd.read_excel(file_path)
                return df.to_string()
            
            elif file_type.lower() == 'csv':
                df = pd.read_csv(file_path)
                return df.to_string()
            
            else:
                raise ValueError(f"不支持的文件格式: {file_type}")
                
        except Exception as e:
            self.logger.error(f"提取文件文本失败: {e}")
            return ""
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """将文本分割成块"""
        # 使用jieba进行中文分词
        sentences = re.split(r'[。！？\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """获取文本的向量表示"""
        if self.model:
            try:
                return self.model.encode(text)
            except Exception as e:
                self.logger.error(f"生成向量失败: {e}")
                return None
        return None
    
    def add_document_from_text(self, content: str, filename: str = "manual_input.txt") -> bool:
        """从文本内容添加文档到知识库"""
        try:
            file_hash = self._calculate_file_hash(content)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查文档是否已存在
            cursor.execute("SELECT id FROM documents WHERE file_hash = ?", (file_hash,))
            if cursor.fetchone():
                self.logger.info(f"文档已存在: {filename}")
                conn.close()
                return True
            
            # 插入文档记录
            cursor.execute('''
                INSERT INTO documents (filename, file_hash, content, file_type, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, file_hash, content, "txt", json.dumps({"source": "manual_input"})))
            
            document_id = cursor.lastrowid
            
            # 分割文本并生成向量
            chunks = self._split_text_into_chunks(content)
            
            for i, chunk in enumerate(chunks):
                embedding = self._get_embedding(chunk)
                embedding_blob = embedding.tobytes() if embedding is not None else None
                
                cursor.execute('''
                    INSERT INTO document_chunks (document_id, chunk_text, chunk_index, embedding)
                    VALUES (?, ?, ?, ?)
                ''', (document_id, chunk, i, embedding_blob))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"成功添加文档: {filename}, 共{len(chunks)}个文本块")
            return True
            
        except Exception as e:
            self.logger.error(f"添加文档失败: {e}")
            return False
    
    def add_document_from_file(self, file_path: str) -> bool:
        """从文件添加文档到知识库"""
        try:
            filename = os.path.basename(file_path)
            file_type = filename.split('.')[-1] if '.' in filename else 'txt'
            
            # 提取文本内容
            content = self._extract_text_from_file(file_path, file_type)
            if not content:
                self.logger.error(f"无法从文件提取内容: {file_path}")
                return False
            
            return self.add_document_from_text(content, filename)
            
        except Exception as e:
            self.logger.error(f"添加文件失败: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相关文档块"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if self.model:
                # 使用向量相似度搜索
                query_embedding = self._get_embedding(query)
                if query_embedding is None:
                    return self._fallback_search(query, top_k, cursor)
                
                # 获取所有文档块
                cursor.execute('''
                    SELECT dc.chunk_text, dc.embedding, d.filename, dc.chunk_index
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE dc.embedding IS NOT NULL
                ''')
                
                results = []
                for row in cursor.fetchall():
                    chunk_text, embedding_blob, filename, chunk_index = row
                    if embedding_blob:
                        chunk_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                        # 计算余弦相似度
                        similarity = np.dot(query_embedding, chunk_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                        )
                        results.append({
                            'text': chunk_text,
                            'filename': filename,
                            'chunk_index': chunk_index,
                            'similarity': float(similarity)
                        })
                
                # 按相似度排序
                results.sort(key=lambda x: x['similarity'], reverse=True)
                conn.close()
                return results[:top_k]
            
            else:
                # 使用关键词搜索作为备选方案
                return self._fallback_search(query, top_k, cursor)
                
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            return []
    
    def _fallback_search(self, query: str, top_k: int, cursor) -> List[Dict[str, Any]]:
        """备选搜索方案（关键词匹配）"""
        # 简单的关键词搜索
        keywords = jieba.lcut(query)
        
        cursor.execute('''
            SELECT dc.chunk_text, d.filename, dc.chunk_index
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
        ''')
        
        results = []
        for row in cursor.fetchall():
            chunk_text, filename, chunk_index = row
            score = 0
            for keyword in keywords:
                score += chunk_text.count(keyword)
            
            if score > 0:
                results.append({
                    'text': chunk_text,
                    'filename': filename,
                    'chunk_index': chunk_index,
                    'similarity': score / len(keywords)
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def get_document_list(self) -> List[Dict[str, Any]]:
        """获取知识库中的文档列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT filename, file_type, upload_time, 
                       COUNT(dc.id) as chunk_count
                FROM documents d
                LEFT JOIN document_chunks dc ON d.id = dc.document_id
                GROUP BY d.id, d.filename, d.file_type, d.upload_time
                ORDER BY d.upload_time DESC
            ''')
            
            documents = []
            for row in cursor.fetchall():
                filename, file_type, upload_time, chunk_count = row
                documents.append({
                    'filename': filename,
                    'file_type': file_type,
                    'upload_time': upload_time,
                    'chunk_count': chunk_count
                })
            
            conn.close()
            return documents
            
        except Exception as e:
            self.logger.error(f"获取文档列表失败: {e}")
            return []
    
    def delete_document(self, filename: str) -> bool:
        """删除指定文档"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取文档ID
            cursor.execute("SELECT id FROM documents WHERE filename = ?", (filename,))
            result = cursor.fetchone()
            if not result:
                self.logger.warning(f"文档不存在: {filename}")
                conn.close()
                return False
            
            document_id = result[0]
            
            # 删除文档块
            cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
            
            # 删除文档记录
            cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"成功删除文档: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除文档失败: {e}")
            return False