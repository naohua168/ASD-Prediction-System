# ASD预测系统 - 基于多中心sMRI数据的自闭症谱系障碍识别

# 一、项目概述

本项目搭建**基于结构性磁共振成像（sMRI）数据+机器学习算法**的自闭症谱系障碍（ASD）智能预测系统。采用三级评估框架，依托脑区灰质体积变异特征挖掘ASD核心生物标志物，同步完成临床关联性分析与多中心数据验证，适配医学科研场景下的影像辅助诊断研究。

# 二、系统架构

```mermaid

graph TD
    A[前端界面] --> B[Flask后端]
    B --> C[Celery异步任务队列]
    C --> D[机器学习核心模块]
    D --> E[MySQL业务数据库]
    E --> F[医学影像专用存储]
    F --> D
    
```
# 三、核心功能

## 3.1 MRI数据上传与预处理

- 支持NIfTI标准医学影像格式文件上传

- 自动化落地VBM8全套预处理流程

- 精准提取脑部灰质体积核心特征

## 3.2 三级科研评估框架

1. 模型层级：集成Searchlight技术，生成3D脑区准确率热力图

2. 特征层级：通过虚拟损伤分析，筛选高稳健性ASD生物标志物

3. 生物学层级：关联灰质体积指标与临床病症，完成相关性分析

## 3.3 多中心数据验证

- 兼容ABIDE II公开多中心影像数据集验证

- 支持跨站点模型性能对比、泛化能力分析

## 3.4 全维度结果可视化

- 3D立体渲染脑区差异区域

- 输出ROC曲线、分类性能量化图表

- 生成临床症状关联性分析图谱

# 四、技术栈分类

|模块| 核心技术/框架                           |
|---|-----------------------------------|
|前端开发| HTML5、CSS3、JavaScript、Bootstrap 5 |
|后端服务| Python 3.6、Flask、Celery、Redis     |
|数据存储| MySQL 5.7、本地影像文件存储                |
|机器学习| Scikit-learn、NiBabel、NumPy、Pandas |
|可视化引擎| Three.js、Chart.js、Papaya.js       |
|部署环境| Windows 11、Anaconda               |
# 五、快速部署指南

## 5.1 环境初始化（Conda）

```bash
# 创建专属虚拟环境
conda create -n asd_env python=3.6 -y
conda activate asd_env

# 拉取项目源码
git clone https://github.com/naohua168/ASD-Prediction-System.git
cd ASD-Prediction-System

# 安装项目依赖库
pip install -r requirements.txt
```

## 5.2 数据库配置（MySQL）

```sql
# 新建业务数据库
CREATE DATABASE asd_prediction;
# 创建专属账号并授权
CREATE USER 'asd_user'@'localhost' IDENTIFIED BY 'SecurePass123!';
GRANT ALL PRIVILEGES ON asd_prediction.* TO 'asd_user'@'localhost';
FLUSH PRIVILEGES;
```

## 5.3 全局配置文件

项目根目录新建 `.env` 配置文件，写入核心参数：

```env
SECRET_KEY=your-secret-key
SQLALCHEMY_DATABASE_URI=mysql+pymysql://asd_user:SecurePass123!@localhost/asd_prediction
CELERY_BROKER_URL=redis://localhost:6379/0
UPLOAD_FOLDER=./data/uploads
```

## 5.4 全服务启动流程

```bash
# 1. 启动Redis缓存服务
redis-server

# 2. 执行数据库迁移初始化
flask db upgrade

# 3. 启动Flask主应用
python run.py

# 4. 新开终端，启动Celery异步任务 Worker
celery -A tasks.analysis_tasks.celery worker --loglevel=info -P eventlet
```

项目访问地址：http://localhost:5000

# 六、完整项目目录结构

```plain text
ASD-Prediction-System/
├── app/                      # Flask核心应用目录
│   ├── __init__.py           # 应用初始化配置
│   ├── routes.py             # 前后端接口路由
│   ├── models.py             # 数据库实体模型
│   ├── forms.py              # 表单校验规则
│   ├── utils/                # 通用工具包
│   │   ├── ml_core.py        # 机器学习调用工具
│   │   ├── auth.py           # 用户权限认证工具
│   │   └── storage.py        # 影像文件存储工具
│   ├── templates/            # 前端HTML模板
│   └── static/               # 静态资源（JS/CSS/图片）
├── ml_core/                  # 机器学习算法核心
│   ├── ClassifyFunc/         # 分类算法封装
│   ├── Utility/              # 算法辅助工具
│   └── classifier.py         # ASD专属分类器
├── tasks/                    # Celery异步分析任务
│   └── analysis_tasks.py     # 影像分析后台任务
├── tests/                    # 单元测试&功能测试用例
├── data/                     # 项目数据存储目录
│   ├── uploads/              # 用户上传原始MRI文件
│   ├── masks/                # 脑区标准掩码文件
│   └── results/              # 分析生成结果文件
├── config.py                 # 基础全局配置
├── requirements.txt          # Python依赖清单
├── run.py                    # 项目启动入口脚本
├── deploy.py                 # 离线部署辅助脚本
└── README.md                 # 项目说明文档
```

# 七、详细使用指南

## 7.1 用户权限认证

- 支持科研人员专属账号注册、登录

- 未授权账号无法访问影像分析、多中心验证核心功能

## 7.2 MRI影像数据上传

1. 登录系统进入【上传MRI】功能页面

2. 绑定患者唯一ID标识

3. 上传标准NIfTI格式脑部MRI文件

4. 选择分析模型（默认标配：MinMaxScaler+SVM组合）

## 7.3 查看智能分析结果

1. 文件提交后系统自动触发后台异步分析

2. 在【任务状态】页面实时查看分析进度

3. 分析完成可查看全维度结果：
       

    - 模型分类指标：准确率、AUC、精确率、召回率

    - 关键异常脑区热力分布图

    - 临床病症关联性分析图表

    - 3D立体脑区差异可视化模型

## 7.4 多中心数据交叉验证

1. 进入【多中心分析】专属页面

2. 自定义选择训练数据源站点（如GU）

3. 匹配测试数据源站点（如UCLA）

4. 一键生成跨站点模型泛化能力验证报告

# 八、开源贡献规范

1. Fork 项目官方源码仓库

2. 新建功能分支：`git checkout -b feature/自定义功能名称`

3. 提交代码备注清晰：`git commit -m "新增/优化：xxx功能描述"`

4. 推送分支至远程仓库：`git push origin feature/自定义功能名称`

5. 提交 Pull Request，等待项目维护方审核合并

# 九、版权与联系方式

1. 开源协议：本项目开源遵循配套 LICENSE 文件规范

2. 项目维护：naohua168

3. 沟通邮箱：bai_bai168@qq.com

4. 源码地址：https://github.com/naohua168

# 十、致谢与合规声明

1. 项目依托科研成果：
基于多中心结构性磁共振成像和机器学习识别自闭症谱系障碍的专项研究（作者&期刊&DOI待补充完善）

2. 合规提醒：
系统严禁违规使用真实患者隐私数据，落地使用需严格遵守HIPAA、GDPR及国内医疗数据安全法规，仅限定用于学术科研场景。
