import os


class Config:
    # 从环境变量读取，或使用默认值
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # 数据库配置 - 使用 asd_user
    DB_USER = os.environ.get('DB_USER', 'asd_user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'SecurePass123!')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'asd_prediction')

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/uploads')
    MAX_CONTENT_LENGTH = 5000 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'nii', 'gz'}


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True  # 打印 SQL 语句，便于调试


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://asd_user:SecurePass123!@localhost/test_asd_prediction'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    # 生产环境使用更强的密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secure-key-change-me'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
