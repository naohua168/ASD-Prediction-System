import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'asd-prediction-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://asd_user:SecurePass123!@localhost/asd_prediction'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

    # Celery配置
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

    # 邮件配置（用于错误报告）
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'bai_bai168@qq.com'
    MAIL_PASSWORD = '你的QQ邮箱授权码'  # 需要在QQ邮箱设置中获取
