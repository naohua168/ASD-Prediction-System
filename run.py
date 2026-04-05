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
    """
    添加 Flask Shell 上下文处理器

    在运行 `flask shell` 命令时，自动将常用的数据库模型和对象注入到交互式环境中，
    方便开发者进行调试和数据操作。

    Returns:
        dict: 包含以下键值对的字典：
            - db (SQLAlchemy): 数据库实例
            - User (Model): 用户模型类
            - Patient (Model): 患者模型类
            - MRIScan (Model): MRI扫描模型类
            - AnalysisResult (Model): 分析结果模型类
            - ClinicalScore (Model): 临床评分模型类
            - SystemLog (Model): 系统日志模型类
            - app (Flask): Flask应用实例
    """
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
    """
    配置应用日志系统

    根据应用的调试模式配置不同的日志输出策略：
    - 调试模式：输出到控制台，级别为 DEBUG
    - 生产模式：输出到轮转文件，级别为 INFO，支持文件大小限制和备份

    Args:
        app (Flask): Flask 应用实例，用于获取配置信息和设置 logger
    """
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
    """
    应用初始化函数

    在应用启动时执行必要的初始化操作，包括：
    1. 创建项目所需的目录结构（上传、临时文件、结果等）
    2. 创建数据库表结构
    3. 创建默认管理员账户（如果不存在）

    Args:
        app (Flask): Flask 应用实例

    Raises:
        SystemExit: 当初始化过程中发生严重错误时，记录错误并退出程序
    """
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
    """
    Flask CLI 命令：导出数据库同步包

    调用数据同步工具导出当前数据库状态，生成可用于团队共享的同步包。
    导出的文件保存在 data_sync/exports 目录下。

    Usage:
        flask sync-export
    """
    from data_sync.sync_tool import main
    main(['export', '--package'])


@app.cli.command("sync-import")
def sync_import():
    """
    Flask CLI 命令：导入数据库同步包

    从 data_sync/exports 目录读取最新的同步包并导入到本地数据库。
    用于团队成员之间同步数据库变更。

    Usage:
        flask sync-import
    """
    from data_sync.sync_tool import main
    main(['import'])


@app.cli.command("export-db")
def export_db_command():
    """
    Flask CLI 命令：导出数据库数据（简化版）

    使用 scripts/export_data 模块导出数据库内容，适用于手动数据备份和迁移。
    导出完成后会在控制台显示成功或失败信息。

    Usage:
        flask export-db
    """
    from scripts.export_data import export_database
    if export_database():
        print("数据库导出成功！")
    else:
        print("数据库导出失败！")


@app.cli.command("import-db")
def import_db_command():
    """
    Flask CLI 命令：导入数据库数据

    使用 scripts/import_data 模块从导出的 JSON 文件导入数据到本地数据库。
    支持增量同步和全量导入，会自动处理外键约束。

    Usage:
        flask import-db
    """
    from scripts.import_data import import_database
    if import_database():
        print("数据库导入成功！")
    else:
        print("数据库导入失败！")


@app.cli.command("verify-db")
def verify_db_command():
    """
    Flask CLI 命令：验证数据库状态

    检查数据库表结构完整性、关键数据存在性以及管理员账户状态。
    用于确认数据库初始化或同步是否成功。

    Usage:
        flask verify-db
    """
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
