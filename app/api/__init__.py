# app/api/__init__.py
from flask import Blueprint

api_bp = Blueprint('api', __name__)

# 导入路由以注册端点
from app.api import routes
