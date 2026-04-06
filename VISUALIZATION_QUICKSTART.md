# 🚀 MRI预处理可视化功能 - 快速启动指南

## ✅ 已完成的优化

### 1. 前端可视化组件
- ✅ 集成 **Papaya.js** NIfTI图像查看器
- ✅ 三视图显示(轴状位/冠状位/矢状位)
- ✅ 交互式切片导航滑块
- ✅ 原始/预处理后/脑掩膜切换
- ✅ 对比模式(左右并排显示)
- ✅ 缩放和平移功能

### 2. 后端API支持
- ✅ `/api/files/nifti` - NIfTI文件安全访问接口
- ✅ `/api/mri-scans/<id>` - MRI扫描信息查询
- ✅ 路径验证和权限检查
- ✅ 正确的MIME类型设置

### 3. 数据处理优化
- ✅ `save_intermediate=True` - 保存中间文件
- ✅ 记录完整文件路径到 `preprocess_info`
- ✅ 包含输出文件、脑掩膜路径等元数据

---

## 📝 使用步骤

### 步骤1: 执行带预处理的分析任务

```python
from tasks.analysis_tasks import submit_analysis_task

# 提交任务(关键: use_preprocessing=True)
task_id = submit_analysis_task(
    mri_scan_id=1,      # 你的MRI扫描ID
    patient_id=1,       # 患者ID
    user_id=1,          # 用户ID
    use_preprocessing=True  # ✅ 启用预处理
)

print(f"任务ID: {task_id}")
```

或在Flask路由中:

```python
# app/routes.py 中的 start_analysis 端点
POST /analysis/start
{
    "mri_scan_id": 1,
    "use_preprocessing": true  # ✅ 关键参数
}
```

### 步骤2: 等待任务完成

系统会自动:
1. 执行预处理流水线(头动校正、去颅骨、标准化、平滑)
2. 保存中间文件到 `data/preprocessed/`
3. 记录文件路径到任务的 `preprocess_info` 字段

生成的文件:
```
data/preprocessed/
├── patient_1_scan_1_brain_mask.nii.gz   # 脑掩膜
└── patient_1_scan_1_preprocessed.nii.gz # 预处理后图像
```

### 步骤3: 访问QC报告页面

在浏览器中打开:

```
http://localhost:5000/preprocessing/qc-report/1
```

将 `1` 替换为你的MRI扫描ID。

### 步骤4: 使用可视化功能

在QC报告页面的**"中间结果可视化"**区域:

#### 按钮操作:
1. **🔵 原始图像** - 查看上传的原始NIfTI文件
2. **🟢 预处理后** - 查看处理后的图像
3. **🟣 脑掩膜** - 查看去颅骨结果(半透明红色)
4. **🟠 对比模式** - 左右并排对比

#### 交互操作:
- **拖拽滑块** - 切换不同切片位置
- **鼠标滚轮** - 放大/缩小
- **鼠标拖拽** - 平移视图
- **点击图像** - 自动同步三视图

---

## 🧪 测试功能

运行测试脚本验证安装:

```bash
cd E:\自闭症\ASD-Prediction-System
python tests/test_visualization.py
```

测试内容:
- ✅ Papaya.js CDN连接
- ✅ NIfTI文件API端点
- ✅ 预处理中间文件存在性
- ✅ QC报告模板完整性
- ✅ 任务预处理信息记录

---

## 🔍 故障排查

### 问题1: 页面显示"无法加载图像"

**检查清单:**
```bash
# 1. 确认预处理文件存在
dir data\preprocessed\*.nii.gz

# 2. 检查任务预处理信息
python -c "
from app import create_app, db
from app.models import AnalysisTask
app = create_app()
with app.app_context():
    task = AnalysisTask.query.filter_by(mri_scan_id=1).first()
    if task and task.preprocess_info:
        print('output_file:', task.preprocess_info.get('output_file'))
        print('brain_mask_path:', task.preprocess_info.get('brain_mask_path'))
    else:
        print('未找到预处理信息')
"
```

**解决方案:**
- 确保 `use_preprocessing=True`
- 重新执行分析任务
- 检查文件路径是否正确

### 问题2: 脑掩膜按钮禁用

**原因:** 预处理时未保存中间文件或生成失败

**解决:**
```python
# 确认 save_intermediate=True
preprocess_result = preprocess_mri_file(
    input_file=mri_file_path,
    subject_id="patient_1",
    scan_id="1",
    save_intermediate=True  # ✅ 必须为True
)
```

### 问题3: Papaya.js加载失败

**检查:**
1. 网络连接(需要从CDN加载)
2. 浏览器控制台错误信息

**替代方案:** 如果CDN不可用,可以本地部署:
```bash
# 下载Papaya.js
curl -o app/static/lib/papaya.min.js https://cdn.jsdelivr.net/npm/papaya-viewer@1.2.4/papaya.min.js
curl -o app/static/lib/papaya.min.css https://cdn.jsdelivr.net/npm/papaya-viewer@1.2.4/papaya.min.css
```

然后修改模板引用:
```html
<script src="{{ url_for('static', filename='lib/papaya.min.js') }}"></script>
<link rel="stylesheet" href="{{ url_for('static', filename='lib/papaya.min.css') }}">
```

---

## 📊 性能提示

### 存储空间

每个MRI扫描的中间文件约占用:
- 脑掩膜: ~500KB (压缩后)
- 预处理后图像: ~2-5MB (压缩后)

**建议:** 生产环境定期清理旧文件

```python
# 清理7天前的文件
import os
from datetime import datetime, timedelta

preprocessed_dir = 'data/preprocessed'
cutoff = datetime.now() - timedelta(days=7)

for filename in os.listdir(preprocessed_dir):
    filepath = os.path.join(preprocessed_dir, filename)
    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
    
    if mtime < cutoff:
        os.remove(filepath)
        print(f"已删除: {filename}")
```

### 内存使用

Papaya.js在浏览器中渲染,不会增加服务器负载。

---

## 🎯 下一步增强建议

如需进一步优化,可以考虑:

1. **3D体渲染** - 使用Three.js实现3D脑部重建
2. **ROI标注工具** - 允许用户在图像上标记感兴趣区域
3. **批量对比** - 同时查看多个患者的预处理结果
4. **导出截图** - 保存当前视图为PNG图片
5. **测量工具** - 距离、角度、体积测量

---

## 📚 相关文档

- [详细使用指南](MRI_VISUALIZATION_GUIDE.md)
- [预处理流水线说明](QUICK_START_PREPROCESSING.md)
- [Papaya Viewer文档](https://github.com/rordenlab/Papaya/wiki)

---

## 💬 获取帮助

遇到问题?

1. 查看浏览器控制台(F12)
2. 检查后端日志: `logs/app.log`
3. 运行测试脚本: `python tests/test_visualization.py`
4. 联系系统管理员

---

**祝使用愉快! 🎉**

