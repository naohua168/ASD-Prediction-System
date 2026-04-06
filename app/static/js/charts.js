class MedicalCharts {
    constructor() {
        this.charts = {};
    }

    createROCCurve(canvasId, rocData) {
        const ctx = document.getElementById(canvasId).getContext('2d');

        this.charts.roc = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'ROC 曲线',
                    data: rocData.points || [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: '随机猜测',
                    data: [{x: 0, y: 0}, {x: 1, y: 1}],
                    borderColor: '#9ca3af',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        title: { display: true, text: '假阳性率 (1 - Specificity)' },
                        min: 0,
                        max: 1
                    },
                    y: {
                        title: { display: true, text: '真阳性率 (Sensitivity)' },
                        min: 0,
                        max: 1
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: `ROC 曲线 (AUC = ${rocData.auc || 'N/A'})`,
                        font: { size: 16 }
                    }
                }
            }
        });
    }

    createConfusionMatrix(canvasId, matrix) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const width = ctx.canvas.width;
        const height = ctx.canvas.height;
        const cellWidth = width / 3;
        const cellHeight = height / 3;

        ctx.clearRect(0, 0, width, height);

        ctx.fillStyle = '#1f2937';
        ctx.font = 'bold 16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('混淆矩阵', width / 2, 30);

        const maxValue = Math.max(matrix.tp, matrix.fn, matrix.fp, matrix.tn);

        const cells = [
            { x: 1, y: 1, value: matrix.tp, label: `TP: ${matrix.tp}` },
            { x: 2, y: 1, value: matrix.fn, label: `FN: ${matrix.fn}` },
            { x: 1, y: 2, value: matrix.fp, label: `FP: ${matrix.fp}` },
            { x: 2, y: 2, value: matrix.tn, label: `TN: ${matrix.tn}` }
        ];

        cells.forEach(cell => {
            const intensity = cell.value / maxValue;
            const blue = Math.floor(37 + (255 - 37) * intensity);
            ctx.fillStyle = `rgb(${255 - blue}, ${255 - blue}, 255)`;
            ctx.fillRect(cell.x * cellWidth, cell.y * cellHeight, cellWidth - 5, cellHeight - 5);

            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(cell.label, cell.x * cellWidth + cellWidth / 2, cell.y * cellHeight + cellHeight / 2);
        });
    }

    createScatterPlot(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');

        this.charts.scatter = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'ASD 患者',
                    data: data.asd || [],
                    backgroundColor: 'rgba(239, 68, 68, 0.6)',
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    pointRadius: 5
                }, {
                    label: '正常对照',
                    data: data.nc || [],
                    backgroundColor: 'rgba(16, 185, 129, 0.6)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: data.xLabel || 'ADOS 评分' } },
                    y: { title: { display: true, text: data.yLabel || '预测概率' } }
                },
                plugins: {
                    title: { display: true, text: '临床评分与预测概率相关性', font: { size: 16 } }
                }
            }
        });
    }

    createRegionVolumeChart(canvasId, regionData) {
        const ctx = document.getElementById(canvasId).getContext('2d');

        const labels = Object.keys(regionData).slice(0, 10);
        const values = labels.map(key => regionData[key].volume || 0);

        this.charts.volume = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '灰质体积 (体素数)',
                    data: values,
                    backgroundColor: 'rgba(59, 130, 246, 0.6)',
                    borderColor: '#3b82f6',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: '关键脑区灰质体积', font: { size: 16 } }
                }
            }
        });
    }

    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) chart.destroy();
        });
        this.charts = {};
    }
}

window.MedicalCharts = MedicalCharts;
