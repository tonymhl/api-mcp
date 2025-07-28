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
Q1：GDS的核心竞争优势是什么？A1：GDS通过深耕一线城市、长期锁定土地资源、自建自营的高可用性设施，以及提供定制化服务，形成了强大的客户粘性和高进入壁垒。
Q2：GDS的国际业务发展路径如何？A2：GDS于2022年设立GDS International（后更名为DayOne），负责海外市场拓展。截至2024年底，GDS已将其控股权出让，目前仅保留35.6%股权。
Q3：GDS为何采用“carrier-neutral”和“cloud-neutral”的运营策略？A3：该策略使GDS可服务多类客户，避免依赖单一电信运营商或云平台，提高设施复用率和网络互联灵活性，提升资产价值。
Q4：GDS的主要收入来源有哪些？A4：其主要收入来自数据中心租赁及运维服务，客户签订长期协议，按月计费，包括电力容量、机柜租赁、运维服务等。
二、财务结构与趋势
Q5：GDS的2025年Q1净利润变化趋势如何？A5：2025年Q1净利润为7.64亿元，显著扭亏为盈，主要因营收增长、运营成本控制和一次性处置收益（子公司权益剥离）。
Q6：GDS的毛利率水平是否稳定？A6：毛利率从2024年Q1的21.4%提升至2025年Q1的23.7%，主要得益于成本占比下降和规模效应提升。
Q7：调整后EBITDA和EBITDA Margin变动如何？A7：2025年Q1调整后EBITDA同比增长16.1%至13.24亿元，EBITDA margin升至48.6%，显示出强劲的经营杠杆和成本效率。
Q8：GDS在过去三年内的收入增长趋势如何？A8：GDS自2021至2024年持续增长，年均增长率超过15%，反映出数据中心市场的高景气度及其扩张策略的执行力。
三、运营数据分析
Q9：截至2025年Q1，GDS的服务面积与使用率是多少？A9：服务面积为610,779平方米，使用面积为462,423平方米，使用率为75.7%，同比提升2.2个百分点。
Q10：GDS的预签约面积规模及变动趋势？A10：2025年Q1预签约和签约总面积为649,561平方米，同比增长6.7%，显示出客户未来需求的可见性。
Q11：GDS的客户粘性表现如何？A11：客户平均合同期超过7年，且以长期大客户为主，流失率极低，增强了收入的可预测性和稳定性。
四、成本结构与效率
Q12：GDS的运营成本控制表现如何？A12：2025年Q1运营成本同比增长8.8%，低于营收增长12%，体现出良好的成本管控和规模效应。
Q13：研发投入在GDS运营中占比大吗？A13：2025年Q1研发支出为人民币7.9百万元，占比不足0.3%，主要集中于运营系统和能效优化平台开发。
Q14：GDS的营销费用变动情况如何？A14：2025年Q1营销费用同比增长12.2%，主要因销售人员成本上升，但绝对金额较小，费用率不到1%。
五、资本结构与风险
Q15：GDS的融资结构中ABS占比如何？A15：2025年Q1完成首个数据中心资产证券化（ABS）交易，70%由机构投资者认购，30%由GDS自持，为其释放资本提供新路径。
Q16：GDS的利息支出趋势如何？A16：2025年Q1利息净支出为人民币4.42亿元，同比下降4.5%，主要得益于总负债规模下降及融资利率下行。
Q17：公司是否存在汇率波动风险？A17：GDS在2025年Q1录得小幅汇兑收益（人民币100万元），汇率波动影响有限，风险敞口管理良好。
六、非经常性项目分析
Q18：GDS为何在2025年Q1录得大额一次性收益？A18：GDS在2025年初完成GDSI（国际业务）的权益剥离交易，确认人民币10.57亿元的非经常性处置收益。
Q19：GDS的资本支出趋势如何？A19：2024年资本支出总额趋于下降，进入更有选择性的新项目开发阶段，有助于改善自由现金流状况。
Q20：GDS是否有配股或再融资计划？A20：截至2024年底，暂无重大增发计划，管理层更倾向通过ABS及资产剥离优化资本结构。
七、战略调整与市场定位
Q21：GDS在国内市场的发展重心有无转移？A21：GDS仍将发展重心放在Tier 1城市，但在2024年后逐步向AI和超算驱动的新需求场景倾斜，如北京、长三角等区域出现更高密度订单。
Q22：GDS的国际化战略是否持续推进？A22：截至2025年，公司已将DayOne（原GDS International）股权出让至少数股东，意味着国际扩张已由战略优先项调整为财务投资项。
Q23：GDS是否采用轻资产模式拓展市场？A23：GDS开始采用“资产证券化+项目公司转让+运营服务保留”的轻重并举模式，如2025年ABS方案及DayOne处置案例。
Q24：GDS是否面临来自云厂商自建数据中心的竞争？A24：GDS强调中立性和灵活服务能力，与客户形成互补关系而非替代，且其大客户往往倾向于“外包部署+快速扩容”。
八、客户与收入结构
Q25：GDS的客户集中度是否偏高？A25：GDS前五大客户贡献过半收入，其中不乏全球互联网和云计算巨头，集中度高但签约周期长、稳定性强。
Q26：是否存在客户流失或终止合同情况？A26：2024年Churn Rate始终保持低位（<1%），且合同期普遍超过7年，未出现重大流失风险迹象。
Q27：客户多样性如何体现？A27：除Hyperscale客户外，GDS亦服务政府、金融、电商、游戏等多行业客户，部分项目采取B-O-T模式定制服务。
Q28：海外业务收入占比有多少？A28：截至2024年，国际业务占比不高，且剥离后不再并表，2025年起仅作为权益法投资列示。
九、运营效率与规模效应
Q29：单位面积EBITDA是否持续提升？A29：2025年Q1每平方米EBITDA提升约10%，主要因高密度客户上架与老旧资产利用率提升。
Q30：新建项目投产周期是否缩短？A30：得益于标准化设计与供应链优化，2024年平均投产周期压缩至18个月内。
Q31：电力成本对运营利润的影响如何？A31：电价占GDS成本中枢，2024年公司通过集中采购和能效优化控制电费波动，有效支撑毛利率改善。
Q32：单客户上架周期是否缩短？A32：因客户扩容需求趋急，2025年Q1平均上架周期已缩短至3个月内，较2023年改善明显。
十、现金流与负债结构
Q33：GDS的自由现金流状况如何？A33：2024年起，公司自由现金流由负转正，得益于资本开支控制、融资结构优化和运营现金流改善。
Q34：其资产负债率走势如何？A34：2022-2024年负债率保持在60%-65%之间，略有下降，表明其资本结构在稳步改善中。
Q35：ABS融资为何重要？A35：ABS作为非债务融资渠道，可释放数据中心资产价值，同时提升资产流动性和资本效率。
Q36：公司是否存在偿债压力？A36：GDS通过滚动ABS和长期债替短期债降低短期偿债压力，现金流覆盖利息支出无明显问题。
十一、管理与组织效率
Q37：管理费用是否处于可控水平？A37：2025年Q1剔除摊销与股份费用后，G&A开支同比下降3.6%，显示其组织效率提升。
Q38：是否存在人力结构优化？A38：2024年起公司压缩部分冗余岗位，并优化能效管理岗位配置，实现人均效能提升。
Q39：GDS是否发布ESG相关信息？A39：GDS每年发布ESG报告，内容覆盖能耗管理、绿色建筑、人才发展等方面。
Q40：GDS是否披露网络安全管理政策？A40：2024年起新增“网络安全披露”章节，涵盖数据防护、备份、SOC监控系统与客户合规机制。
十二、运营模式与发展路径
Q41：GDS采用自建还是租赁数据中心？A41：GDS多数数据中心为自建或长期租赁用地建设，具备较强资产控制力，部分项目采用B-O-T方式满足特定客户需求。
Q42：GDS的数据中心在建规模有多大？A42：截至2025年Q1，在建面积超过150,000平方米，其中近半项目已有预签约客户锁定。
Q43：预签约率对公司现金流有何帮助？A43：预签约客户可提前支付订金与租金，帮助公司对冲建设期资金压力，优化现金流匹配。
Q44：公司是否具备模块化部署能力？A44：GDS推行模块化建设，通过标准化设计和批量化建造，降低单位造价、缩短交付周期。
十三、风险管控与审计合规
Q45：GDS是否对收入确认进行审计确认？A45：公司财报由毕马威（KPMG）审计，依据US GAAP收入确认准则，收入确认基于客户签署协议与数据中心交付状态。
Q46：财务报告是否存在调整或重述？A46：截至2024年末，GDS无重大财务报表重述，亦未发生需追回激励薪酬的差错性更正事件。
Q47：GDS如何应对网络安全风险？A47：公司设立SOC系统与应急响应机制，且2024年起披露相关策略，包括客户数据隔离、物理安防及加密技术使用。
Q48：是否披露供应链合规信息？A48：GDS在ESG报告中列出主要设备供应商选择标准，包括节能性能、合规认证和交付能力等。
十四、资本市场与股东结构
Q49：GDS的主要股东有哪些？A49：截至2024年末，主要机构股东包括ST Telemedia、GIC、新加坡主权基金等，管理层亦通过B类股保留超额表决权。
Q50：GDS为何保留AB股结构？A50：AB股结构确保创始人对董事会的控制权，稳定公司战略执行，同时向公众发行A类普通股提高流动性。
Q51：公司是否进行过回购？A51：2024年无新增回购计划，公司更偏好保留现金支持项目建设与偿债，提升信用质量。
Q52：是否可能进行IPO分拆？A52：GDS曾考虑为GDS International独立融资，但已于2025年Q1完成股权出让，未进一步推进独立上市。
十五、行业对比与市场趋势
Q53：GDS在中国数据中心市场的地位如何？A53：GDS是中国领先的第三方中立数据中心运营商，服务于互联网头部客户，市场份额位列前列，仅次于万国数据（ChinaCache退出后）。
Q54：其收入增速相比行业平均如何？A54：2021-2024年年均复合营收增长率约为15%，高于中国IDC行业平均（约10%-12%）。
Q55：GDS毛利率与行业平均比较？A55：GDS近三年毛利率在21%-24%之间，略低于采用轻资产策略的数据中心服务商（如万国数据的部分云外包项目），但运营杠杆更强。
Q56：GDS的资本开支强度在行业中处于什么水平？A56：资本开支占营收比在40%-60%之间，属高资本密集型模式，资产沉淀大但单位EBITDA产出也较优。
十六、宏观环境与政策
Q57：中国政策对GDS有何影响？A57：政策鼓励绿色、集约型数据中心发展，GDS布局城市多数为国家级算力枢纽地区，政策扶持增强其项目可行性。
Q58：双碳政策是否影响GDS能源结构？A58：GDS正在引入可再生能源采购机制，并建设PUE≤1.4的绿色数据中心，积极响应双碳目标与客户低碳诉求。
Q59：中美科技摩擦对GDS有无影响？A59：公司强调其客户数据不涉军工与AI芯片核心技术，且多数设备采购本地化，受制裁风险低。
Q60：人民币汇率波动是否构成重大风险？A60：GDS以人民币计价为主，仅部分ABS融资以美元结算，汇率风险可控；如2025年Q1汇兑收益为人民币100万元。
十七、品牌与发展历程
Q61：万国数据（GDS）的成立时间与总部在哪里？A61：万国数据成立于2006年，总部位于中国上海浦东，是最早专注于第三方数据中心开发与运营的中资公司之一。
Q62：GDS为何选用“GDS Holdings Limited”作为国际名称？A62：GDS寓意“Global Data Solutions”，强调其国际化战略目标与中立服务定位。
Q63：GDS的上市历程如何？A63：GDS于2016年在纳斯达克挂牌上市（GDS.US），2020年在港交所二次上市（9698.HK），成为中概股中少有的双重上市数据中心企业。
Q64：GDS的创始人是谁？A64：公司由黄伟（William Wei Huang）创立，其为现任董事长兼CEO，拥有长期IT与电信行业背景，是GDS战略推动核心人物。
十八、客户结构与合作模式
Q65：GDS主要客户包含哪些知名企业？A65：主要客户包括阿里巴巴、腾讯、字节跳动、百度、美团等中国大型互联网企业，以及AWS、微软、谷歌等国际云厂商。
Q66：与Hyperscaler客户的合作方式是怎样的？A66：GDS通常与Hyperscaler签订5年以上的长期服务协议，提供定制化机柜、电力配置与运维交付支持，形成“贴身”部署。
Q67：GDS是否拥有B端客户的行业多样性？A67：GDS服务客户涵盖金融（如平安、招商）、电商、游戏、制造、政府等行业，业务覆盖从云到边缘多个场景。
Q68：GDS如何管理客户生命周期？A68：通过合同期、服务等级协议（SLA）、续约激励、故障响应平台及客户定期回访等机制，维系客户粘性。
十九、资产布局与扩张策略
Q69：GDS数据中心是否集中在东部沿海？A69：是的，GDS重点布局于北京、上海、深圳、广州、杭州、成都等核心城市，2023年后亦向环渤海和中西部拓展。
Q70：公司是否涉足边缘计算数据中心？A70：GDS目前重点仍在核心城域级数据中心，但未来考虑与边缘节点联动发展，如边缘缓存与AI训练节点协同。
Q71：未来三年GDS的新建项目集中在哪？A71：计划在上海临港、北京通州、深圳光明等区域推进绿色、低PUE数据中心园区，并加强园区规模化部署。
Q72：土地资源取得方式有哪些？A72：GDS通过自购、产业园区合作、政府招商引入等多种方式获取土地使用权或长期租赁权，保障项目供给连续性。
二十、技术投入与能效管理
Q73：GDS如何管理PUE（电源使用效率）？A73：公司新建项目目标PUE<1.4，采用冷热通道封闭、水冷系统、AI能耗监控平台优化运维能效。
Q74：是否引入绿色电力或碳中和机制？A74：GDS在深圳、北京项目尝试与绿电交易中心合作，引入可再生能源购电指标，并发布碳排放披露数据。
Q75：GDS是否设有技术创新部门？A75：公司设有研发中心与运营平台团队，开发数据中心智能监控平台（DCP）、智能运维机器人等系统。
Q76：在AI时代GDS有何布局？A76：GDS正与AI云客户合作部署高功率密度机房（>20kW/rack），提升冷却与供电能力，服务AI训练与推理场景。
二十一、治理与人才体系
Q77：GDS的治理结构是否透明？A77：GDS披露董事会架构、独立董事比例、审计与薪酬委员会设置等信息，符合中美两地上市规则要求。
Q78：公司是否实施股权激励？A78：设有长期激励计划，包括期权与限制性股票授予，覆盖高管与关键岗位人才，激励期一般为3-5年。
Q79：人才梯队建设方式？A79：通过“工程师+运维+能源+销售”四条职业路径，结合外部引才与内部培训（如数据中心学院）提升人才密度。
Q80：员工数量与增长情况？A80：截至2024年底，GDS员工总数超过2,800人，同比增长约9%，主要增长集中于项目建设与运维岗位。
二十二、未来增长与战略方向
Q81：未来三年GDS的主要增长引擎是什么？A81：主要来自AI应用场景（如AIGC、训练集群）驱动的高密度算力需求；一线城市新政推动数据中心产业集聚升级亦构成政策红利。
Q82：公司未来是否计划更大规模国际化？A82：原国际业务平台GDSI（今DayOne）已剥离控股权，未来国际化主要通过股权合作与基金参股方式参与。
Q83：GDS是否考虑向上游电力资产布局？A83：目前暂无自建电厂计划，但在尝试通过长期PPA（电力购买协议）或虚拟电厂模式保障绿电供给与能耗稳定性。
Q84：公司如何应对新一轮AI芯片能耗挑战？A84：已推进液冷机架、双回路供电及AI运维系统布设，计划支持NVIDIA H100等热功率达30-40kW/rack级别部署。
二十三、资本市场与投资者沟通
Q85：GDS的IR（投资者关系）机制如何？A85：GDS设有专职投资者关系团队，定期参与美港路演、财报电话会议、发布季度经营数据与客户签约更新。
Q86：公司如何回应ESG投资者关切？A86：自2021年起发布年度ESG报告，披露环境、员工、公司治理指标，持续强化绿色运维和社会责任履行能力。
Q87：公司是否参与行业指数或评级？A87：GDS被纳入MSCI中国中型股指数，亦参与恒生可持续发展指数评估，其ESG评级稳步提升中。
Q88：是否设有股东沟通机制？A88：除年度股东大会外，管理层每季度参与分析师会议，并通过邮件、社交平台与中小投资人互动。
二十四、行业政策与法规环境
Q89：中国数据中心行业准入政策是否收紧？A89：国家层面推行“算力枢纽+能耗双控”政策，GDS通过“规划+审批+绿电”三合一准入机制强化合规运营能力。
Q90：新一轮IDC备案监管对公司影响？A90：GDS项目多位于国家级园区内，政策稳定性较高，备案审批影响有限，反而提升其项目护城河。
Q91：是否受到数据跨境与信息保护监管影响？A91：GDS不直接处理客户数据内容，仅提供物理和网络基础设施，配合客户合规部署，风险可控。
Q92：公司是否参与行业协会与标准制定？A92：GDS为中国通信标准化协会成员，积极参与IDC节能标准制定与算力联盟等行业共建项目。
二十五、ESG治理与社会责任
Q93：GDS是否披露碳足迹数据？A93：自2022年起在ESG报告中披露范围一与二碳排放数据，并设定中长期碳强度下降目标。
Q94：公司在多样性与包容性方面有哪些举措？A94：GDS鼓励性别多元化，董事会女性比例达25%，运营团队设有多元文化培训计划。
Q95：是否开展社区共建活动？A95：GDS在部分项目地（如深圳、嘉兴）设立社区技能培训基地，开展公益编程、绿色科普等活动。
Q96：员工健康安全机制如何保障？A96：执行“零事故”管理制度，部署智能安防、巡检系统与突发应急演练，并为员工提供心理健康与家庭支持服务。
二十六、总结性判断
Q97：GDS的护城河体现在哪些方面？A97：深度绑定头部客户、城市核心资源布局能力、模块化快速交付体系、运维效率领先、客户续约率高构成其多重壁垒。
Q98：公司最大挑战可能来自哪些方面？A98：项目准入审批趋严、资本开支与负债管理平衡、高功率密度机房标准快速迭代、AI能耗与碳配额限制是主要挑战。
Q99：GDS相比轻资产IDC玩家有何差异？A99：GDS资产自持比例高，具备更强盈利杠杆与资产溢价能力，轻资产运营商（如世宏、城云）则更依赖代建与租赁利润。
Q100：GDS的长期价值是否受认可？A100：尽管短期受制资本成本与扩张节奏放缓，但长期高质量客户组合、城市中心位布局及AI算力红利支撑其价值重估潜力。
二十七、技术架构与能效管理
Q101：GDS采用何种供电冗余结构？A101：GDS数据中心普遍采用双回路供电（2N或N+1冗余）模式，支持关键负载的连续稳定运行。
Q102：液冷系统在GDS中的应用进展如何？A102：GDS已在部分AI训练集群部署液冷技术，支持高达30-40kW/rack的热密度，适应A100/H100等GPU部署需求。
Q103：模块化建设方式带来哪些效率提升？A103：模块化设计缩短交付周期至12-18个月内，单位造价降低5%-10%，且利于后期快速扩容与标准化运维。
Q104：GDS的平均PUE水平是多少？A104：新建项目目标PUE控制在1.3-1.4，优于行业平均水平（约1.5），通过冷热通道封闭、水冷与智能能效系统共同作用达成。
Q105：是否部署AI能效管理平台？A105：GDS自研智能能效平台，通过AI算法预测负载变化、动态调节空调负荷，实现节能与高效能运营平衡。
二十八、智能运维与监控平台
Q106：GDS是否采用集中监控系统？A106：采用统一的DCP（Data Center Platform）平台监控温度、电流、电压、网络状态等关键指标，实现多园区集中管理。
Q107：是否引入机器人或无人值守系统？A107：部分数据中心部署机器人巡检系统与远程操作台，提高夜间巡检效率与故障响应速度。
Q108：GDS如何提升设备故障预警能力？A108：引入AI预测模型，对UPS、电池、电缆发热进行异常识别，减少非计划停机事件。
Q109：对智能化客户自服务平台有无部署？A109：客户可通过GDS平台远程查看机架用电、温度、上架情况并进行报修、授权等操作，提升客户控制力。
Q110：是否支持多租户资源隔离？A110：采用虚拟资源隔离与物理分区结合的方式，满足金融、政企客户对合规与数据隔离的高要求。
二十九、网络安全与灾备能力
Q111：GDS的数据中心如何实现物理安全？A111：设有多级门禁、视频监控、巡更系统，并实行机柜层级访问授权控制。
Q112：网络层面如何实现入侵防御？A112：部署防火墙、DDoS防御系统及IDS入侵检测系统，并设立客户专属VLAN通道。
Q113：是否具备异地灾备能力？A113：为金融客户提供“异地三中心”解决方案，支持异地热备、数据库双活、秒级切换等功能。
Q114：GDS是否参与数据安全合规认证？A114：通过ISO27001、等保三级、SOC2等多项安全认证，符合云计算和金融业监管合规要求。
Q115：对新兴网络攻击（如勒索软件）有无策略？A115：与主流杀毒厂商合作，定期更新签名库，并建立应急响应流程与演练机制。
三十、AI高密度算力支持与芯片适配
Q116：GDS能支持多少功率密度的机架？A116：部分园区支持40kW/rack的高热密度机柜，远高于传统8-12kW水平，满足AI算力需求。
Q117：是否兼容主流AI芯片厂商的部署要求？A117：GDS设计可适配NVIDIA H100、Google TPU、AMD Instinct等主流AI加速卡的冷却与供电需求。
Q118：AI集群是否使用GPU专属区域部署？A118：部分AI客户租用整层甚至整栋作为AI训练集群部署，GDS提供专属供电与液冷通道保障散热。
Q119：在AI项目中采用何种冷却系统？A119：在超高热负载场景下使用液冷+热回收系统，确保系统稳定同时提升能源利用效率。
Q120：AI业务对整体PUE有何影响？A120：尽管AI业务单点能耗高，但冷却系统效率提升使得边际PUE控制在合理区间，对总能效影响受控。
三十一、国际对比与技术路径
Q121：与Equinix相比GDS有哪些优势？A121：GDS在中国本地政企资源、土地获取效率与定制化服务能力上具优势，但在全球互联密度与资产周转率方面仍逊色。
Q122：与Digital Realty在AI适配能力方面如何对比？A122：GDS在AI部署密度（>30kW/rack）与液冷试点领先国内同行，与Digital Realty高密度方案接近。
Q123：GDS与万国数据在架构侧有何差异？A123：GDS偏向自持型大园区建设，万国数据近年则更多采用轻资产与边缘节点策略，模式差异体现于负债结构与灵活性上。
Q124：PUE控制路径是否参照国际标准？A124：GDS设计参考ASHRAE标准与Uptime TIER III规范，且逐步向TIER IV与碳中和工艺靠拢。
Q125：是否有尝试“绿色算力”标签化运营？A125：GDS在北京、深圳项目申请绿色算力备案与绿电指标配额，提升客户绿色IT部署吸引力。
Q126：GDS如何实现多个数据中心的集中管控？A126：采用自研DCP平台，实现机电设备、环境状态、能源使用、客户用量的实时集中可视与远程控制。
Q127：DCP是否具备自动化告警与修复功能？A127：系统内置故障诊断模型与容错机制，支持基于规则的自动告警联动响应，提升MTTR效率。
Q128：是否具备跨园区负载调度能力？A128：通过SDN虚拟网络与边缘调度节点，部分高等级客户可实现资源在不同园区间的灾备级切换。
Q129：多园区是否使用统一标准建设？A129：GDS推行标准化机房模块体系，90%以上设备采用同品牌同规格采购，便于批量维护和备件通用。
Q130：园区间是否共享智能能效数据？A130：各数据中心能效数据同步至总部数据湖平台，供AI建模训练，优化区域整体冷却与能源效率。
三十二、边缘计算与新场景支持
Q131：GDS是否涉足边缘计算节点建设？A131：GDS在2024年起布局边缘缓存与AI inference节点，如在电商和OTT客户附近部署5-20机架的小型IDC。
Q132：边缘节点是否支持GPU负载？A132：新一代边缘模块支持4-8路GPU部署，适用于实时视频处理、语音识别、物联网场景推理需求。
Q133：边缘IDC是否采用一体化封装？A133：采用预制模块化箱体，包含UPS、制冷、网络与安全控制，可快速部署、便于搬迁与扩容。
Q134：GDS如何选择边缘节点位置？A134：基于客户CDN、用户访问密度、光缆节点聚集度进行部署选址，兼顾成本与业务流量分布。
Q135：边缘节点对收入结构影响如何？A135：目前占比仍低，但未来在AI推理、智能制造、智慧城市等领域有望成为新增量来源。
三十三、绿色能源与碳中和路径
Q136：GDS是否签署PPA协议获取绿电？A136：公司正与国家电网和地方绿电交易中心合作签订长期PPA，锁定绿电采购价格与供给稳定性。
Q137：绿电在整体电力使用中占比多少？A137：截至2024年绿电占比约8%，计划在2027年前提升至30%以上，逐步减少碳足迹。
Q138：GDS是否参与碳交易市场？A138：目前已在广东碳市场备案，正筹备进入国家级碳排放权交易系统，具备碳配额管理能力。
Q139：是否推动客户购买绿色IDC服务？A139：提供“绿色算力”标签服务选项，向客户提供PUE/碳强度报告，吸引ESG导向型企业签约。
Q140：在能耗KPI方面对员工是否考核？A140：公司将单位能耗下降目标纳入运营与工程团队KPI中，鼓励节能创新实践。
三十四、客户需求演化与IT战略适配
Q141：客户IT基础设施有何变化趋势？A141：客户从传统服务器迁移至AI-GPU集群，平均功率密度提高一倍以上，对冷却系统与供电提出新要求。
Q142：GDS是否支持私有云与混合云部署？A142：提供灵活的网络接入与SD-WAN支持，客户可在GDS数据中心部署私有云并连接公有云平台。
Q143：客户对网络带宽与时延有何新要求？A143：AI训练与推理对低时延要求增强，GDS通过BGP优化与直连POP点布局，降低网络链路时延。
Q144：是否协助客户完成系统上架与迁移？A144：GDS提供TIS（技术集成服务），包括硬件上架、布线、配置、测试与系统切换等一站式交付。
Q145：客户对服务等级协议（SLA）要求是否提升？A145：AI与金融客户SLA要求普遍提升至99.999%可用性水平，GDS已提供5级容灾设计与多路径供电保障。
三十五、研发体系与技术演进
Q146：GDS的技术研发组织架构如何？A146：公司设有“智能运维、AI平台、能效建模”三大研发方向，由CTO牵头跨部门协同。
Q147：是否参与开源社区或技术联盟？A147：GDS参与ODCC开放数据中心委员会与算力基础设施标准组，推动液冷、AI标准化建设。
Q148：对智能布线与电力调度是否有自研工具？A148：自研布线仿真平台与电流负载预测系统，支持在项目设计阶段即预判风险负载分布。
Q149：研发投入强度处于行业何种水平？A149：虽占比不足1%，但重投入于工程优化与平台工具，技术人均产出处于行业前列。
Q150：GDS未来三年研发重点将聚焦哪些方向？A150：重点聚焦AI负载热能管理、液冷集成度提升、客户IT可视化工具与碳中和追踪机制。
三十六、收入结构与增长质量
Q151：2025年Q1 GDS的收入增长是由单价提升还是使用面积扩张驱动？A151：收入同比增长12%，其中使用面积同比增长10%，价格因素提升约2%，主要源于高密度客户比重提升 。
Q152：预签约面积同比增长6.7%，是否预示未来收入增长存在提前锁定特征？A152：是的，高预签约率确保建成即投用，平滑现金流周期，提高项目边际回报。
Q153：2025年Q1单位使用面积带来的收入变化趋势如何？A153：单位面积营收小幅上升，反映AI负载客户占比上升，同时提升了单位EBITDA产出 。
Q154：海外业务剥离后是否对收入增长节奏造成影响？A154：影响有限。海外业务已于2024年底出表，保留权益性持股，对并表收入影响可控 。
三十七、EBITDA结构与成本效率
Q155：GDS的EBITDA提升主要来自哪三个方面？A155：一是高密度客户上架带来的单位产出上升，二是运营效率提升压低边际成本，三是非经常性成本下降 。
Q156：调整后EBITDA Margin为何能从47.2%升至48.6%？A156：成本增速低于收入增速，且部分固定支出摊薄，如项目规模化投入阶段结束。
Q157：高功率密度客户带来的EBITDA边际收益率是否更高？A157：是的，其单位面积产出显著高于传统客户，尽管初始冷却与供电投资更大，但边际EBITDA更强。
Q158：毛利率从21.4%升至23.7%，是否反映成本结构持续优化？A158：是的，主要因能源集中采购、设备利用率提升与AI智能化运维降低人工成本 。
三十八、现金流与资本效率
Q159：自由现金流由负转正的核心原因有哪些？A159：一是资本开支收缩，二是运营现金流持续改善，三是资产证券化（ABS）释放部分已投资产价值 。
Q160：2025年Q1净利润为何大幅改善至7.64亿元？A160：除经营改善外，还包括约10.57亿元来自GDS International股权剥离的一次性收益 。
Q161：利息支出同比下降是否源于债务结构变化？A161：是的，公司通过ABS等工具优化了债务成本，降低整体融资利率 。
Q162：资产证券化在释放资本方面效果如何？A162：首个ABS项目70%外部认购，显著提升资产周转率并回笼资金，用于后续项目投资 。
三十九、AI业务增长动能与结构变化
Q163：AI相关客户在GDS整体收入中的占比是否提升？A163：虽然未单列披露，但AI集群部署带动高密度区域机房使用率与单价提升，是主要增长动因之一 。
Q164：GDS如何保障AI训练所需电力与冷却？A164：通过液冷部署、2N供电、模块化设计满足>30kW/rack机架的持续供电和散热需求。
Q165：AI集群项目的投产周期是否更短？A165：部分高优先级AI项目采用快速部署模式，周期压缩至12–14个月内，加快产出兑现。
Q166：AI客户生命周期价值（LTV）是否更高？A166：是的，AI客户合同周期更长、部署密度更高、复购概率更强，单位LTV高于传统互联网客户。
四十、业务模式对资本效率的影响
Q167：重资产自建与轻资产运营的资本效率差异有多大？A167：自建模式ROIC略低但单位EBITDA产出更高，适合头部客户长期绑定；轻资产则提高灵活性与回报周期。
Q168：BOT（建造-运营-移交）模式是否影响资产沉淀？A168：BOT模式可减少表内资产增加，适用于大客户定制型需求，有助于提升资产周转率。
Q169：ABS释放出的资产未来是否仍可带来运营收入？A169：ABS项目多数保留运营权与服务合同，GDS仍享有稳定运维收入与客户关系。
Q170：项目转让是否影响GDS的客户粘性？A170：通过“服务保留”机制确保客户体验与原协议延续，未显著削弱客户关系稳定性。
Q171：GDS项目开发周期是否显著优于行业平均？A171：GDS通过模块化建设与标准化流程，将平均交付周期压缩至18个月内，快于行业常规24个月水平 。
Q172：城市选址策略是否影响项目投产效率？A172：核心城市如北京、上海具备电力接入、客户集中与政策支持优势，有效缩短审批与投运周期 。
Q173：GDS如何在多个项目同时推进中保障交付质量？A173：采用统一设计标准、批量采购与分区运维团队制度，提升工程管理一致性 。
Q174：与AI客户的项目交付是否设置专属通道？A174：为满足AI客户快速部署需求，部分高优先级项目设置专属调度团队与绿色审批机制 。
四十一、智能化运维与组织效率
Q175：DCP平台是否实现跨园区统一监控？A175：DCP支持多园区统一监控与远程控制，实时采集电流、电压、环境数据，提升响应速度 。
Q176：智能安防系统对人员配置有无优化作用？A176：部分园区通过机器人与摄像头巡检，替代夜班安保与部分人力岗位，提升人效 。
Q177：AI运维模型在节能中的作用如何体现？A177：平台可根据负载预测调节冷却与电源输出，避免过度供给，平均节电效率提升5–8%。
Q178：GDS在组织层面是否设置节能KPI？A178：运营与工程团队绩效考核中已纳入能耗指标，推动日常运行节能与设计端优化。
四十二、资产质量与产出能力
Q179：单位面积EBITDA产出与轻资产运营商差距如何？A179：GDS单位面积EBITDA高于轻资产运营商10–20%，主要因高密度客户与服务内容更完整 。
Q180：毛利率略低是否反映运营模式劣势？A180：虽毛利率略低于轻资产玩家，但其折旧占比较高，调整后经营利润率具有竞争力。
Q181：在建项目预签约率是否影响资产投产即盈利的节奏？A181：是的，高预签约率项目平均投产6个月内达产，回报周期大幅缩短。
Q182：2025年Q1使用率提升是否与AI客户上架密度有关？A182：AI客户平均每机架功率更高，使得同等面积下实现更高产出和空间利用率 。
四十三、行业地位与国际对比
Q183：GDS在全球第三方IDC运营商中处于什么水平？A183：在中国本土中属龙头，在全球视野下服务定制化能力强，但互联密度与全球覆盖仍待加强。
Q184：与Equinix的商业模式有何根本区别？A184：Equinix更重互联枢纽与网络交汇，而GDS侧重超大客户私有部署与定制化能力 。
Q185：GDS的PUE控制能力在亚洲同行中是否领先？A185：目标PUE在1.3–1.4，领先于亚洲平均（1.5+），体现其冷却设计与AI控能平台的先进性。
Q186：未来是否可能探索区域性互联交换中心？A186：若客户需求延伸至边缘数据交互场景，GDS有望联手运营商或云平台建立区域互联节点 。
四十四、资本结构与风险承压能力
Q187：若未来融资利率上升，是否对ROIC构成压力？A187：是的，GDS需通过更高的使用率与更快的投产周期提升项目内部收益率对冲融资成本 。
Q188：资产剥离是否会稀释未来长期现金流？A188：短期内会减少稳定租金收入，但通过运营保留条款仍可收取服务费用，且释放资本用于扩张 。
Q189：资本开支下降是否意味着增长进入瓶颈？A189：不一定，公司由高速扩张转向高质量增长阶段，项目筛选更聚焦回报与客户预期 。
Q190：未来三年ROE走势是否有改善空间？A190：若自持项目投入产出加速兑现、费用率控制有效、利息支出下降，ROE存在回升空间。
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
    # 从环境变量获取端口，默认为5001
    port = int(os.environ.get('FLASK_PORT', 5001))
    print(f"🔌 监听端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=True)