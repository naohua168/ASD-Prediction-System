import os
from dotenv import load_dotenv

# 加载环境变量
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # 安全密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 数据库配置（完全从环境变量读取）
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'mysql+pymysql://asd_user:SecurePass123!@localhost/asd_prediction'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # 数据库连接池配置
    SQLALCHEMY_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
    SQLALCHEMY_POOL_RECYCLE = int(os.environ.get('DB_POOL_RECYCLE', 3600))

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(basedir, 'data/uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 500)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {'nii', 'nii.gz', 'img', 'hdr'}

    # Celery 配置
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'

    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.qq.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_MAX_EMAILS = int(os.environ.get('MAIL_MAX_EMAILS', 100))

    # 日志配置
    LOG_DIR = os.path.join(basedir, 'logs')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 10))

    # 机器学习配置
    DEFAULT_MODEL = os.environ.get('DEFAULT_MODEL', 'MinMaxScaler+SVM')
    ML_N_JOBS = int(os.environ.get('ML_N_JOBS', -1))
    ML_RANDOM_STATE = int(os.environ.get('ML_RANDOM_STATE', 42))
    ML_CV_FOLDS = int(os.environ.get('ML_CV_FOLDS', 5))

    # 临时目录配置
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER', 'data/temp')
    RESULTS_FOLDER = os.environ.get('RESULTS_FOLDER', 'data/results')
    MASKS_FOLDER = os.environ.get('MASKS_FOLDER', 'data/masks')
    ML_CACHE_DIR = os.environ.get('ML_CACHE_DIR', 'data/cache')

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        os.makedirs(Config.TEMP_FOLDER, exist_ok=True)
        os.makedirs(Config.RESULTS_FOLDER, exist_ok=True)
        os.makedirs(Config.MASKS_FOLDER, exist_ok=True)
        os.makedirs(Config.ML_CACHE_DIR, exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

    # 生产环境必须设置的环境变量
    @classmethod
    def init_app(cls, app):
        super().init_app(app)

        # 生产环境检查必要的环境变量
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("生产环境必须设置 SECRET_KEY")

        if not os.environ.get('DATABASE_URL'):
            raise ValueError("生产环境必须设置 DATABASE_URL")


# 配置映射
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
