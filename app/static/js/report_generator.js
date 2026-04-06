// 文件路径: E:\自闭症\ASD-Prediction-System\app\static\js\report_generator.js

class ReportGenerator {
    constructor() {
        this.reportData = null;
    }

    async generateReport(patientData, analysisResult, brainData) {
        this.reportData = {
            patient: patientData,
            analysis: analysisResult,
            brain: brainData,
            timestamp: new Date().toISOString()
        };

        const printWindow = window.open('', '_blank');
        const html = this.createReportHTML();

        printWindow.document.write(html);
        printWindow.document.close();

        setTimeout(() => {
            printWindow.print();
        }, 500);
    }

    createReportHTML() {
        const { patient, analysis, brain } = this.reportData;

        return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ASD 诊断分析报告 - ${patient.name}</title>
    <style>
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 40px; 
            color: #1f2937; 
            line-height: 1.6; 
        }
        .header { 
            text-align: center; 
            border-bottom: 3px solid #2563eb; 
            padding-bottom: 20px; 
            margin-bottom: 30px; 
        }
        .header h1 { 
            color: #2563eb; 
            margin: 0; 
            font-size: 28px; 
        }
        .section { 
            margin-bottom: 30px; 
        }
        .section-title { 
            color: #2563eb; 
            font-size: 20px; 
            border-left: 4px solid #2563eb; 
            padding-left: 10px; 
            margin-bottom: 15px; 
        }
        .info-grid { 
            display: grid; 
            grid-template-columns: repeat(2, 1fr); 
            gap: 15px; 
        }
        .info-item { 
            padding: 10px; 
            background: #f9fafb; 
            border-radius: 5px; 
        }
        .info-label { 
            font-size: 12px; 
            color: #6b7280; 
            text-transform: uppercase; 
        }
        .info-value { 
            font-size: 16px; 
            font-weight: bold; 
        }
        .result-box { 
            background: #eff6ff; 
            border: 2px solid #2563eb; 
            border-radius: 10px; 
            padding: 20px; 
            text-align: center; 
            margin: 20px 0; 
        }
        .prediction { 
            font-size: 36px; 
            font-weight: bold; 
            color: #2563eb; 
            margin: 10px 0; 
        }
        .probability { 
            font-size: 24px; 
            color: #6b7280; 
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 15px; 
        }
        th, td { 
            padding: 10px; 
            text-align: left; 
            border-bottom: 1px solid #e5e7eb; 
        }
        th { 
            background: #f9fafb; 
            font-weight: 600; 
        }
        .recommendations {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            border-radius: 8px;
        }
        .recommendations ul {
            margin: 10px 0 0 20px;
        }
        .recommendations li {
            margin-bottom: 8px;
        }
        @media print { 
            body { margin: 20px; }
            .no-print { display: none; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>ASD 诊断分析报告</h1>
        <p>基于结构磁共振成像的自闭症谱系障碍预测系统</p>
        <p>报告生成时间: ${new Date().toLocaleString('zh-CN')}</p>
    </div>
    
    <div class="section">
        <h2 class="section-title">患者信息</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">患者ID</div>
                <div class="info-value">${patient.id}</div>
            </div>
            <div class="info-item">
                <div class="info-label">姓名</div>
                <div class="info-value">${patient.name}</div>
            </div>
            <div class="info-item">
                <div class="info-label">年龄</div>
                <div class="info-value">${patient.age} 岁</div>
            </div>
            <div class="info-item">
                <div class="info-label">性别</div>
                <div class="info-value">${patient.gender === 'male' ? '男' : '女'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">全量表智商</div>
                <div class="info-value">${patient.full_scale_iq || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">ADOS-G评分</div>
                <div class="info-value">${patient.ados_g_score || 'N/A'}</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2 class="section-title">AI预测结果</h2>
        <div class="result-box" style="background: ${analysis.prediction === 'ASD' ? '#fee2e2' : '#d1fae5'}; border-color: ${analysis.prediction === 'ASD' ? '#ef4444' : '#10b981'};">
            <div style="font-size: 14px; color: #6b7280;">诊断预测</div>
            <div class="prediction" style="color: ${analysis.prediction === 'ASD' ? '#ef4444' : '#10b981'};">
                ${analysis.prediction === 'ASD' ? '自闭症谱系障碍 (ASD)' : '正常对照 (NC)'}
            </div>
            <div class="probability">置信度: ${(analysis.confidence * 100).toFixed(2)}%</div>
            <div style="margin-top: 10px; font-size: 14px; color: #6b7280;">
                ASD概率: ${(analysis.probability * 100).toFixed(2)}% | 
                NC概率: ${((1 - analysis.probability) * 100).toFixed(2)}%
            </div>
        </div>
    </div>
    
    ${brain && brain.region_values ? `
    <div class="section">
        <h2 class="section-title">关键脑区灰质体积分析</h2>
        <table>
            <thead>
                <tr>
                    <th>脑区</th>
                    <th>平均体积</th>
                    <th>中位数</th>
                    <th>标准差</th>
                    <th>总体积</th>
                </tr>
            </thead>
            <tbody>
                ${Object.entries(brain.region_values).map(([region, data]) => `
                <tr>
                    <td><strong>${region}</strong></td>
                    <td>${data.mean?.toFixed(2) || 'N/A'}</td>
                    <td>${data.median?.toFixed(2) || 'N/A'}</td>
                    <td>${data.std?.toFixed(2) || 'N/A'}</td>
                    <td>${data.volume || 'N/A'}</td>
                </tr>
                `).join('')}
            </tbody>
        </table>
    </div>
    ` : ''}
    
    <div class="section">
        <h2 class="section-title">模型性能指标</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">准确率</div>
                <div class="info-value">85%</div>
            </div>
            <div class="info-item">
                <div class="info-label">灵敏度</div>
                <div class="info-value">82%</div>
            </div>
            <div class="info-item">
                <div class="info-label">特异度</div>
                <div class="info-value">88%</div>
            </div>
            <div class="info-item">
                <div class="info-label">AUC-ROC</div>
                <div class="info-value">0.90</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2 class="section-title">临床建议</h2>
        <div class="recommendations">
            <ul>
                <li>本分析结果基于结构磁共振成像数据，仅供参考</li>
                <li>建议结合ADOS、ADI-R等标准化评估工具进行综合诊断</li>
                <li>定期随访观察行为发展和社交能力变化</li>
                <li>早期干预对改善预后具有重要意义</li>
                <li>建议多学科团队协作制定个性化干预方案</li>
            </ul>
        </div>
    </div>
    
    <div class="footer" style="margin-top: 50px; text-align: center; color: #6b7280; font-size: 12px; border-top: 1px solid #e5e7eb; padding-top: 20px;">
        <p>本报告由ASD预测系统自动生成 | 仅供医疗专业人员参考</p>
        <p>模型版本: ${analysis.model_version || 'v1.0'} | 分析时间: ${new Date(analysis.created_at).toLocaleString('zh-CN')}</p>
    </div>
    
    <div class="no-print" style="position: fixed; bottom: 20px; right: 20px;">
        <button onclick="window.print()" style="padding: 12px 24px; background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px;">
            <i class="fas fa-print"></i> 打印报告
        </button>
    </div>
</body>
</html>`;
    }
}

window.ReportGenerator = ReportGenerator;
