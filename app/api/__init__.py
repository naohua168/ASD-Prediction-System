from flask import Blueprint

# 创建 API 蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 导入路由以确保注册
from app.api import routes