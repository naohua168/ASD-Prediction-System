# 日志与监控系统使用指南

## 📋 概述

ASD预测系统已实现完整的日志与监控功能，包括：

1. **系统日志（数据库持久化）**: ✅ 100% 完成
   - 用户操作记录（登录/上传/分析）
   - IP地址追踪
   - 数据库持久化存储

2. **应用日志（文件输出）**: ✅ 100% 完成
   - Python logging配置
   - 文件输出（logs/app.log）
   - 日志轮转（自动管理文件大小和备份）

---

## 🔧 日志配置说明

### 配置文件位置
- **主配置**: `config.py` - 日志路径和轮转参数
- **日志设置**: `run.py` - setup_logging()函数

### 配置参数

```python
# config.py
LOG_FILE = 'logs/app.log'              # 日志文件路径
LOG_MAX_BYTES = 10 * 1024 * 1024       # 单个日志文件最大大小 (10MB)
LOG_BACKUP_COUNT = 10                  # 保留的备份文件数量
```

### 环境差异

#### 开发环境 (DEBUG=True)
- ✅ 控制台输出 (DEBUG级别)
- ✅ 文件输出 (DEBUG级别)
- ✅ 实时查看日志

#### 生产环境 (DEBUG=False)
- ✅ 仅文件输出 (INFO级别)
- ✅ 日志轮转自动管理
- ✅ 抑制第三方库过多日志

---

## 📝 系统日志（数据库）

### 数据表结构

```sql
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER,                    -- 操作用户ID
    action VARCHAR(100) NOT NULL,       -- 操作类型
    description TEXT,                   -- 操作描述
    ip_address VARCHAR(50),             -- IP地址
    created_at DATETIME                 -- 操作时间
);
```

### 记录的操作类型

| 操作类型 | 说明 | 触发场景 |
|---------|------|---------|
| USER_LOGIN | 用户登录 | 用户成功登录系统 |
| USER_REGISTERED | 用户注册 | 新用户注册账户 |
| USER_LOGOUT | 用户登出 | 用户退出系统 |
| PATIENT_CREATED | 创建患者 | 新建患者档案 |
| PATIENT_UPDATED | 更新患者 | 修改患者信息 |
| MRI_UPLOADED | 上传MRI | 上传MRI扫描文件 |
| MRI_BATCH_UPLOADED | 批量上传 | 批量上传多个MRI文件 |
| ANALYSIS_STARTED | 开始分析 | 提交分析任务 |
| ANALYSIS_COMPLETED | 分析完成 | 后台任务完成分析 |
| ANALYSIS_FAILED | 分析失败 | 分析任务出错 |
| TASK_CANCELLED | 取消任务 | 用户手动取消任务 |
| SCORE_ADDED | 添加评分 | 录入临床评分 |

### 查询示例

```python
# Flask Shell中执行
flask shell

# 查询最近10条日志
from app.models import SystemLog
logs = SystemLog.query.order_by(SystemLog.created_at.desc()).limit(10).all()
for log in logs:
    print(f"{log.created_at} | {log.action} | {log.description}")

# 查询特定用户的操作
user_logs = SystemLog.query.filter_by(user_id=1).all()

# 查询特定操作类型
login_logs = SystemLog.query.filter_by(action='USER_LOGIN').all()

# 统计今日登录次数
from datetime import datetime
today = datetime.utcnow().date()
today_logins = SystemLog.query.filter(
    SystemLog.action == 'USER_LOGIN',
    db.func.date(SystemLog.created_at) == today
).count()
```

---

## 📂 应用日志（文件）

### 日志文件位置

```
E:\自闭症\ASD-Prediction-System\logs\
├── app.log              # 当前日志文件
├── app.log.1            # 备份文件1（最新）
├── app.log.2            # 备份文件2
└── ...
```

### 日志格式

```
2026-04-06 15:30:45 INFO app: ASD 预测系统启动（开发模式） [in E:\...\run.py:100]
2026-04-06 15:31:20 DEBUG werkzeug: 127.0.0.1 - - [06/Apr/2026 15:31:20] "GET /dashboard HTTP/1.1" 200 -
2026-04-06 15:32:10 ERROR tasks.analysis_tasks._execute_analysis_task: 分析任务失败: Task ID=xxx [in E:\...\analysis_tasks.py:272]
```

**格式说明**:
- `时间戳`: YYYY-MM-DD HH:MM:SS
- `日志级别`: DEBUG/INFO/WARNING/ERROR
- `模块名`: 产生日志的模块
- `消息内容`: 具体日志信息
- `位置`: 文件名和行号

### 日志轮转机制

当 `app.log` 达到 **10MB** 时：
1. 自动重命名为 `app.log.1`
2. 原有的 `app.log.1` → `app.log.2`
3. 依此类推...
4. 超过 **10个备份** 后，最旧的文件被删除

---

## 🛠️ 日志管理工具

### 1. 日志测试脚本

**用途**: 验证日志配置是否正确

```bash
# Windows
scripts\test_logging.bat

# 或直接运行Python
python scripts\test_logging.py
```

**输出示例**:
```
================================================================================
日志系统测试
================================================================================

✓ 测试1: 日志目录检查
  - 日志文件路径: logs/app.log
  - 日志目录: E:\...\logs
  - 目录存在: True

✓ 测试2: 日志配置参数
  - 最大文件大小: 10.00 MB
  - 备份数量: 10
  - 调试模式: True

✓ 测试3: 写入测试日志
  ✓ 已写入测试日志

✓ 测试4: 验证日志文件
  ✓ 日志文件已创建: logs/app.log
  - 文件大小: 2.35 KB
  - 总行数: 15

  最后5行日志:
    2026-04-06 15:30:45 DEBUG app: 这是DEBUG级别的测试日志
    2026-04-06 15:30:45 INFO app: 这是INFO级别的测试日志
    ...

✓ 日志系统测试完成！
```

### 2. 日志查看工具

**用途**: 便捷查看和管理日志文件

```bash
# 列出所有日志文件
python scripts\view_logs.py list

# 查看最后50行日志
python scripts\view_logs.py tail

# 查看最后100行
python scripts\view_logs.py tail -n 100

# 持续跟踪日志（类似tail -f）
python scripts\view_logs.py tail -f

# 搜索关键词
python scripts\view_logs.py search -k "ERROR"
python scripts\view_logs.py search -k "ANALYSIS_COMPLETED"

# 清理30天前的日志
python scripts\view_logs.py clean --days 30
```

---

## 🔍 日志使用场景

### 场景1: 排查分析失败问题

```python
# 1. 查看应用日志中的错误
python scripts\view_logs.py search -k "分析任务失败"

# 2. 查看数据库中的失败记录
flask shell
>>> from app.models import SystemLog
>>> failed = SystemLog.query.filter_by(action='ANALYSIS_FAILED').all()
>>> for log in failed:
...     print(f"{log.created_at}: {log.description}")
```

### 场景2: 审计用户操作

```python
# 查询某用户的所有操作
flask shell
>>> from app.models import SystemLog, User
>>> user = User.query.filter_by(username='admin').first()
>>> logs = SystemLog.query.filter_by(user_id=user.id).order_by(SystemLog.created_at.desc()).all()
>>> for log in logs[:20]:
...     print(f"{log.created_at} | {log.action:20s} | {log.ip_address:15s} | {log.description}")
```

### 场景3: 监控系统性能

```python
# 查看日志文件大小和增长
python scripts\view_logs.py list

# 如果日志过大，清理旧文件
python scripts\view_logs.py clean --days 7
```

### 场景4: 实时监控系统运行

```bash
# 在一个终端窗口中持续跟踪日志
python scripts\view_logs.py tail -f

# 在另一个终端执行操作，实时观察日志输出
```

---

## ⚙️ 高级配置

### 自定义日志级别

编辑 `run.py` 中的 `setup_logging()` 函数：

```python
# 修改根日志器级别
root_logger.setLevel(logging.DEBUG)  # 或 logging.INFO/WARNING/ERROR

# 修改特定模块的日志级别
logging.getLogger('werkzeug').setLevel(logging.ERROR)  # 只记录错误
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
```

### 添加新的日志处理器

```python
# 例如：添加邮件通知（仅在ERROR级别）
from logging.handlers import SMTPHandler

mail_handler = SMTPHandler(
    mailhost='smtp.example.com',
    fromaddr='noreply@example.com',
    toaddrs=['admin@example.com'],
    subject='ASD系统错误通知',
    credentials=('username', 'password')
)
mail_handler.setLevel(logging.ERROR)
app.logger.addHandler(mail_handler)
```

### 日志格式化定制

```python
# 更详细的格式
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s.%(funcName)s:%(lineno)d\n'
    '  消息: %(message)s\n'
    '  线程: %(threadName)s\n'
    '  进程: %(process)d',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

---

## 🐛 常见问题

### Q1: 日志文件没有生成？

**检查清单**:
1. 确认 `logs` 目录存在且有写入权限
2. 确认 `setup_logging(app)` 在 `run.py` 中被调用
3. 检查是否有异常阻止了日志初始化

**解决方法**:
```bash
# 手动创建目录
mkdir logs

# 运行测试脚本
python scripts\test_logging.py
```

### Q2: 日志轮转不工作？

**可能原因**:
- 日志文件未达到10MB阈值
- 备份数量未超过10个

**验证方法**:
```python
import os
log_file = 'logs/app.log'
print(f"当前大小: {os.path.getsize(log_file) / 1024 / 1024:.2f} MB")
print(f"备份文件数: {len([f for f in os.listdir('logs') if f.startswith('app.log.')])}")
```

### Q3: 如何减少日志输出？

**方法1**: 提高日志级别
```python
# run.py
app.logger.setLevel(logging.WARNING)  # 只记录WARNING及以上
```

**方法2**: 抑制特定模块
```python
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
```

### Q4: 数据库日志太多怎么办？

**定期清理脚本**:
```python
# scripts/cleanup_system_logs.py
from app import create_app, db
from app.models import SystemLog
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # 删除90天前的日志
    cutoff = datetime.utcnow() - timedelta(days=90)
    deleted = SystemLog.query.filter(SystemLog.created_at < cutoff).delete()
    db.session.commit()
    print(f"已删除 {deleted} 条旧日志")
```

---

## 📊 监控指标建议

基于日志数据，可以监控以下指标：

1. **系统活跃度**
   - 每日登录次数
   - 每日上传文件数
   - 每日分析任务数

2. **系统健康度**
   - 分析失败率
   - 平均分析时长
   - 错误频率趋势

3. **用户行为**
   - 活跃用户数
   - 常用功能统计
   - 操作时间分布

**示例查询**:
```python
# 本周分析成功率
from datetime import timedelta
week_ago = datetime.utcnow() - timedelta(days=7)
completed = SystemLog.query.filter(
    SystemLog.action == 'ANALYSIS_COMPLETED',
    SystemLog.created_at >= week_ago
).count()
failed = SystemLog.query.filter(
    SystemLog.action == 'ANALYSIS_FAILED',
    SystemLog.created_at >= week_ago
).count()
total = completed + failed
success_rate = (completed / total * 100) if total > 0 else 0
print(f"本周分析成功率: {success_rate:.2f}% ({completed}/{total})")
```

---

## 🎯 最佳实践

1. **定期检查日志**
   - 每周查看一次错误日志
   - 每月清理旧日志文件

2. **关键操作必须记录**
   - 所有数据修改操作
   - 所有分析任务状态变化
   - 所有系统异常

3. **日志信息安全**
   - 不要在日志中记录密码
   - 敏感数据脱敏处理
   - 定期备份重要日志

4. **性能优化**
   - 避免在循环中记录过多DEBUG日志
   - 生产环境关闭DEBUG级别
   - 合理设置日志轮转参数

---

## 📞 技术支持

如有日志相关问题，请：
1. 首先运行 `python scripts\test_logging.py` 进行自检
2. 查看 `logs/app.log` 中的错误信息
3. 联系系统管理员

---

**最后更新**: 2026-04-06  
**版本**: v1.0
