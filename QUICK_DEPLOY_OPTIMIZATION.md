# 数据库优化 - 快速执行指南

## 🎯 一键执行流程

### 步骤 1: 备份数据库（重要！）
```bash
# Windows PowerShell
mysqldump -u root -p asd_prediction > backup_before_optimization_$(Get-Date -Format "yyyyMMdd_HHmmss").sql
```

### 步骤 2: 应用数据库迁移
```bash
flask db upgrade
```

### 步骤 3: 验证优化效果
```bash
python scripts/verify_optimizations.py
```

### 步骤 4: 重启应用
```bash
python run.py
```

---

## ✅ 验证检查清单

部署后请确认以下功能正常：

- [ ] 患者列表页面显示正常
- [ ] 可以新建患者
- [ ] 可以编辑患者
- [ ] 删除患者后，患者从列表消失但数据仍保留在数据库中
- [ ] 仪表盘统计数据准确（不包含已删除患者）
- [ ] 患者搜索功能正常

---

## 🔍 快速问题排查

### 如果迁移失败
```bash
# 查看当前迁移状态
flask db current

# 如果表已存在但版本不同步，手动标记版本
flask db stamp 8f2a1b3c4d5e
```

### 如果验证脚本报错
```bash
# 检查数据库连接
python -c "from app import create_app; app = create_app(); print('DB OK')"

# 手动检查索引
mysql -u root -p asd_prediction -e "SHOW INDEX FROM patients;"
```

---

## 📊 预期效果

| 优化项 | 预期提升 | 验证方法 |
|--------|---------|----------|
| 患者查询性能 | 30-50% | 观察患者列表加载速度 |
| 统计分析性能 | 40-60% | 观察仪表盘加载速度 |
| 数据安全性 | 显著提升 | 测试删除和恢复功能 |

---

## 🆘 紧急回滚

如遇严重问题：

```bash
# 1. 回滚数据库
flask db downgrade add_indexes

# 2. 恢复代码
git log --oneline  # 找到本次提交的hash
git revert <commit_hash>

# 3. 重启应用
python run.py
```

---

**详细文档**: 查看 `DATABASE_OPTIMIZATION_REPORT.md` 获取完整说明
