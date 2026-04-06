from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.websocket_handler import socketio, init_socketio

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_class=None):
    """创建并配置 Flask 应用"""
    app = Flask(__name__)

    # 加载配置
    if config_class is None:
        from config import DevelopmentConfig
        config_class = DevelopmentConfig

    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    init_socketio(app)

    # 配置登录
    login_manager.login_view = 'main.login'
    login_manager.login_message = '请先登录以访问此页面'

    # 注册蓝图
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # 注册API蓝图（从 api 包导入）
    from app.api import api_bp
    app.register_blueprint(api_bp)

    # 注册错误处理蓝图
    from app.errors.handlers import errors_bp
    app.register_blueprint(errors_bp)

    return app
