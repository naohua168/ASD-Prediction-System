from flask import Blueprint, render_template, jsonify
from app import db

errors_bp = Blueprint('errors', __name__)


@errors_bp.app_errorhandler(400)
def bad_request(error):
    """400错误处理"""
    if request_wants_json():
        return jsonify({'error': '请求参数错误', 'code': 400}), 400
    return render_template('errors/400.html'), 400


@errors_bp.app_errorhandler(401)
def unauthorized(error):
    """401错误处理"""
    if request_wants_json():
        return jsonify({'error': '未授权访问', 'code': 401}), 401
    return render_template('errors/401.html'), 401


@errors_bp.app_errorhandler(403)
def forbidden(error):
    """403错误处理"""
    if request_wants_json():
        return jsonify({'error': '禁止访问', 'code': 403}), 403
    return render_template('errors/403.html'), 403


@errors_bp.app_errorhandler(404)
def not_found(error):
    """404错误处理"""
    if request_wants_json():
        return jsonify({'error': '资源不存在', 'code': 404}), 404
    return render_template('errors/404.html'), 404


@errors_bp.app_errorhandler(500)
def internal_error(error):
    """500错误处理"""
    db.session.rollback()
    if request_wants_json():
        return jsonify({'error': '服务器内部错误', 'code': 500}), 500
    return render_template('errors/500.html'), 500


def request_wants_json():
    """检查客户端是否期望JSON响应"""
    from flask import request
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
           request.accept_mimetypes['application/json'] > \
           request.accept_mimetypes['text/html']
