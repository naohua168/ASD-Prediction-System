# MRI预处理中间结果可视化使用指南

## 📋 功能概述

本系统现已支持**MRI预处理中间结果的可视化查看**,包括:

- ✅ **脑部切片查看器** - 三视图(轴状位/冠状位/矢状位)交互浏览
- ✅ **原始vs预处理对比** - 并排对比查看预处理效果
- ✅ **脑掩膜叠加显示** - 透明显示去颅骨结果
- ✅ **交互式操作** - 缩放、平移、切片导航

---

## 🚀 快速开始

### 1. 执行带预处理的分析任务

在提交分析任务时,启用预处理选项:

```javascript
// 前端调用示例
fetch('/api/analysis/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        mri_scan_id: 123,
        use_preprocessing: true  // ✅ 关键参数
    })
});
```

或使用Python API:

```python
from tasks.analysis_tasks import submit_analysis_task

task_id = submit_analysis_task(
    mri_scan_id=123,
    patient_id=456,
    user_id=1,
    use_preprocessing=True  # ✅ 启用预处理
)
```

### 2. 访问QC报告页面

任务完成后,访问质量控制报告页面:

```
http://localhost:5000/preprocessing/qc-report/123
```

其中 `123` 是MRI扫描ID。

### 3. 使用可视化功能

在QC报告页面中,你将看到**"中间结果可视化"**区域:

#### 按钮说明:
- **🔵 原始图像** - 显示上传的原始NIfTI文件
- **🟢 预处理后** - 显示经过完整预处理流程的图像
- **🟣 脑掩膜** - 显示去颅骨后的脑部掩膜(如果已保存)
- **🟠 对比模式** - 左右并排显示原始和预处理后图像

#### 交互操作:
- **拖拽滑块** - 切换不同切片位置
- **鼠标滚轮** - 缩放图像
- **鼠标拖拽** - 平移视图
- **方向键** - 微调切片位置

---

## ⚙️ 技术细节

### 中间文件存储路径

当 `save_intermediate=True` 时,系统会在以下位置保存文件:

```
data/preprocessed/
├── patient_123_scan_456_brain_mask.nii.gz   # 脑掩膜
└── patient_123_scan_456_preprocessed.nii.gz # 预处理后图像
```

### 文件访问API

系统提供安全的NIfTI文件访问接口:

```
GET /api/files/nifti?path=/absolute/path/to/file.nii.gz
```

**安全机制:**
- ✅ 路径验证:仅允许访问 `data/` 目录下的文件
- ✅ 登录验证:需要用户认证
- ✅ 权限检查:验证患者数据访问权限

### Papaya.js查看器

我们使用 [Papaya Viewer](https://github.com/rordenlab/Papaya) 作为NIfTI图像渲染引擎:

**特性:**
- 轻量级(~500KB)
- 支持NIfTI(.nii/.nii.gz)格式
- 三视图同步显示
- 无需后端转换

---

## 🔧 故障排查

### 问题1: "无法加载图像"错误

**可能原因:**
1. 未启用 `save_intermediate=True`
2. 文件路径不正确
3. 文件已被删除

**解决方案:**
```bash
# 检查文件是否存在
ls -lh data/preprocessed/patient_*_scan_*_*.nii.gz

# 重新执行预处理任务(确保save_intermediate=True)
```

### 问题2: 脑掩膜按钮禁用

**原因:** 预处理失败或未生成掩膜文件

**检查方法:**
```javascript
// 在浏览器控制台查看
console.log(imagePaths.mask);  // 应该显示文件URL
```

### 问题3: 切片滑块无法拖动

**原因:** 图像尚未完全加载

**解决方案:**
- 等待加载完成(查看加载提示消失)
- 刷新页面重试
- 检查浏览器控制台是否有错误

---

## 📊 性能优化建议

### 1. 存储空间管理

中间文件会占用额外空间,建议定期清理:

```python
# 清理7天前的预处理文件
import os
from datetime import datetime, timedelta

preprocessed_dir = 'data/preprocessed'
cutoff_date = datetime.now() - timedelta(days=7)

for filename in os.listdir(preprocessed_dir):
    filepath = os.path.join(preprocessed_dir, filename)
    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
    
    if file_mtime < cutoff_date:
        os.remove(filepath)
        print(f"已删除: {filename}")
```

### 2. 选择性保存

如果不需要可视化,可以禁用中间文件保存以节省空间:

```python
preprocess_result = preprocess_mri_file(
    input_file=mri_file_path,
    subject_id="patient_1",
    scan_id="1",
    save_intermediate=False  # ❌ 不保存中间文件
)
```

### 3. 压缩存储

NIfTI文件默认使用gzip压缩(.nii.gz),无需额外处理。

---

## 🎨 高级用法

### 自定义颜色映射

修改Papaya查看器的查找表(LUT):

```javascript
// 在 initPapayaViewer 函数中修改
params["lut"] = "Red";      // 红色
params["lut"] = "Green";    // 绿色
params["lut"] = "Blue";     // 蓝色
params["lut"] = "Gray";     // 灰度(默认)
```

### 调整透明度

对于脑掩膜叠加显示:

```javascript
params["min"] = 0.5;  // 最小值阈值
params["max"] = 1.0;  // 最大值阈值
```

### 添加标注

在特定切片位置添加标记:

```javascript
// 在 viewer.onImagesLoaded 回调中添加
viewer.setCurrentCoord(x, y, z);  // 定位到指定坐标
```

---

## 📚 相关文档

- [预处理流水线详细说明](QUICK_START_PREPROCESSING.md)
- [Papaya Viewer官方文档](https://github.com/rordenlab/Papaya/wiki)
- [NIfTI文件格式规范](https://nifti.nimh.nih.gov/)

---

## 💡 最佳实践

1. **生产环境**: 仅在需要调试时启用 `save_intermediate=True`
2. **开发环境**: 始终启用以便观察预处理效果
3. **数据审核**: 使用对比模式验证预处理质量
4. **教学演示**: 利用三视图展示脑部解剖结构

---

## 🆘 获取帮助

如遇问题,请检查:

1. 浏览器控制台错误信息
2. 后端日志 (`logs/app.log`)
3. 预处理任务状态 (`/api/tasks/<task_id>`)

或联系系统管理员。

