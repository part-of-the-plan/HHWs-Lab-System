"""JWT 认证中间件：每个请求自动解析 Token，提取用户身份和权限列表挂到 g 对象。

在 app 工厂中注册为 before_request 钩子。
"""
from flask import g, request, current_app
from flask_jwt_extended import decode_token
from jwt import ExpiredSignatureError, InvalidTokenError


def register_auth_middleware(app):
    """在 Flask app 上注册 JWT 认证中间件"""

    @app.before_request
    def _extract_user():
        # 初始化默认值
        g.current_user_id = None
        g.current_permissions = set()

        # 放行不需要认证的接口
        path = request.path
        if any(path.startswith(p) for p in [
            "/api/auth/captcha",
            "/api/auth/register",
            "/api/auth/login",
            "/api/health",
        ]):
            return  # 不做认证，继续进入路由

        # 从 Header 解析 Token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return  # Token 不存在，交给 require_permission 返回 401

        token = auth_header[7:]
        try:
            payload = decode_token(token)
            user_id = int(payload.get("sub", 0))
        except (ExpiredSignatureError, InvalidTokenError, ValueError, TypeError):
            return  # Token 无效 / 过期，交给 require_permission 返回 401

        if not user_id:
            return

        # 查出权限并挂到 g
        from app.models.user import User
        user = User.query.get(user_id)
        if user and user.status == 1:
            g.current_user_id = user_id
            g.current_permissions = user.get_permissions()
            g.current_user = user
