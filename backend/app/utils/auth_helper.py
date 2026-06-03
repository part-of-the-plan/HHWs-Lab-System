"""权限校验装饰器 + 当前用户快捷获取。"""

from functools import wraps
from flask import g, current_app, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.utils.response import error


def require_permission(perm_code: str):
    """接口权限装饰器。基于权限标识鉴权，不基于角色名。

    用法: @require_permission('device:create')

    流程：
    1. 检查是否有有效 JWT Token → 无则 401
    2. 从 g.current_permissions 检查是否包含 perm_code → 无则 403
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # 1. 验证 JWT Token
            try:
                verify_jwt_in_request()
            except Exception:
                return error("请先登录", code=401, http_status=401)

            # 2. 检查权限
            perms = getattr(g, "current_permissions", set())
            if perm_code not in perms:
                return error("无此操作权限", code=403, http_status=403)

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    """获取当前登录的 User 对象，未登录返回 None"""
    from app.models.user import User
    uid = getattr(g, "current_user_id", None)
    if uid is None:
        return None
    return User.query.get(uid)


def get_current_user_id():
    return getattr(g, "current_user_id", None)
