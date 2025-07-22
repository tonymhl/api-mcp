#!/usr/bin/env python3
"""
简化版知识库Web界面
避免复杂的NLP依赖，提供基本的文档管理功能
"""

import os
import sys
import json
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 计算正确的上传目录路径
upload_dir = os.path.join(project_root, 'data', 'uploads')
os.makedirs(upload_dir, exist_ok=True)

# 配置上传
UPLOAD_FOLDER = upload_dir
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 简单的文档存储
documents = []

@app.route('/')
def index():
    """主页"""
    template = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>知识库管理系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4">🎯 GDS MCP Tool - 万国数据GDS知识库管理</h1>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                    <h5>📝 添加文本内容</h5>
                    <small class="text-muted">提示：上传以"GDS"或"万国数据"开头的文件可自定义GDS万国数据介绍内容</small>
                </div>
                    <div class="card-body">
                        <form id="textForm">
                            <div class="mb-3">
                                <label for="filename" class="form-label">文件名</label>
                                <input type="text" class="form-control" id="filename" value="manual_input.txt">
                            </div>
                            <div class="mb-3">
                                <label for="content" class="form-label">文本内容</label>
                                <textarea class="form-control" id="content" rows="5" placeholder="输入要添加的文本内容..."></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary">添加文本</button>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>📁 上传文件</h5>
                    </div>
                    <div class="card-body">
                        <form id="fileForm" enctype="multipart/form-data">
                            <div class="mb-3">
                                <label for="file" class="form-label">选择文件</label>
                                <input type="file" class="form-control" id="file" accept=".txt,.md,.pdf,.docx">
                            </div>
                            <button type="submit" class="btn btn-success">上传文件</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>🔍 搜索知识库</h5>
                    </div>
                    <div class="card-body">
                        <form id="searchForm">
                            <div class="input-group mb-3">
                                <input type="text" class="form-control" id="query" placeholder="输入搜索关键词...">
                                <button type="submit" class="btn btn-outline-secondary">搜索</button>
                            </div>
                        </form>
                        <div id="searchResults"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>📚 文档列表</h5>
                    </div>
                    <div class="card-body">
                        <div id="documentList">
                            <p class="text-muted">暂无文档</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // 添加文本内容
        document.getElementById('textForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const filename = document.getElementById('filename').value;
            const content = document.getElementById('content').value;
            
            if (!content) {
                alert('请输入文本内容');
                return;
            }
            
            try {
                const response = await fetch('/api/upload_text', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({filename, content})
                });
                
                const result = await response.json();
                if (result.success) {
                    alert('文本添加成功！');
                    document.getElementById('content').value = '';
                    loadDocuments();
                } else {
                    alert('添加失败: ' + result.error);
                }
            } catch (error) {
                alert('添加失败: ' + error.message);
            }
        });
        
        // 上传文件
        document.getElementById('fileForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('file');
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
                    alert('文件上传成功！');
                    fileInput.value = '';
                    loadDocuments();
                } else {
                    alert('上传失败: ' + result.error);
                }
            } catch (error) {
                alert('上传失败: ' + error.message);
            }
        });
        
        // 搜索
        document.getElementById('searchForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const query = document.getElementById('query').value;
            
            if (!query) {
                alert('请输入搜索关键词');
                return;
            }
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({query})
                });
                
                const result = await response.json();
                const resultsDiv = document.getElementById('searchResults');
                
                if (result.success) {
                    resultsDiv.innerHTML = '<div class="alert alert-success">' + result.message + '</div>';
                } else {
                    resultsDiv.innerHTML = '<div class="alert alert-danger">搜索失败: ' + result.error + '</div>';
                }
            } catch (error) {
                document.getElementById('searchResults').innerHTML = '<div class="alert alert-danger">搜索失败: ' + error.message + '</div>';
            }
        });
        
        // 加载文档列表
        async function loadDocuments() {
            try {
                const response = await fetch('/api/documents');
                const result = await response.json();
                const listDiv = document.getElementById('documentList');
                
                if (result.success && result.documents.length > 0) {
                    listDiv.innerHTML = result.documents.map(doc => 
                        '<div class="d-flex justify-content-between align-items-center border-bottom py-2">' +
                        '<span>' + doc + '</span>' +
                        '<button class="btn btn-sm btn-danger" onclick="deleteDocument(\'' + doc + '\')">删除</button>' +
                        '</div>'
                    ).join('');
                } else {
                    listDiv.innerHTML = '<p class="text-muted">暂无文档</p>';
                }
            } catch (error) {
                console.error('加载文档列表失败:', error);
            }
        }
        
        // 删除文档
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
                    alert('文档删除成功！');
                    loadDocuments();
                } else {
                    alert('删除失败: ' + result.error);
                }
            } catch (error) {
                alert('删除失败: ' + error.message);
            }
        }
        
        // 页面加载时获取文档列表
        loadDocuments();
    </script>
</body>
</html>
    '''
    return render_template_string(template)

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
        
        # 保存文本文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 添加到文档列表
        if filename not in documents:
            documents.append(filename)
        
        return jsonify({
            'success': True,
            'message': f'文本文件 {filename} 保存成功'
        })
        
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
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # 确保上传目录存在
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # 保存文件
            file.save(file_path)
            
            # 添加到文档列表
            if filename not in documents:
                documents.append(filename)
            
            return jsonify({
                'success': True,
                'message': f'文件 {filename} 上传成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '文件上传失败'
            })
            
    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/search', methods=['POST'])
def search_knowledge():
    """搜索知识库API（简化版）"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'success': False,
                'error': '请提供搜索查询'
            })
        
        # 简单的文本搜索
        results = []
        for filename in documents:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            # 找到包含查询词的段落
                            lines = content.split('\n')
                            matching_lines = [line for line in lines if query.lower() in line.lower()]
                            results.append({
                                'filename': filename,
                                'matches': matching_lines[:3]  # 最多显示3个匹配行
                            })
                except Exception as e:
                    logger.error(f"读取文件 {filename} 失败: {e}")
        
        if results:
            response = f"找到 {len(results)} 个相关文档：\n\n"
            for result in results:
                response += f"**文档: {result['filename']}**\n"
                for match in result['matches']:
                    response += f"- {match.strip()}\n"
                response += "\n"
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

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """获取文档列表API"""
    try:
        # 刷新文档列表
        documents.clear()
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                    documents.append(filename)
        
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
        # 删除物理文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 从文档列表删除
        if filename in documents:
            documents.remove(filename)
        
        return jsonify({
            'success': True,
            'message': f'文档 {filename} 删除成功'
        })
        
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/gds_intro', methods=['GET'])
def gds_intro():
    """GDS万国数据介绍API"""
    try:
        # 默认的GDS万国数据介绍内容
        default_intro = """
一、经营与战略
Q1：GDS的核心竞争优势是什么？
A1：GDS通过深耕一线城市、长期锁定土地资源、自建自营的高可用性设施，以及提供定制化服务，形成了强大的客户粘性和高进入壁垒。
Q2：GDS的国际业务发展路径如何？
A2：GDS于2022年设立GDS International（后更名为DayOne），负责海外市场拓展。截至2024年底，GDS已将其控股权出让，目前仅保留35.6%股权。
Q3：GDS为何采用“carrier-neutral”和“cloud-neutral”的运营策略？
A3：该策略使GDS可服务多类客户，避免依赖单一电信运营商或云平台，提高设施复用率和网络互联灵活性，提升资产价值。
Q4：GDS的主要收入来源有哪些？
A4：其主要收入来自数据中心租赁及运维服务，客户签订长期协议，按月计费，包括电力容量、机柜租赁、运维服务等。
二、财务结构与趋势
Q5：GDS的2025年Q1净利润变化趋势如何？
A5：2025年Q1净利润为7.64亿元，显著扭亏为盈，主要因营收增长、运营成本控制和一次性处置收益（子公司权益剥离）。
Q6：GDS的毛利率水平是否稳定？
A6：毛利率从2024年Q1的21.4%提升至2025年Q1的23.7%，主要得益于成本占比下降和规模效应提升。
Q7：调整后EBITDA和EBITDA Margin变动如何？
A7：2025年Q1调整后EBITDA同比增长16.1%至13.24亿元，EBITDA margin升至48.6%，显示出强劲的经营杠杆和成本效率。
Q8：GDS在过去三年内的收入增长趋势如何？
A8：GDS自2021至2024年持续增长，年均增长率超过15%，反映出数据中心市场的高景气度及其扩张策略的执行力。
三、运营数据分析
Q9：截至2025年Q1，GDS的服务面积与使用率是多少？
A9：服务面积为610,779平方米，使用面积为462,423平方米，使用率为75.7%，同比提升2.2个百分点。
Q10：GDS的预签约面积规模及变动趋势？
A10：2025年Q1预签约和签约总面积为649,561平方米，同比增长6.7%，显示出客户未来需求的可见性。
Q11：GDS的客户粘性表现如何？
A11：客户平均合同期超过7年，且以长期大客户为主，流失率极低，增强了收入的可预测性和稳定性。
四、成本结构与效率
Q12：GDS的运营成本控制表现如何？
A12：2025年Q1运营成本同比增长8.8%，低于营收增长12%，体现出良好的成本管控和规模效应。
Q13：研发投入在GDS运营中占比大吗？
A13：2025年Q1研发支出为人民币7.9百万元，占比不足0.3%，主要集中于运营系统和能效优化平台开发。
Q14：GDS的营销费用变动情况如何？
A14：2025年Q1营销费用同比增长12.2%，主要因销售人员成本上升，但绝对金额较小，费用率不到1%。
五、资本结构与风险
Q15：GDS的融资结构中ABS占比如何？
A15：2025年Q1完成首个数据中心资产证券化（ABS）交易，70%由机构投资者认购，30%由GDS自持，为其释放资本提供新路径。
Q16：GDS的利息支出趋势如何？
A16：2025年Q1利息净支出为人民币4.42亿元，同比下降4.5%，主要得益于总负债规模下降及融资利率下行。
Q17：公司是否存在汇率波动风险？
A17：GDS在2025年Q1录得小幅汇兑收益（人民币100万元），汇率波动影响有限，风险敞口管理良好。
六、非经常性项目分析
Q18：GDS为何在2025年Q1录得大额一次性收益？
A18：GDS在2025年初完成GDSI（国际业务）的权益剥离交易，确认人民币10.57亿元的非经常性处置收益。
Q19：GDS的资本支出趋势如何？
A19：2024年资本支出总额趋于下降，进入更有选择性的新项目开发阶段，有助于改善自由现金流状况。
Q20：GDS是否有配股或再融资计划？
A20：截至2024年底，暂无重大增发计划，管理层更倾向通过ABS及资产剥离优化资本结构。
七、客户与收入结构
Q25：GDS的客户集中度是否偏高？
A25：GDS前五大客户贡献过半收入，其中不乏全球互联网和云计算巨头，集中度高但签约周期长、稳定性强。
Q26：是否存在客户流失或终止合同情况？
A26：2024年Churn Rate始终保持低位（<1%），且合同期普遍超过7年，未出现重大流失风险迹象。
Q27：客户多样性如何体现？
A27：除Hyperscale客户外，GDS亦服务政府、金融、电商、游戏等多行业客户，部分项目采取B-O-T模式定制服务。
Q28：海外业务收入占比有多少？
A28：截至2024年，国际业务占比不高，且剥离后不再并表，2025年起仅作为权益法投资列示。
八、运营效率与规模效应
Q29：单位面积EBITDA是否持续提升？
A29：2025年Q1每平方米EBITDA提升约10%，主要因高密度客户上架与老旧资产利用率提升。
Q30：新建项目投产周期是否缩短？
A30：得益于标准化设计与供应链优化，2024年平均投产周期压缩至18个月内。
Q31：电力成本对运营利润的影响如何？
A31：电价占GDS成本中枢，2024年公司通过集中采购和能效优化控制电费波动，有效支撑毛利率改善。
Q32：单客户上架周期是否缩短？
A32：因客户扩容需求趋急，2025年Q1平均上架周期已缩短至3个月内，较2023年改善明显。
九、现金流与负债结构
Q33：GDS的自由现金流状况如何？
A33：2024年起，公司自由现金流由负转正，得益于资本开支控制、融资结构优化和运营现金流改善。
Q34：其资产负债率走势如何？
A34：2022-2024年负债率保持在60%-65%之间，略有下降，表明其资本结构在稳步改善中。
Q35：ABS融资为何重要？
A35：ABS作为非债务融资渠道，可释放数据中心资产价值，同时提升资产流动性和资本效率。
Q36：公司是否存在偿债压力？
A36：GDS通过滚动ABS和长期债替短期债降低短期偿债压力，现金流覆盖利息支出无明显问题。
十、管理与组织效率
Q37：管理费用是否处于可控水平？
A37：2025年Q1剔除摊销与股份费用后，G&A开支同比下降3.6%，显示其组织效率提升。
Q38：是否存在人力结构优化？
A38：2024年起公司压缩部分冗余岗位，并优化能效管理岗位配置，实现人均效能提升。
Q39：GDS是否发布ESG相关信息？
A39：GDS每年发布ESG报告，内容覆盖能耗管理、绿色建筑、人才发展等方面。
Q40：GDS是否披露网络安全管理政策？
A40：2024年起新增“网络安全披露”章节，涵盖数据防护、备份、SOC监控系统与客户合规机制。
十一、运营模式与发展路径
Q41：GDS采用自建还是租赁数据中心？
A41：GDS多数数据中心为自建或长期租赁用地建设，具备较强资产控制力，部分项目采用B-O-T方式满足特定客户需求。
Q42：GDS的数据中心在建规模有多大？
A42：截至2025年Q1，在建面积超过150,000平方米，其中近半项目已有预签约客户锁定。
Q43：预签约率对公司现金流有何帮助？
A43：预签约客户可提前支付订金与租金，帮助公司对冲建设期资金压力，优化现金流匹配。
Q44：公司是否具备模块化部署能力？
A44：GDS推行模块化建设，通过标准化设计和批量化建造，降低单位造价、缩短交付周期。
十二、风险管控与审计合规
Q45：GDS是否对收入确认进行审计确认？
A45：公司财报由毕马威（KPMG）审计，依据US GAAP收入确认准则，收入确认基于客户签署协议与数据中心交付状态。
Q46：财务报告是否存在调整或重述？
A46：截至2024年末，GDS无重大财务报表重述，亦未发生需追回激励薪酬的差错性更正事件。
Q47：GDS如何应对网络安全风险？
A47：公司设立SOC系统与应急响应机制，且2024年起披露相关策略，包括客户数据隔离、物理安防及加密技术使用。
Q48：是否披露供应链合规信息？
A48：GDS在ESG报告中列出主要设备供应商选择标准，包括节能性能、合规认证和交付能力等。
十三、收入结构与增长质量
Q151：2025年Q1 GDS的收入增长是由单价提升还是使用面积扩张驱动？
A151：收入同比增长12%，其中使用面积同比增长10%，价格因素提升约2%，主要源于高密度客户比重提升 。
Q152：预签约面积同比增长6.7%，是否预示未来收入增长存在提前锁定特征？
A152：是的，高预签约率确保建成即投用，平滑现金流周期，提高项目边际回报。
Q153：2025年Q1单位使用面积带来的收入变化趋势如何？
A153：单位面积营收小幅上升，反映AI负载客户占比上升，同时提升了单位EBITDA产出 。
Q154：海外业务剥离后是否对收入增长节奏造成影响？
A154：影响有限。海外业务已于2024年底出表，保留权益性持股，对并表收入影响可控 。
十四、EBITDA结构与成本效率
Q155：GDS的EBITDA提升主要来自哪三个方面？
A155：一是高密度客户上架带来的单位产出上升，二是运营效率提升压低边际成本，三是非经常性成本下降 。
Q156：调整后EBITDA Margin为何能从47.2%升至48.6%？
A156：成本增速低于收入增速，且部分固定支出摊薄，如项目规模化投入阶段结束。
Q157：高功率密度客户带来的EBITDA边际收益率是否更高？
A157：是的，其单位面积产出显著高于传统客户，尽管初始冷却与供电投资更大，但边际EBITDA更强。
Q158：毛利率从21.4%升至23.7%，是否反映成本结构持续优化？
A158：是的，主要因能源集中采购、设备利用率提升与AI智能化运维降低人工成本 。
十五、智能化运维与组织效率
Q175：DCP平台是否实现跨园区统一监控？
A175：DCP支持多园区统一监控与远程控制，实时采集电流、电压、环境数据，提升响应速度 。
Q176：智能安防系统对人员配置有无优化作用？
A176：部分园区通过机器人与摄像头巡检，替代夜班安保与部分人力岗位，提升人效 。
Q177：AI运维模型在节能中的作用如何体现？
A177：平台可根据负载预测调节冷却与电源输出，避免过度供给，平均节电效率提升5–8%。
Q178：GDS在组织层面是否设置节能KPI？
A178：运营与工程团队绩效考核中已纳入能耗指标，推动日常运行节能与设计端优化。
十六、资产质量与产出能力
Q179：单位面积EBITDA产出与轻资产运营商差距如何？
A179：GDS单位面积EBITDA高于轻资产运营商10–20%，主要因高密度客户与服务内容更完整 。
Q180：毛利率略低是否反映运营模式劣势？
A180：虽毛利率略低于轻资产玩家，但其折旧占比较高，调整后经营利润率具有竞争力。
Q181：在建项目预签约率是否影响资产投产即盈利的节奏？
A181：是的，高预签约率项目平均投产6个月内达产，回报周期大幅缩短。
Q182：2025年Q1使用率提升是否与AI客户上架密度有关？
A182：AI客户平均每机架功率更高，使得同等面积下实现更高产出和空间利用率 。
十七、行业地位与国际对比
Q183：GDS在全球第三方IDC运营商中处于什么水平？
A183：在中国本土中属龙头，在全球视野下服务定制化能力强，但互联密度与全球覆盖仍待加强。
Q184：与Equinix的商业模式有何根本区别？
A184：Equinix更重互联枢纽与网络交汇，而GDS侧重超大客户私有部署与定制化能力 。
Q185：GDS的PUE控制能力在亚洲同行中是否领先？
A185：目标PUE在1.3–1.4，领先于亚洲平均（1.5+），体现其冷却设计与AI控能平台的先进性。
Q186：未来是否可能探索区域性互联交换中心？
A186：若客户需求延伸至边缘数据交互场景，GDS有望联手运营商或云平台建立区域互联节点 。
十八、资本结构与风险承压能力
Q187：若未来融资利率上升，是否对ROIC构成压力？
A187：是的，GDS需通过更高的使用率与更快的投产周期提升项目内部收益率对冲融资成本 。
Q188：资产剥离是否会稀释未来长期现金流？
A188：短期内会减少稳定租金收入，但通过运营保留条款仍可收取服务费用，且释放资本用于扩张 。
Q189：资本开支下降是否意味着增长进入瓶颈？
A189：不一定，公司由高速扩张转向高质量增长阶段，项目筛选更聚焦回报与客户预期 。
Q190：未来三年ROE走势是否有改善空间？
A190：若自持项目投入产出加速兑现、费用率控制有效、利息支出下降，ROE存在回升空间。
        """
        
        # 检查是否有用户上传的自定义内容
        custom_content = None
        for filename in documents:
            if filename.lower().startswith('gds') or 'gds' in filename.lower() or '万国数据' in filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            custom_content = f.read()
                            break
                    except Exception as e:
                        logger.error(f"读取文件 {filename} 失败: {e}")
        
        # 返回自定义内容或默认内容
        return jsonify({
            'success': True,
            'content': custom_content if custom_content else default_intro
        })
        
    except Exception as e:
        logger.error(f"获取GDS介绍失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'content': "获取GDS万国数据介绍信息时发生错误"
        })

if __name__ == '__main__':
    print("🌐 启动简化版知识库Web界面...")
    print(f"📁 上传目录: {upload_dir}")
    # 从环境变量获取端口，默认为5000
    port = int(os.environ.get('FLASK_PORT', 5000))
    print(f"🔌 监听端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=True)