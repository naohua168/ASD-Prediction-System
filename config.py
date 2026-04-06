import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    DB_USER = os.environ.get('DB_USER', 'asd_user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'SecurePass123!')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'asd_prediction')

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 3600

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'nii', 'gz', 'nii.gz'}

    MODELS_FOLDER = os.path.join(BASE_DIR, 'models')

    TEMP_FOLDER = os.path.join(BASE_DIR, 'data', 'temp')
    RESULTS_FOLDER = os.path.join(BASE_DIR, 'data', 'results')
    MASKS_FOLDER = os.path.join(BASE_DIR, 'data', 'masks')
    ML_CACHE_DIR = os.path.join(BASE_DIR, 'data', 'cache')
    BACKUP_FOLDER = os.path.join(BASE_DIR, 'data', 'backups')

    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 10

    STORAGE_MONITORING = {
        'temp_max_age_hours': 24,
        'backup_keep_count': 5,
        'disk_warning_threshold': 90
    }



class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://asd_user:SecurePass123!@localhost/test_asd_prediction'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secure-key-change-me'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
