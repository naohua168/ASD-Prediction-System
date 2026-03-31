import os
from dotenv import load_dotenv
from pathlib import Path  # ✅ 使用现代化路径处理

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent  # ✅ 统一路径基准


class Config:
    # ✅ 路径更简洁
    UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'

    # ✅ 添加文件扩展名限制
    ALLOWED_EXTENSIONS = {'nii', 'nii.gz', 'img', 'hdr'}

    # ✅ 数据库连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }

    # ✅ 完整的 Celery 配置
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'Asia/Shanghai'

    # ✅ 邮件配置增强
    MAIL_MAX_EMAILS = 100
    MAIL_ASCII_ATTACHMENTS = False


# ✅ 多环境支持
class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True
    # ✅ 生产环境强制检查 SECRET_KEY
    if not os.getenv('SECRET_KEY'):
        raise ValueError("生产环境必须设置 SECRET_KEY")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
