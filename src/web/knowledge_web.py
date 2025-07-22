"""
知识库管理Web界面
提供简单的文档上传和管理功能
"""

import os
import sys
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入知识库模块
try:
    from ..knowledge.knowledge_base import KnowledgeBase
    from ..knowledge.document_uploader import DocumentUploader
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    sys.path.insert(0, os.path.join(project_root, 'src'))
    from knowledge.knowledge_base import KnowledgeBase
    from knowledge.document_uploader import DocumentUploader

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 在生产环境中应该使用更安全的密钥

# 初始化知识库和文档上传器
kb = KnowledgeBase()

# 计算正确的上传目录路径
upload_dir = os.path.join(project_root, 'data', 'uploads')
uploader = DocumentUploader(upload_dir=upload_dir, knowledge_base=kb)

# 配置上传
UPLOAD_FOLDER = upload_dir
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/knowledge')
def knowledge_base():
    """知识库管理页面"""
    documents = kb.get_document_list()
    return render_template('knowledge_base.html', documents=documents)

@app.route('/api/search', methods=['POST'])
def search_knowledge():
    """搜索知识库API"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({
                'success': False,
                'error': '请提供搜索查询'
            })
        
        results = kb.search(query, top_k)
        
        # 构建回答
        if results:
            response = f"找到 {len(results)} 个相关结果：\n\n"
            for i, result in enumerate(results, 1):
                response += f"**结果 {i}** (来源: {result['filename']}, 相似度: {result['similarity']:.3f})\n"
                response += f"{result['text'][:200]}...\n\n"
        else:
            response = f"未找到与'{query}'相关的信息"
        
        return jsonify({
            'success': True,
            'message': response,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/upload_text', methods=['POST'])
def upload_text():
    """上传文本内容API"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        filename = data.get('filename', 'manual_input.txt')
        
        if not content:
            return jsonify({
                'success': False,
                'error': '请提供文本内容'
            })
        
        result = uploader.upload_text_content(content, filename)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"上传文本失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/upload_file', methods=['POST'])
def upload_file():
    """上传文件API"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            })
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            })
        
        if file and uploader.is_supported_format(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # 确保上传目录存在
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # 保存文件
            file.save(file_path)
            
            # 添加到知识库
            result = uploader.upload_file(file_path, filename)
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': '不支持的文件格式'
            })
            
    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """获取文档列表API"""
    try:
        documents = kb.get_document_list()
        return jsonify({
            'success': True,
            'documents': documents
        })
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/documents/<filename>', methods=['DELETE'])
def delete_document(filename):
    """删除文档API"""
    try:
        # 从知识库删除
        kb_result = kb.delete_document(filename)
        
        # 删除物理文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({
            'success': kb_result,
            'message': f'文档 {filename} 删除成功' if kb_result else f'删除文档 {filename} 失败'
        })
        
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/supported_formats', methods=['GET'])
def get_supported_formats():
    """获取支持的文件格式API"""
    return jsonify({
        'success': True,
        'formats': uploader.get_supported_formats()
    })

def create_templates():
    """创建基本的HTML模板"""
    
    # 基础模板
    base_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}知识库管理系统{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .search-result {
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 10px 0;
        }
        .similarity-score {
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">知识库管理系统</a>
            <div class="navbar-nav">
                <a class="nav-link" href="{{ url_for('index') }}">首页</a>
                <a class="nav-link" href="{{ url_for('knowledge_base') }}">知识库</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-info">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    # 主页模板
    index_template = '''{% extends "base.html" %}

{% block title %}知识库搜索 - 知识库管理系统{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8">
        <h2>知识库搜索</h2>
        <div class="card">
            <div class="card-body">
                <div class="mb-3">
                    <label for="searchQuery" class="form-label">搜索问题</label>
                    <input type="text" class="form-control" id="searchQuery" placeholder="请输入您的问题...">
                </div>
                <div class="mb-3">
                    <label for="topK" class="form-label">返回结果数量</label>
                    <select class="form-select" id="topK">
                        <option value="3">3</option>
                        <option value="5" selected>5</option>
                        <option value="10">10</option>
                    </select>
                </div>
                <button type="button" class="btn btn-primary" onclick="searchKnowledge()">搜索</button>
            </div>
        </div>
        
        <div id="searchResults" class="mt-4"></div>
    </div>
    
    <div class="col-md-4">
        <h3>添加文本内容</h3>
        <div class="card">
            <div class="card-body">
                <div class="mb-3">
                    <label for="textContent" class="form-label">文本内容</label>
                    <textarea class="form-control" id="textContent" rows="5" placeholder="请输入要添加的文本内容..."></textarea>
                </div>
                <div class="mb-3">
                    <label for="textFilename" class="form-label">文件名</label>
                    <input type="text" class="form-control" id="textFilename" placeholder="manual_input.txt">
                </div>
                <button type="button" class="btn btn-success" onclick="uploadText()">添加到知识库</button>
            </div>
        </div>
        
        <h3 class="mt-4">上传文件</h3>
        <div class="card">
            <div class="card-body">
                <div class="mb-3">
                    <label for="fileUpload" class="form-label">选择文件</label>
                    <input type="file" class="form-control" id="fileUpload" accept=".txt,.pdf,.doc,.docx,.xls,.xlsx,.csv">
                </div>
                <button type="button" class="btn btn-success" onclick="uploadFile()">上传文件</button>
                <div class="mt-2">
                    <small class="text-muted">支持格式: TXT, PDF, DOC, DOCX, XLS, XLSX, CSV</small>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
async function searchKnowledge() {
    const query = document.getElementById('searchQuery').value;
    const topK = document.getElementById('topK').value;
    
    if (!query.trim()) {
        alert('请输入搜索问题');
        return;
    }
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: parseInt(topK)
            })
        });
        
        const result = await response.json();
        displaySearchResults(result);
    } catch (error) {
        console.error('搜索失败:', error);
        alert('搜索失败，请重试');
    }
}

function displaySearchResults(result) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (result.success) {
        let html = '<h3>搜索结果</h3>';
        html += '<div class="search-result">';
        html += '<pre>' + result.message + '</pre>';
        html += '</div>';
        resultsDiv.innerHTML = html;
    } else {
        resultsDiv.innerHTML = '<div class="alert alert-danger">搜索失败: ' + result.error + '</div>';
    }
}

async function uploadText() {
    const content = document.getElementById('textContent').value;
    const filename = document.getElementById('textFilename').value || 'manual_input.txt';
    
    if (!content.trim()) {
        alert('请输入文本内容');
        return;
    }
    
    try {
        const response = await fetch('/api/upload_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: content,
                filename: filename
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('文本添加成功');
            document.getElementById('textContent').value = '';
            document.getElementById('textFilename').value = '';
        } else {
            alert('添加失败: ' + result.error);
        }
    } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败，请重试');
    }
}

async function uploadFile() {
    const fileInput = document.getElementById('fileUpload');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('请选择文件');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload_file', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('文件上传成功');
            fileInput.value = '';
        } else {
            alert('上传失败: ' + result.error);
        }
    } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败，请重试');
    }
}
</script>
{% endblock %}'''
    
    # 知识库管理模板
    knowledge_template = '''{% extends "base.html" %}

{% block title %}知识库管理 - 知识库管理系统{% endblock %}

{% block content %}
<h2>知识库文档管理</h2>

<div class="card">
    <div class="card-header">
        <h5>文档列表</h5>
        <button type="button" class="btn btn-sm btn-primary" onclick="refreshDocuments()">刷新</button>
    </div>
    <div class="card-body">
        <div id="documentsTable">
            {% if documents %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>文件名</th>
                                <th>文件类型</th>
                                <th>上传时间</th>
                                <th>文档块数</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for doc in documents %}
                            <tr>
                                <td>{{ doc.filename }}</td>
                                <td>{{ doc.file_type }}</td>
                                <td>{{ doc.upload_time }}</td>
                                <td>{{ doc.chunk_count }}</td>
                                <td>
                                    <button type="button" class="btn btn-sm btn-danger" 
                                            onclick="deleteDocument('{{ doc.filename }}')">删除</button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <p class="text-muted">知识库中暂无文档</p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
async function refreshDocuments() {
    try {
        const response = await fetch('/api/documents');
        const result = await response.json();
        
        if (result.success) {
            updateDocumentsTable(result.documents);
        } else {
            alert('获取文档列表失败: ' + result.error);
        }
    } catch (error) {
        console.error('刷新失败:', error);
        alert('刷新失败，请重试');
    }
}

function updateDocumentsTable(documents) {
    const tableDiv = document.getElementById('documentsTable');
    
    if (documents.length === 0) {
        tableDiv.innerHTML = '<p class="text-muted">知识库中暂无文档</p>';
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-striped">';
    html += '<thead><tr><th>文件名</th><th>文件类型</th><th>上传时间</th><th>文档块数</th><th>操作</th></tr></thead>';
    html += '<tbody>';
    
    documents.forEach(doc => {
        html += '<tr>';
        html += '<td>' + doc.filename + '</td>';
        html += '<td>' + doc.file_type + '</td>';
        html += '<td>' + doc.upload_time + '</td>';
        html += '<td>' + doc.chunk_count + '</td>';
        html += '<td><button type="button" class="btn btn-sm btn-danger" onclick="deleteDocument(\'' + doc.filename + '\')">';
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    tableDiv.innerHTML = html;
}

async function deleteDocument(filename) {
    if (!confirm('确定要删除文档 "' + filename + '" 吗？')) {
        return;
    }
    
    try {
        const response = await fetch('/api/documents/' + encodeURIComponent(filename), {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('文档删除成功');
            refreshDocuments();
        } else {
            alert('删除失败: ' + result.message);
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请重试');
    }
}
</script>
{% endblock %}'''
    
    # 保存模板文件
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write(base_template)
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(index_template)
    
    with open('templates/knowledge_base.html', 'w', encoding='utf-8') as f:
        f.write(knowledge_template)

if __name__ == '__main__':
    # 创建模板目录和基本模板文件
    os.makedirs('templates', exist_ok=True)
    
    # 创建基本的HTML模板
    create_templates()
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5001)

def create_templates():
    """创建基本的HTML模板"""
    
    # 基础模板
    base_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}知识库管理系统{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .search-result {
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 10px 0;
        }
        .similarity-score {
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">知识库管理系统</a>
            <div class="navbar-nav">
                <a class="nav-link" href="{{ url_for('index') }}">首页</a>
                <a class="nav-link" href="{{ url_for('knowledge_base') }}">知识库</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-info">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    # 主页模板
    index_template = '''{% extends "base.html" %}

{% block title %}知识库搜索 - 知识库管理系统{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8">
        <h2>知识库搜索</h2>
        <div class="card">
            <div class="card-body">
                <div class="mb-3">
                    <label for="searchQuery" class="form-label">搜索问题</label>
                    <input type="text" class="form-control" id="searchQuery" placeholder="请输入您的问题...">
                </div>
                <div class="mb-3">
                    <label for="topK" class="form-label">返回结果数量</label>
                    <select class="form-select" id="topK">
                        <option value="3">3</option>
                        <option value="5" selected>5</option>
                        <option value="10">10</option>
                    </select>
                </div>
                <button type="button" class="btn btn-primary" onclick="searchKnowledge()">搜索</button>
            </div>
        </div>
        
        <div id="searchResults" class="mt-4"></div>
    </div>
    
    <div class="col-md-4">
        <h3>添加文本内容</h3>
        <div class="card">
            <div class="card-body">
                <div class="mb-3">
                    <label for="textContent" class="form-label">文本内容</label>
                    <textarea class="form-control" id="textContent" rows="5" placeholder="请输入要添加的文本内容..."></textarea>
                </div>
                <div class="mb-3">
                    <label for="textFilename" class="form-label">文件名</label>
                    <input type="text" class="form-control" id="textFilename" placeholder="manual_input.txt">
                </div>
                <button type="button" class="btn btn-success" onclick="uploadText()">添加到知识库</button>
            </div>
        </div>
        
        <h3 class="mt-4">上传文件</h3>
        <div class="card">
            <div class="card-body">
                <div class="mb-3">
                    <label for="fileUpload" class="form-label">选择文件</label>
                    <input type="file" class="form-control" id="fileUpload" accept=".txt,.pdf,.doc,.docx,.xls,.xlsx,.csv">
                </div>
                <button type="button" class="btn btn-success" onclick="uploadFile()">上传文件</button>
                <div class="mt-2">
                    <small class="text-muted">支持格式: TXT, PDF, DOC, DOCX, XLS, XLSX, CSV</small>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
async function searchKnowledge() {
    const query = document.getElementById('searchQuery').value;
    const topK = document.getElementById('topK').value;
    
    if (!query.trim()) {
        alert('请输入搜索问题');
        return;
    }
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: parseInt(topK)
            })
        });
        
        const result = await response.json();
        displaySearchResults(result);
    } catch (error) {
        console.error('搜索失败:', error);
        alert('搜索失败，请重试');
    }
}

function displaySearchResults(result) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (result.success) {
        let html = '<h3>搜索结果</h3>';
        html += '<div class="search-result">';
        html += '<pre>' + result.message + '</pre>';
        html += '</div>';
        resultsDiv.innerHTML = html;
    } else {
        resultsDiv.innerHTML = '<div class="alert alert-danger">搜索失败: ' + result.error + '</div>';
    }
}

async function uploadText() {
    const content = document.getElementById('textContent').value;
    const filename = document.getElementById('textFilename').value || 'manual_input.txt';
    
    if (!content.trim()) {
        alert('请输入文本内容');
        return;
    }
    
    try {
        const response = await fetch('/api/upload_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: content,
                filename: filename
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('文本添加成功');
            document.getElementById('textContent').value = '';
            document.getElementById('textFilename').value = '';
        } else {
            alert('添加失败: ' + result.error);
        }
    } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败，请重试');
    }
}

async function uploadFile() {
    const fileInput = document.getElementById('fileUpload');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('请选择文件');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload_file', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('文件上传成功');
            fileInput.value = '';
        } else {
            alert('上传失败: ' + result.error);
        }
    } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败，请重试');
    }
}
</script>
{% endblock %}'''
    
    # 知识库管理模板
    knowledge_template = '''{% extends "base.html" %}

{% block title %}知识库管理 - 知识库管理系统{% endblock %}

{% block content %}
<h2>知识库文档管理</h2>

<div class="card">
    <div class="card-header">
        <h5>文档列表</h5>
        <button type="button" class="btn btn-sm btn-primary" onclick="refreshDocuments()">刷新</button>
    </div>
    <div class="card-body">
        <div id="documentsTable">
            {% if documents %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>文件名</th>
                                <th>文件类型</th>
                                <th>上传时间</th>
                                <th>文档块数</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for doc in documents %}
                            <tr>
                                <td>{{ doc.filename }}</td>
                                <td>{{ doc.file_type }}</td>
                                <td>{{ doc.upload_time }}</td>
                                <td>{{ doc.chunk_count }}</td>
                                <td>
                                    <button type="button" class="btn btn-sm btn-danger" 
                                            onclick="deleteDocument('{{ doc.filename }}')">删除</button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <p class="text-muted">知识库中暂无文档</p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
async function refreshDocuments() {
    try {
        const response = await fetch('/api/documents');
        const result = await response.json();
        
        if (result.success) {
            updateDocumentsTable(result.documents);
        } else {
            alert('获取文档列表失败: ' + result.error);
        }
    } catch (error) {
        console.error('刷新失败:', error);
        alert('刷新失败，请重试');
    }
}

function updateDocumentsTable(documents) {
    const tableDiv = document.getElementById('documentsTable');
    
    if (documents.length === 0) {
        tableDiv.innerHTML = '<p class="text-muted">知识库中暂无文档</p>';
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-striped">';
    html += '<thead><tr><th>文件名</th><th>文件类型</th><th>上传时间</th><th>文档块数</th><th>操作</th></tr></thead>';
    html += '<tbody>';
    
    documents.forEach(doc => {
        html += '<tr>';
        html += '<td>' + doc.filename + '</td>';
        html += '<td>' + doc.file_type + '</td>';
        html += '<td>' + doc.upload_time + '</td>';
        html += '<td>' + doc.chunk_count + '</td>';
        html += '<td><button type="button" class="btn btn-sm btn-danger" onclick="deleteDocument(\'' + doc.filename + '\')">删除</button></td>';
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    tableDiv.innerHTML = html;
}

async function deleteDocument(filename) {
    if (!confirm('确定要删除文档 "' + filename + '" 吗？')) {
        return;
    }
    
    try {
        const response = await fetch('/api/documents/' + encodeURIComponent(filename), {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('文档删除成功');
            refreshDocuments();
        } else {
            alert('删除失败: ' + result.message);
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请重试');
    }
}
</script>
{% endblock %}'''
    
    # 保存模板文件
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write(base_template)
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(index_template)
    
    with open('templates/knowledge_base.html', 'w', encoding='utf-8') as f:
        f.write(knowledge_template)