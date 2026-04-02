import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from flask_migrate import Migrate

from app import create_app, db
from config import DevelopmentConfig, config

# 加载环境变量
load_dotenv()

# 根据环境变量选择配置
env = os.getenv('FLASK_ENV', 'development')
config_class = config.get(env, DevelopmentConfig)

# 创建应用实例
app = create_app(config_class)

# 初始化数据库迁移
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    """添加 shell 上下文"""
    from app.models import User, Patient, MRIScan, AnalysisResult, ClinicalScore, SystemLog
    return {
        'db': db,
        'User': User,
        'Patient': Patient,
        'MRIScan': MRIScan,
        'AnalysisResult': AnalysisResult,
        'ClinicalScore': ClinicalScore,
        'SystemLog': SystemLog,
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

            from app.models import User

            if not User.query.filter_by(username=admin_username).first():
                admin = User(
                    username=admin_username,
                    email=admin_email,
                    role='doctor'
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                app.logger.info(f'已创建管理员账户：{admin_username}')

            app.logger.info('应用初始化完成')

        except Exception as e:
            app.logger.error(f'应用初始化失败：{e}', exc_info=True)
            sys.exit(1)


@app.cli.command("sync-export")
def sync_export():
    """导出数据库同步包"""
    from data_sync.sync_tool import main
    main(['export', '--package'])


@app.cli.command("sync-import")
def sync_import():
    """导入数据库同步包"""
    from data_sync.sync_tool import main
    main(['import'])


@app.cli.command("export-db")
def export_db_command():
    """导出数据库数据"""
    from scripts.export_data import export_database
    if export_database():
        print("数据库导出成功！")
    else:
        print("数据库导出失败！")


@app.cli.command("import-db")
def import_db_command():
    """导入数据库数据"""
    from scripts.import_data import import_database
    if import_database():
        print("数据库导入成功！")
    else:
        print("数据库导入失败！")


@app.cli.command("verify-db")
def verify_db_command():
    """验证数据库状态"""
    from scripts.verify_db import verify_database
    if verify_database():
        print("数据库验证成功！")
    else:
        print("数据库验证失败！")


if __name__ == '__main__':
    # 配置日志
    setup_logging(app)

    # 初始化应用
    initialize_app(app)

    # 获取服务器配置
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('SERVER_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '1' if env == 'development' else '0').lower() in ('1', 'true', 'yes')

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
