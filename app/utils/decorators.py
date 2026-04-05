from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def permission_required(permission):
    """
    权限检查装饰器

    Args:
        permission: 所需权限 ('doctor', 'researcher', 'admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            # 研究员可以访问所有功能
            if current_user.role == 'researcher':
                return f(*args, **kwargs)

            # 医生只能访问doctor权限的功能
            if permission == 'doctor' and current_user.role == 'doctor':
                return f(*args, **kwargs)

            # 管理员可以访问所有功能
            if hasattr(current_user, 'is_admin') and current_user.is_admin:
                return f(*args, **kwargs)

            abort(403)
        return decorated_function
    return decorator


def doctor_or_researcher(f):
    """医生或研究员权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role not in ['doctor', 'researcher']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def owner_or_researcher(model_class, id_param='id'):
    """
    资源所有者或研究员权限检查

    Args:
        model_class: 数据库模型类
        id_param: URL参数中的ID字段名
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            # 研究员可以访问所有资源
            if current_user.role == 'researcher':
                return f(*args, **kwargs)

            # 检查是否为资源所有者
            resource_id = kwargs.get(id_param)
            if resource_id:
                resource = model_class.query.get(resource_id)
                if resource and hasattr(resource, 'doctor_id'):
                    if resource.doctor_id == current_user.id:
                        return f(*args, **kwargs)

            flash('您没有权限访问此资源', 'error')
            abort(403)
        return decorated_function
    return decorator
