

# Universal MCP Tool

一个万能的MCP工具，能够将Web API接口轻松转化为MCP工具，供AI助手使用。现已集成RAG知识库功能，支持多种文档格式的智能问答。

## 功能特点

### API管理功能
- 通过简单配置，快速将API转化为MCP工具
- 支持GET和POST请求方法
- 可视化界面，操作简便
- 支持动态添加、删除和修改API配置
- 实时查看和编辑API描述和参数格式
- **API测试功能**，确保API可用性，提前验证请求和响应
- **API密钥管理**，支持多种密钥认证方式，AI助手可自动使用密钥调用API

### 知识库功能 🆕
- **RAG智能问答**：基于向量相似度的知识检索和问答
- **多格式支持**：支持TXT、PDF、DOC、DOCX、XLS、XLSX、CSV等文档格式
- **文档管理**：支持文档上传、删除、列表查看等操作
- **Web界面**：提供友好的Web界面进行知识库管理
- **中文优化**：针对中文文本进行优化的分词和检索
- **向量化存储**：使用SentenceTransformer进行文本向量化，支持语义搜索

## 项目结构

```
api-mcp/
├── main.py                 # 主启动脚本
├── requirements.txt        # 依赖包列表
├── pyproject.toml         # 项目配置文件
├── README.md              # 项目说明文档
├── src/                   # 源代码目录
│   ├── core/              # 核心功能模块
│   │   ├── universal_mcp_tool.py  # MCP工具核心
│   │   ├── config_manager.py      # 配置管理
│   │   └── mcp_pipe.py           # MCP管道
│   ├── knowledge/         # 知识库模块
│   │   ├── knowledge_base.py     # 知识库核心
│   │   ├── document_uploader.py  # 文档上传处理
│   │   └── knowledge_mcp_tool.py # 知识库MCP工具
│   └── web/               # Web界面模块
│       ├── knowledge_web.py      # 知识库Web界面
│       ├── universal_mcp_gui.py  # GUI管理界面
│       └── templates/            # HTML模板
├── scripts/               # 启动脚本
│   ├── start_services.py         # 服务启动脚本
│   └── 启动_universal_mcp.py     # 中文启动脚本
├── data/                  # 数据目录
│   ├── uploads/           # 上传文件存储
│   ├── api_configs.json   # API配置文件
│   └── *.log             # 日志文件
└── docs/                  # 文档目录
```

## 安装要求

```
python>=3.8
requests>=2.25.0
fastmcp>=0.1.0
flask>=2.0.0,<3.0.0
werkzeug>=2.0.0,<3.0.0
sentence-transformers>=2.2.0,<3.0.0
transformers>=4.20.0,<5.0.0
torch>=1.12.0,<3.0.0
jieba>=0.42.0
numpy>=1.21.0,<2.0.0
scipy>=1.7.0,<2.0.0
scikit-learn>=1.0.0,<2.0.0
PyPDF2>=3.0.0
python-docx>=0.8.11
pandas>=1.3.0,<3.0.0
openpyxl>=3.0.0
```

## 快速开始

1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **启动应用**

### 方式一：使用主启动脚本（推荐）
```bash
# 启动GUI管理界面
python main.py --mode gui

# 启动完整服务（MCP + 知识库Web界面）
python main.py --mode full

# 仅启动MCP服务
python main.py --mode mcp

# 仅启动知识库Web界面
python main.py --mode web --port 5001
```

### 方式二：使用脚本启动
```bash
# 启动GUI界面（仅API管理）
python scripts/启动_universal_mcp.py

# 启动完整服务（API + 知识库）
python scripts/start_services.py
```

### 方式三：分别启动服务
```bash
# 启动MCP服务
python src/core/mcp_pipe.py src/core/universal_mcp_tool.py

# 启动知识库Web界面（新终端窗口）
python src/web/knowledge_web.py
```

## 服务访问

- **MCP服务**：自动连接到小智AI终端
- **知识库Web界面**：http://localhost:5001
- **GUI管理界面**：通过启动脚本打开

## 使用指南

### 基本配置

1. 在"基本配置"选项卡中设置MCP端点
2. 点击"保存配置"按钮保存设置

### API管理

1. 在"API管理"选项卡中，您可以添加、删除和修改API配置
2. 添加API时，需要提供以下信息：
   - API名称：将会成为MCP工具的名称
   - API URL：API的完整URL地址
   - 请求方法：GET或POST
   - API描述：对API功能的简短描述
   - API密钥：需要授权的API可以设置密钥
   - 密钥位置：header、query或body，指定密钥放在哪里
   - 密钥参数名：密钥的参数名称，如"Authorization"、"api_key"等
   - 请求参数格式：JSON格式的请求参数描述
   - 返回参数格式：JSON格式的返回参数描述

3. 添加完成后，点击"保存API"按钮

### API密钥管理

1. 对于需要密钥的API，可在添加时直接填写"API密钥"字段
2. 可选择密钥位置：
   - header：在HTTP请求头中添加密钥（如Authorization头）
   - query：在URL查询参数中添加密钥（如?api_key=xxx）
   - body：在请求体中添加密钥（适用于POST请求）
3. 密钥参数名根据API要求填写，例如"Authorization"、"api_key"、"token"等
4. 系统会自动处理密钥的添加，AI助手无需知道密钥即可调用API

### API测试

1. 选择已添加的API，点击"测试API"按钮
2. 在弹出的测试窗口中，填写API请求参数
3. 点击"发送请求"按钮测试API
4. 查看API响应结果和格式验证
   - 系统会自动验证响应是否符合预期格式
   - 如果有缺少的字段，会显示警告信息

### 启动服务

1. 在"日志"选项卡中，点击"启动服务"按钮启动MCP服务
2. 服务启动后，将在后台运行，可以与AI助手集成使用

## 知识库使用指南

### 通过Web界面管理

1. **访问Web界面**：打开 http://localhost:5000
2. **搜索知识**：
   - 在首页输入问题进行搜索
   - 选择返回结果数量（3、5、10）
   - 查看搜索结果和相似度评分

3. **添加文本内容**：
   - 在右侧面板输入文本内容
   - 指定文件名（可选）
   - 点击"添加到知识库"

4. **上传文档**：
   - 选择支持的文件格式（TXT、PDF、DOC、DOCX、XLS、XLSX、CSV）
   - 点击"上传文件"
   - 系统自动解析并添加到知识库

5. **管理文档**：
   - 访问"知识库"页面查看所有文档
   - 查看文档信息（文件名、类型、上传时间、文档块数）
   - 删除不需要的文档

### 通过MCP工具使用

知识库功能已集成到MCP服务中，AI助手可以直接使用以下工具：

1. **knowledge_search**：搜索知识库并获取答案
   - 参数：query（搜索问题）、top_k（返回结果数，可选）
   - 返回：相关文档片段和智能回答

2. **knowledge_add_text**：添加文本内容到知识库
   - 参数：content（文本内容）、filename（文件名，可选）
   - 返回：添加结果

3. **knowledge_list_documents**：列出知识库中的所有文档
   - 无参数
   - 返回：文档列表

4. **knowledge_delete_document**：删除指定文档
   - 参数：filename（文件名）
   - 返回：删除结果

### 预置知识内容

系统已预置"GDS万国数据"公司介绍作为示例知识库内容，您可以：
- 搜索相关问题测试功能
- 添加更多相关内容扩展知识库
- 上传相关文档丰富知识库

## API配置示例

### 天气查询API

```json
{
  "api_name": "查询天气",
  "api_url": "https://api.example.com/weather",
  "method": "GET",
  "request_format": {
    "city": "string",
    "days": "number"
  },
  "response_format": {
    "temperature": "number",
    "weather": "string",
    "humidity": "number"
  },
  "description": "根据城市名称查询天气预报"
}
```

### 需要API密钥的翻译API

```json
{
  "api_name": "翻译文本",
  "api_url": "https://api.example.com/translate",
  "method": "POST",
  "api_key": "your-api-key-here",
  "key_location": "header",
  "key_name": "Authorization",
  "request_format": {
    "text": "string",
    "source": "string",
    "target": "string"
  },
  "response_format": {
    "translated": "string",
    "status": "number"
  },
  "description": "将文本从源语言翻译到目标语言"
}
```

## 高级使用

1. 直接注册API：MCP服务本身提供了`register_api`工具，可以通过AI助手直接调用注册新API
2. 查看已注册API：可以通过`list_registered_apis`工具查看所有已注册的API
3. 删除注册的API：可以通过`remove_registered_api`工具删除指定的API
4. 带密钥API调用：AI助手可以直接调用带密钥的API，无需知道密钥内容

## 注意事项

### API相关
1. API配置保存在`api_configs.json`文件中
2. 基本配置保存在`~/.xiaozhi_mcp_config.json`文件中
3. 确保您使用的API端点允许跨域请求
4. 测试API功能中的参数类型会自动转换，例如数字类型、布尔类型等
5. API密钥会被保存在配置文件中，请确保配置文件的安全性

### 知识库相关
1. 知识库数据存储在SQLite数据库中（`knowledge_base.db`）
2. 上传的文件保存在`uploads/`目录中
3. 首次运行时会自动下载SentenceTransformer模型，需要网络连接
4. 支持的文档格式：TXT、PDF、DOC、DOCX、XLS、XLSX、CSV
5. 文档会被自动分块处理，每块大小约500字符
6. 建议上传高质量、结构化的文档以获得更好的问答效果
7. Web界面默认运行在5000端口，确保端口未被占用

### 性能优化建议
1. 对于大型文档，建议分批上传以提高处理速度
2. 定期清理不需要的文档以节省存储空间
3. 知识库搜索结果数量建议设置为3-10个，平衡准确性和响应速度
