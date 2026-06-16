"""CSRF 防护工具。

方案：登录后下发一个随机 Token 存 Redis（key=csrf:{user_id}），
前端在所有写请求（POST/PUT/DELETE/PATCH）的 X-CSRF-Token 头里带回，
后端比对 Redis 中的值。

为什么不是 Cookie 双提交？
- 本项目是 SPA + JWT（Header 认证），不依赖 Cookie 做身份识别，
  CSRF 攻击无法利用浏览器自动带 Cookie 的行为。
- 此 CSRF 模块作为纵深防御（defense-in-depth），
  防止攻击者诱导已登录用户从第三方页面发起 JSON 跨站请求。
"""
import secrets
from flask import request, current_app, g
from app.extensions import redis_client


def generate_csrf_token(user_id: int) -> str:
    """为指定用户生成新 CSRF Token，写入 Redis 并返回。"""
    token = secrets.token_hex(32)
    ttl = current_app.config["CSRF_TOKEN_EXPIRE_SECONDS"]
    redis_client.setex(f"csrf:{user_id}", ttl, token)
    return token


def validate_csrf_token(user_id: int, token: str) -> bool:
    """校验 CSRF Token 是否与 Redis 中存储的一致（常量时间比较）。"""
    stored = redis_client.get(f"csrf:{user_id}")
    if not stored or not token:
        return False
    return secrets.compare_digest(stored, token)


def refresh_csrf_ttl(user_id: int):
    """校验通过后刷新 TTL，避免使用中过期。"""
    ttl = current_app.config["CSRF_TOKEN_EXPIRE_SECONDS"]
    redis_client.expire(f"csrf:{user_id}", ttl)


def check_csrf():
    """before_request 钩子：对写请求校验 CSRF Token。

    放行条件（任一满足即跳过）：
    1. 读请求（GET / HEAD / OPTIONS）
    2. 白名单路径（登录/注册/验证码/健康检查/CSRF Token 获取本身）
    3. 用户未登录（由 require_permission 兜底返回 401）
    """
    # 读请求不校验
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None

    # 白名单：无需 CSRF Token 的写请求
    path = request.path
    WHITELIST = (
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/captcha",
        "/api/auth/csrf-token",
        "/api/health",
    )
    if any(path.startswith(p) for p in WHITELIST):
        return None

    # 未登录用户不校验 CSRF（后续权限装饰器会返回 401）
    user_id = getattr(g, "current_user_id", None)
    if not user_id:
        return None

    token = request.headers.get("X-CSRF-Token", "")
    if not token:
        from .response import error
        return error("缺少 CSRF Token，请刷新页面后重试", code=403, http_status=403)

    if not validate_csrf_token(user_id, token):
        from .response import error
        return error("CSRF Token 无效或已过期，请刷新页面后重试", code=403, http_status=403)

    # 校验通过，刷新 TTL
    refresh_csrf_ttl(user_id)
    return None
