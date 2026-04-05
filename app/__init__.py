from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

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

    # 配置登录
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面'

    # 注册蓝图
    try:
        from app.routes import main_bp
        app.register_blueprint(main_bp)
    except ImportError:
        pass

    return app
