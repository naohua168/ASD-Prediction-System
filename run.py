from app import create_app, db
from dotenv import load_dotenv
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import ProductionConfig, DevelopmentConfig

# 加载环境变量
load_dotenv()

# 根据环境变量选择配置
env = os.getenv('FLASK_ENV', 'development')
if env == 'production':
    config_object = ProductionConfig
else:
    config_object = DevelopmentConfig

# 创建应用实例
app = create_app(config_object)

# ✅ 延迟导入 models（在应用创建后）
with app.app_context():
    from app.models import User, Patient, Analysis


@app.shell_context_processor
def make_shell_context():
    """添加 shell 上下文"""
    return {
        'db': db,
        'User': User,
        'Patient': Patient,
        'Analysis': Analysis,
        'app': app
    }


def setup_logging(app):
    """配置日志系统"""
    if app.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        return

    # 创建日志目录
    log_dir = Path(app.config.get('LOG_FILE', 'logs/app.log')).parent
    log_dir.mkdir(exist_ok=True)

    # 配置日志轮转
    handler = RotatingFileHandler(
        app.config.get('LOG_FILE', 'logs/app.log'),
        maxBytes=app.config.get('LOG_MAX_BYTES', 10485760),
        backupCount=app.config.get('LOG_BACKUP_COUNT', 10)
    )
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('ASD 预测系统启动')


def initialize_app(app):
    """应用初始化函数"""
    with app.app_context():
        try:
            # 创建必要的目录
            directories = [
                app.config['UPLOAD_FOLDER'],
                app.config.get('TEMP_FOLDER', 'data/temp'),
                app.config.get('RESULTS_FOLDER', 'data/results'),
                app.config.get('MASKS_FOLDER', 'data/masks'),
                app.config.get('ML_CACHE_DIR', 'data/cache'),
                Path(app.config.get('LOG_FILE', 'logs/app.log')).parent
            ]

            for directory in directories:
                os.makedirs(directory, exist_ok=True)

            # 创建数据库表
            db.create_all()

            # 创建默认管理员账户
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            admin_email = os.getenv('ADMIN_EMAIL', 'admin@asd-system.com')

            if not User.query.filter_by(username=admin_username).first():
                admin = User(
                    username=admin_username,
                    email=admin_email,
                    role='admin'
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                app.logger.info(f'已创建管理员账户：{admin_username}')

            app.logger.info('应用初始化完成')

        except Exception as e:
            app.logger.error(f'应用初始化失败：{e}', exc_info=True)
            sys.exit(1)


if __name__ == '__main__':
    # 配置日志
    setup_logging(app)

    # 初始化应用
    initialize_app(app)

    # 获取服务器配置
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('SERVER_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    app.logger.info(f'服务器启动：http://{host}:{port}')

    try:
        # 启动应用
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        app.logger.info('服务器已停止')
    except Exception as e:
        app.logger.error(f'服务器运行错误：{e}', exc_info=True)
        sys.exit(1)
