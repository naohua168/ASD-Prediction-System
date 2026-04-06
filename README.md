# ASD预测系统 \- 基于多中心sMRI数据的自闭症谱系障碍识别

基于结构性磁共振成像（sMRI）与机器学习的医学影像辅助诊断系统

## 目录

1. 项目概述

2. 系统架构

3. 核心功能

4. 技术栈

5. 快速部署

6. 多人协作数据库使用解决方案（大赛要求）

7. 项目目录结构

8. 使用说明

9. 数据库管理与维护

10. 团队分工

11. 注意事项与安全规范

12. 版权与声明

---

## 1\. 项目概述

本项目基于结构性磁共振成像（sMRI）数据与机器学习算法，构建自闭症谱系障碍（ASD）智能识别与预测系统。系统支持多中心数据验证、自动化影像预处理、脑区特征提取、模型训练与全维度结果可视化，适用于医学科研与辅助诊断场景。

---

## 2\. 系统架构

- 前端：HTML5、Bootstrap、JavaScript、Three\.js

- 后端：Python、Flask、threading 异步任务

- 数据库：MySQL

- 机器学习：Scikit\-learn、NiBabel、NumPy、Pandas

- 部署：Anaconda、Windows/Linux

---

## 3\. 核心功能

1. MRI影像上传、存储与自动化预处理

2. 脑区灰质体积特征提取

3. 多分类模型训练与评估

4. 3D脑区可视化与结果图表展示

5. 多中心数据交叉验证

6. 后台任务处理与分析任务调度

---

## 4\. 技术栈

|模块|技术|
|---|---|
|模块|技术|
|后端框架|Flask|
|数据库|MySQL|
|异步任务|Python threading|
|机器学习|Scikit-learn, NiBabel|
|可视化|Three.js, Chart.js|
|数据库迁移|Flask-Migrate|
|环境管理|Conda + .env|

---

## 5\. 快速部署

### 5\.1 环境创建

```bash
conda create -n asd_env python=3.6
conda activate asd_env
pip install -r requirements.txt
```

### 5\.2 数据库创建

```sql
CREATE DATABASE asd_prediction CHARACTER SET utf8mb4;
```

### 5\.3 环境变量配置

新建 `\.env` 文件（不提交Git）

```env
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_NAME=asd_prediction
SECRET_KEY=your_secret_key
```

### 5.4 启动服务

```bash
# 初始化数据库
flask db upgrade

# 启动主程序（内置异步任务支持）
python run.py
```

---

## 6\. 多人协作数据库使用解决方案（大赛核心要求）

### 6\.1 数据库版本控制（核心方案）

使用 **Flask\-Migrate** 实现数据库结构统一管理，所有结构变更纳入版本控制。

```python
# 初始化配置（已集成在项目中）
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@localhost/db_name'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
```

**开发流程：**

1. 开发者修改 `models\.py` 数据模型

2. 生成迁移脚本：
              `flask db migrate \-m \&\#34;修改说明\&\#34;`

3. 提交迁移脚本到Git

4. 其他成员拉取代码后执行：
             `flask db upgrade`

### 6\.2 初始数据同步方案

确保所有开发者拥有相同基础数据（脑区、掩码、字典表等）。

**管理员导出：**

```bash
mysqldump -u root -p --no-data asd_prediction > schema.sql
mysqldump -u root -p asd_prediction brain_regions > brain_regions_data.sql
```

**团队成员本地导入：**

```bash
mysql -u root -p asd_prediction < schema.sql
mysql -u root -p asd_prediction < brain_regions_data.sql
```

### 6\.3 本地独立数据库配置

每位成员使用**独立本地库**，不共用生产/开发库。

```python
# config.py
from config import Config

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:pass@localhost/asd_prediction_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭不必要的跟踪，避免警告
```

### 6\.4 测试数据管理

使用独立测试数据库，自动创建测试数据。

```python
# tests/conftest.py
import pytest
from app import create_app, db
from app.models import User, Patient

@pytest.fixture
def test_client():
    app = create_app('testing')
    with app.test_client() as testing_client:
        with app.app_context():
            db.create_all()
            # 插入测试用户、患者数据
            doctor = User(username='test_doctor', email='doctor@test.com')
            doctor.set_password('test123')
            patient = Patient(patient_id='PAT001', name='测试患者', age=10)
            db.session.add(doctor)
            db.session.add(patient)
            db.session.commit()
        yield testing_client
        with app.app_context():
            db.drop_all()
```

### 6\.5 多人协作工作流

#### 6\.5\.1 数据库变更标准流程

```mermaid
graph TD
    A[开发者修改模型] --> B[生成迁移脚本]
    B --> C[提交到Git]
    C --> D[团队成员拉取代码]
    D --> E[执行 flask db upgrade]
    E --> F[本地数据库同步完成]
```

#### 6\.5\.2 日常操作步骤

**本地初始化：**

```bash
git clone https://github.com/yourteam/asd-prediction.git
mysql -u root -p -e "CREATE DATABASE asd_prediction_dev"
flask db upgrade
```

**修改模型时：**

```bash
flask db migrate -m "添加临床评分表"
git add migrations/
git commit -m "db: 添加临床评分表"
git push
```

**接收他人变更：**

```bash
git pull
flask db upgrade
```

---

## 7\. 项目目录结构

```plain text
ASD-Prediction-System/
├── migrations/          # 数据库迁移脚本（必须提交Git）
├── data/
│   └── initial_data/    # 初始基础SQL脚本
├── app/
│   ├── models.py        # 数据模型
│   ├── routes.py        # 接口路由
│   └── __init__.py      # 应用初始化
├── tasks/               # 异步分析任务
├── tests/               # 单元测试
├── .env                 # 本地配置（不提交）
├── config.py            # 全局配置
├── run.py               # 启动入口
└── requirements.txt
```

---

## 8\. 使用说明

1. 登录系统 → 上传患者sMRI数据

2. 选择预处理与模型参数 → 提交分析任务

3. 查看实时任务进度

4. 分析完成后查看：分类指标、脑区热力图、3D可视化、临床相关性图表

5. 支持多中心数据跨站点验证

---

## 9\. 数据库管理与维护

### 9\.1 常用命令

```bash
flask db current      # 查看当前版本
flask db history      # 查看变更历史
flask db downgrade    # 回滚上一版本
```

### 9\.2 数据备份

```bash
mysqldump -u root -p asd_prediction > backup_$(date +%F).sql
```

### 9\.3 冲突解决

1. 迁移冲突：使用 `flask db merge heads` 合并

2. 模型冲突：由数据库管理员统一协调

3. 测试数据添加独立前缀避免冲突

---

## 10\. 团队分工

### 10\.1 数据库管理员

- 维护迁移脚本

- 管理初始数据

- 解决数据库合并冲突

- 定期备份数据库

### 10\.2 后端开发

- 遵循迁移流程修改模型

- 编写单元测试

- 保证接口与数据结构一致

### 10\.3 前端开发

- 使用本地测试数据库开发

- 不直接操作生产库

- 通过接口获取数据

---

## 11\. 注意事项与安全规范

1. **\.env 绝不提交到Git**

2. 数据库凭证使用环境变量加载

3. 成员使用独立本地开发库

4. 真实患者数据必须脱敏

5. 每日自动备份，保留7天以上

6. 严格遵守医疗数据安全与隐私法规

---

## 12\. 版权与声明

- 本项目仅限学术科研使用

- 遵循医疗数据安全管理规范

- 严禁未经授权使用真实隐私数据

- 项目开源协议：MIT

文档版本：v2\.0
最后更新：2026\-04\-04

