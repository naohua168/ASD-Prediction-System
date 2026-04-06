# 🚀 MRI预处理流水线 - 5分钟快速开始

## 前置条件

- ✅ Python 3.7+ 已安装
- ✅ 项目依赖已安装 (`pip install -r requirements.txt`)
- ✅ 数据库已初始化
- ✅ 至少有一个MRI扫描记录在数据库中

---

## 步骤1: 启动服务器 (1分钟)

```bash
# 在项目根目录执行
python run.py
```

等待看到以下输出：
```
 * Running on http://127.0.0.1:5000
 * Ready!
```

---

## 步骤2: 运行自动化测试 (2分钟)

### Windows用户：
```bash
scripts\test_preprocessing.bat
```

### Linux/Mac用户：
```bash
python scripts/test_preprocessing_features.py
```

**测试将自动执行**:
1. 登录系统
2. 获取配置预设
3. 提交预处理任务
4. 查询QC报告
5. 访问可视化页面

**预期输出**:
```
📊 测试总结
============================================================
   ✅ 通过 - 获取配置预设
   ✅ 通过 - 提交标准预处理任务
   ✅ 通过 - 提交自定义配置任务
   ✅ 通过 - 获取QC报告
   ✅ 通过 - QC报告页面
   ✅ 通过 - 主路由预处理接口

   总计: 6/6 测试通过

🎉 所有测试通过！预处理流水线功能完整。
```

---

## 步骤3: 查看QC报告页面 (1分钟)

### 方法1: 直接访问

在浏览器中打开：
```
http://localhost:5000/preprocessing/qc-report/1
```

> 将 `1` 替换为你数据库中实际的MRI扫描ID

### 方法2: 通过API触发后访问

```bash
# 1. 提交预处理任务
curl -X POST http://localhost:5000/api/preprocessing/execute \
  -H "Content-Type: application/json" \
  -d '{"mri_scan_id": 1, "config_preset": "standard"}'

# 2. 等待任务完成（约2-5分钟）

# 3. 在浏览器中查看QC报告
# 访问: http://localhost:5000/preprocessing/qc-report/1
```

---

## 📖 页面功能说明

访问QC报告页面后，你将看到：

### 1. 基本信息卡片
- MRI扫描ID
- 文件名
- 处理状态（成功/失败）

### 2. 质量控制总览
- **QC通过徽章**: 绿色表示通过，红色表示警告
- **SNR指标**: 信噪比，建议值 > 5.0
- **脑体积**: 以体素数显示，正常范围 600K-2M

### 3. 预处理步骤
显示完成的5个步骤：
1. ✅ 头动校正与质量控制
2. ✅ 强度标准化
3. ✅ 去颅骨处理
4. ✅ 空间标准化到MNI空间
5. ✅ 空间平滑

### 4. 技术细节（可折叠）
点击展开查看：
- 原始图像尺寸
- MNI标准化后尺寸
- 输出文件路径
- 脑掩膜路径

---

## 🧪 快速测试不同配置

### 测试1: 标准配置
```bash
curl -X POST http://localhost:5000/api/preprocessing/execute \
  -H "Content-Type: application/json" \
  -d '{"mri_scan_id": 1, "config_preset": "standard"}'
```

### 测试2: 高分辨率配置
```bash
curl -X POST http://localhost:5000/api/preprocessing/execute \
  -H "Content-Type: application/json" \
  -d '{"mri_scan_id": 1, "config_preset": "high_res"}'
```

### 测试3: 自定义配置
```bash
curl -X POST http://localhost:5000/api/preprocessing/execute \
  -H "Content-Type: application/json" \
  -d '{
    "mri_scan_id": 1,
    "config_preset": "custom",
    "custom_config": {
      "target_resolution": [1.5, 1.5, 1.5],
      "smoothing_fwhm": 6.0,
      "intensity_normalization": true
    }
  }'
```

### 测试4: 保存中间文件
```bash
curl -X POST http://localhost:5000/api/preprocessing/execute \
  -H "Content-Type: application/json" \
  -d '{
    "mri_scan_id": 1,
    "config_preset": "standard",
    "save_intermediate": true
  }'
```

---

## 🔍 验证功能是否正常

### 检查点1: API响应
提交任务后应收到：
```json
{
  "success": true,
  "task_id": "preprocess_abc123",
  "message": "预处理任务已提交，请在任务列表查看进度"
}
```

### 检查点2: 后台日志
在终端中应看到：
```
🔄 开始预处理任务: preprocess_abc123, MRI=1
✅ 预处理完成: data/preprocessed/patient_1_scan_1_preprocessed.nii.gz
✅ 预处理任务完成: preprocess_abc123
```

### 检查点3: 数据库记录
```sql
SELECT task_id, status, progress, preprocess_info 
FROM analysis_tasks 
WHERE task_id LIKE 'preprocess_%' 
ORDER BY created_at DESC 
LIMIT 5;
```

应看到 `status='completed'` 和完整的 `preprocess_info` JSON数据。

### 检查点4: 生成文件
```bash
# 检查预处理后的文件是否存在
ls -lh data/preprocessed/

# 应看到类似文件：
# patient_1_scan_1_preprocessed.nii.gz
# patient_1_scan_1_brain_mask.nii.gz (如果save_intermediate=true)
```

---

## ❓ 常见问题

### Q1: 测试脚本报错 "登录失败"
**解决**: 修改测试脚本中的用户名和密码
```python
# scripts/test_preprocessing_features.py 第16-17行
USERNAME = 'your_username'
PASSWORD = 'your_password'
```

### Q2: QC报告显示"未找到"
**原因**: 尚未执行预处理或任务未完成  
**解决**: 先提交预处理任务，等待2-5分钟后刷新页面

### Q3: 任务一直处于"pending"状态
**原因**: 达到最大并发数（3个）  
**解决**: 等待其他任务完成，或重启服务器清空任务队列

### Q4: 预处理失败，错误信息模糊
**解决**: 查看详细日志
```bash
# 查看应用日志
cat logs/app.log | grep "预处理"

# 或在Python终端中
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Q5: 找不到MRI扫描ID
**解决**: 查询数据库获取有效的MRI ID
```sql
SELECT id, patient_id, original_filename, file_path 
FROM mri_scans 
LIMIT 10;
```

---

## 📚 下一步学习

完成快速测试后，建议阅读：

1. **[完整使用指南](./PREPROCESSING_PIPELINE_GUIDE.md)** - 详细的API文档和示例
2. **[实施总结](./PREPROCESSING_IMPLEMENTATION_SUMMARY.md)** - 技术实现细节
3. **[前端集成示例](./FRONTEND_INTEGRATION_EXAMPLES.js)** - Vue/React集成代码

---

## 🎯 功能清单验证

完成后请确认以下功能可用：

- [ ] ✅ 可以提交独立预处理任务
- [ ] ✅ 可以选择不同的配置预设
- [ ] ✅ 可以使用自定义配置参数
- [ ] ✅ 可以查看QC报告页面
- [ ] ✅ QC报告显示SNR和脑体积
- [ ] ✅ QC报告显示完成的预处理步骤
- [ ] ✅ 任务状态实时更新
- [ ] ✅ 错误时有明确的提示信息

---

## 💡 提示

1. **首次运行**: 建议使用小文件测试（<100MB），处理速度更快
2. **调试模式**: 设置 `save_intermediate=true` 可查看中间结果
3. **批量测试**: 可以一次性提交多个任务，系统会自动排队
4. **性能监控**: 观察服务器CPU和内存使用情况

---

**准备好了吗？开始测试吧！** 🚀

如有问题，请查看详细文档或联系开发团队。
