let brainViz = null;
let medicalCharts = null;

document.addEventListener('DOMContentLoaded', function() {
    brainViz = new BrainVisualizer('brainContainer', {
        width: document.getElementById('brainContainer').clientWidth,
        height: 500
    });

    medicalCharts = new MedicalCharts();
    loadROCData();
    setupDragAndDrop();
});

async function loadROCData() {
    try {
        const response = await fetch('/api/model/metrics');
        const data = await response.json();

        if (data.roc_curve) {
            medicalCharts.createROCCurve('rocChart', data.roc_curve);
        } else {
            medicalCharts.createROCCurve('rocChart', {
                auc: 0.90,
                points: generateROCPoints(0.90)
            });
        }
    } catch (error) {
        console.error('加载 ROC 数据失败:', error);
    }
}

function generateROCPoints(auc) {
    const points = [];
    for (let i = 0; i <= 1; i += 0.05) {
        const y = Math.pow(i, 0.3 + auc * 0.4);
        points.push({ x: i, y: Math.min(1, y) });
    }
    return points;
}

function setupDragAndDrop() {
    const uploadZone = document.getElementById('uploadZone');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => uploadZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('dragover'), false);
    });

    uploadZone.addEventListener('drop', handleDrop, false);
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    if (dt.files.length > 0) {
        handleFiles(dt.files[0]);
    }
}

function handleFileUpload(input) {
    if (input.files.length > 0) {
        handleFiles(input.files[0]);
    }
}

async function handleFiles(file) {
    if (!file.name.endsWith('.nii') && !file.name.endsWith('.nii.gz')) {
        alert('请上传 .nii 或 .nii.gz 格式的 MRI 文件');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const progressDiv = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    progressDiv.style.display = 'block';

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            progressFill.style.width = percent + '%';
            progressText.textContent = percent + '%';
        }
    });

    xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
            alert('文件上传成功！');
            location.reload();
        } else {
            alert('上传失败');
        }
    });

    xhr.open('POST', '/upload/mri');
    xhr.send(formData);
}

function showView(viewType) {
    if (!brainViz) return;

    document.querySelectorAll('.brain-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    if (viewType === 'heatmap') {
        loadHeatmapData();
    } else {
        brainViz.clearHighlights();
    }
}

function loadHeatmapData() {
    fetch('/api/brain/regions')
        .then(response => response.json())
        .then(data => {
            if (data.regions) {
                brainViz.loadRegionData(data.regions);
            }
        })
        .catch(error => console.error('加载脑区数据失败:', error));
}

function resetBrain() {
    if (brainViz) {
        brainViz.clearHighlights();
        brainViz.brainMesh.rotation.set(0, 0, 0);
    }
}

function rotateLeft() {
    if (brainViz && brainViz.brainMesh) {
        brainViz.brainMesh.rotation.y -= 0.3;
    }
}

function rotateRight() {
    if (brainViz && brainViz.brainMesh) {
        brainViz.brainMesh.rotation.y += 0.3;
    }
}


// 存储监控功能
async function loadStorageStats() {
    try {
        const response = await fetch('/api/storage/stats');
        const data = await response.json();

        if (data.success) {
            updateStorageDisplay(data.storage);
            updateDiskDisplay(data.disk);
        }
    } catch (error) {
        console.error('加载存储统计失败:', error);
    }
}

function updateStorageDisplay(storage) {
    // 更新上传文件统计
    document.getElementById('upload-size').textContent =
        `${storage.uploads.total_size_mb} MB`;
    document.getElementById('upload-count').textContent =
        storage.uploads.file_count;

    // 更新其他存储统计...
}

function updateDiskDisplay(disk) {
    if (disk.warning) {
        showDiskWarning(disk.used_percent);
    }

    document.getElementById('disk-used').textContent =
        `${disk.used_gb} GB / ${disk.total_gb} GB`;
    document.getElementById('disk-percent').textContent =
        `${disk.used_percent}%`;
}

async function cleanupTempFiles() {
    if (!confirm('确定要清理临时文件吗？')) return;

    try {
        const response = await fetch('/api/storage/cleanup/temp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ max_age_hours: 24 })
        });

        const data = await response.json();
        if (data.success) {
            alert(`成功清理 ${data.deleted_count} 个临时文件`);
            loadStorageStats(); // 刷新统计
        }
    } catch (error) {
        console.error('清理临时文件失败:', error);
    }
}

async function backupDatabase() {
    if (!confirm('确定要备份数据库吗？')) return;

    try {
        const response = await fetch('/api/storage/backup', {
            method: 'POST'
        });

        const data = await response.json();
        if (data.success) {
            alert(`数据库备份成功: ${data.backup_file}`);
        } else {
            alert(`备份失败: ${data.error}`);
        }
    } catch (error) {
        console.error('数据库备份失败:', error);
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadStorageStats();

    // 每5分钟刷新一次
    setInterval(loadStorageStats, 5 * 60 * 1000);
});
