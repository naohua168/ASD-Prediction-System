# 🧠 MRI预处理可视化 - 快速参考卡

## 🚀 一行命令启动

```bash
# 1. 执行带预处理的分析
python -c "from tasks.analysis_tasks import submit_analysis_task; print(submit_analysis_task(1, 1, 1, use_preprocessing=True))"

# 2. 访问QC报告
# http://localhost:5000/preprocessing/qc-report/1

# 3. 运行测试
python tests/test_visualization.py
```

---

## 📋 API速查

### 提交预处理任务
```javascript
POST /analysis/start
{
    "mri_scan_id": 1,
    "use_preprocessing": true  // ✅ 关键参数
}
```

### 获取NIfTI文件
```
GET /api/files/nifti?path=/absolute/path/to/file.nii.gz
Headers: Cookie: session=xxx (需要登录)
```

### 查询MRI信息
```
GET /api/mri-scans/1
Response: { "file_path": "...", "original_filename": "..." }
```

---

## 🎮 可视化控件

| 按钮 | 功能 | 快捷键 |
|------|------|--------|
| 🔵 原始图像 | 显示上传的原始文件 | - |
| 🟢 预处理后 | 显示处理后的图像 | - |
| 🟣 脑掩膜 | 显示去颅骨结果 | - |
| 🟠 对比模式 | 左右并排对比 | - |

**交互操作:**
- 鼠标滚轮 → 缩放
- 鼠标拖拽 → 平移
- 滑块拖动 → 切换切片

---

## 📁 文件位置

```
data/preprocessed/
├── patient_1_scan_1_brain_mask.nii.gz   # 脑掩膜
└── patient_1_scan_1_preprocessed.nii.gz # 预处理后
```

---

## 🔧 常见问题

### Q1: 图像加载失败?
```bash
# 检查文件是否存在
dir data\preprocessed\*.nii.gz

# 检查任务信息
python -c "
from app import create_app, db
from app.models import AnalysisTask
app = create_app()
with app.app_context():
    task = AnalysisTask.query.filter_by(mri_scan_id=1).first()
    print(task.preprocess_info if task else 'No task')
"
```

### Q2: 脑掩膜按钮禁用?
→ 确保 `save_intermediate=True`

### Q3: Papaya.js不加载?
→ 检查网络连接(CDN需要联网)

---

## 💻 代码片段

### Python: 执行预处理
```python
from tasks.analysis_tasks import submit_analysis_task

task_id = submit_analysis_task(
    mri_scan_id=1,
    patient_id=1,
    user_id=1,
    use_preprocessing=True  # ✅ 启用
)
```

### JavaScript: 切换图像
```javascript
showImage('original');      // 原始
showImage('preprocessed');  // 处理后
showImage('mask');          // 掩膜
toggleCompareMode();        // 对比
```

---

## 📊 性能数据

- **文件大小**: 2-5MB/扫描
- **加载时间**: ~1秒
- **内存占用**: ~100MB (浏览器)
- **存储开销**: ~5-10MB/扫描

---

## 🔗 相关链接

- [详细指南](MRI_VISUALIZATION_GUIDE.md)
- [快速启动](VISUALIZATION_QUICKSTART.md)
- [优化总结](OPTIMIZATION_SUMMARY.md)
- [Papaya文档](https://github.com/rordenlab/Papaya/wiki)

---

**版本**: v1.0 | **更新日期**: 2026-04-06
