"""认证蓝图：注册 / 登录 / 验证码 / 修改密码"""
import uuid
import json
from datetime import datetime, timedelta
from io import BytesIO
import base64

from flask import Blueprint, request, current_app, g
from flask_jwt_extended import create_access_token, get_jwt_identity

from app.extensions import db, redis_client
from app.models import User, Role, UserRole
from app.utils.crypto import hash_password, verify_password, encrypt_field
from app.utils.response import success, error
from app.utils.validators import (
    check_username, check_phone, check_email, check_required,
    check_password_complexity, sanitize_input,
)

auth_bp = Blueprint("auth", __name__)


# ==================== 验证码 ====================

@auth_bp.get("/captcha")
def get_captcha():
    """生成图片验证码，存 Redis（可配置过期秒数），返回 Base64 图片 + UUID"""
    from captcha.image import ImageCaptcha
    import random
    import string

    chars = string.ascii_uppercase + string.digits
    code = "".join(random.SystemRandom().choice(chars) for _ in range(4))

    image = ImageCaptcha(width=160, height=60)
    img_bytes = BytesIO()
    image.write(code, img_bytes)
    img_b64 = "data:image/png;base64," + base64.b64encode(img_bytes.getvalue()).decode()

    captcha_id = uuid.uuid4().hex
    ttl = current_app.config["CAPTCHA_EXPIRE_SECONDS"]
    redis_client.setex(f"captcha:{captcha_id}", ttl, code)

    return success({
        "captcha_id": captcha_id,
        "captcha_img": img_b64,
    })


# ==================== 注册 ====================

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    # 1. 必填字段
    for field, name in [("username", "用户名"), ("password", "密码"),
                         ("real_name", "真实姓名")]:
        ok, msg = check_required(data.get(field), name)
        if not ok:
            return error(msg)

    username = sanitize_input(data["username"].strip())
    password = data["password"]
    real_name = sanitize_input(data.get("real_name", "").strip())
    phone = sanitize_input(data.get("phone", "").strip())
    email = sanitize_input(data.get("email", "").strip())

    # 2. 输入格式校验
    ok, msg = check_username(username)
    if not ok: return error(msg)

    ok, msg = check_password_complexity(password)
    if not ok: return error(msg)

    ok, msg = check_phone(phone)
    if not ok: return error(msg)

    ok, msg = check_email(email)
    if not ok: return error(msg)

    # 3. 唯一性检查
    if User.query.filter_by(username=username).first():
        return error("用户名已被使用")
    if phone:
        # 比较加密后的值,先查所有(粒度粗,课设量级够;生产上可考虑加哈希索引列)
        existing = User.query.all()
        from app.utils.crypto import decrypt_field
        for u in existing:
            if decrypt_field(u.phone_enc) == phone:
                return error("该手机号已被注册")
    if email and User.query.filter_by(email=email).first():
        return error("该邮箱已被使用")

    # 4. 密码 SM3 加盐哈希
    pwd_hash = hash_password(password)

    # 5. 手机号 SM4 加密
    phone_enc = encrypt_field(phone) if phone else ""

    # 6. 写入数据库（用户 + 默认普通用户角色，一个事务）
    try:
        user = User(
            username=username,
            password_hash=pwd_hash,
            real_name=real_name,
            phone_enc=phone_enc,
            email=email or None,
            status=1,
        )
        db.session.add(user)
        db.session.flush()  # 拿到 user.id

        # 分配默认角色
        normal_role = Role.query.filter_by(role_code="NORMAL_USER").first()
        if normal_role:
            ur = UserRole(user_id=user.id, role_id=normal_role.id)
            db.session.add(ur)

        db.session.commit()
    except Exception:
        db.session.rollback()
        return error("注册失败，请稍后重试")

    return success({"user_id": user.id, "username": user.username},
                   "注册成功")


# ==================== 登录 ====================

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    captcha_code = (data.get("captcha_code") or "").strip()
    captcha_id = (data.get("captcha_id") or "").strip()

    if not username or not password:
        return error("用户名和密码不能为空")

    # 1. 验证码校验
    if not captcha_id or not captcha_code:
        return error("请输入验证码")
    stored_code = redis_client.get(f"captcha:{captcha_id}")
    if stored_code is None:
        return error("验证码已过期，请刷新")
    if stored_code.upper() != captcha_code.upper():
        return error("验证码错误")
    redis_client.delete(f"captcha:{captcha_id}")  # 用后即删，防重放

    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")[:255]

    # 2. 查用户
    user = User.query.filter_by(username=username).first()
    if not user:
        _log(operator_id=None, username=username, action="LOGIN_FAIL",
             target=f"用户名:{username}", detail="用户不存在", ip=ip, ua=ua)
        return error("用户名或密码错误")  # 不暴露具体原因

    # 3. 账号锁定检查
    if user.is_locked():
        remain = int((user.lock_until - datetime.utcnow()).total_seconds() / 60) + 1
        return error(f"账号已锁定，请约{remain}分钟后再试")

    # 4. 密码验证
    if not verify_password(password, user.password_hash):
        user.fail_count += 1
        if user.fail_count >= current_app.config["LOGIN_FAIL_LIMIT"]:
            user.lock_until = datetime.utcnow() + timedelta(
                minutes=current_app.config["LOGIN_LOCK_MINUTES"])
            user.fail_count = 0
            _log(operator_id=user.id, username=username, action="LOGIN_LOCKED",
                 target=f"用户ID:{user.id}", detail="连续失败锁定", ip=ip, ua=ua)
        db.session.commit()
        _log(operator_id=user.id, username=username, action="LOGIN_FAIL",
             target=f"用户ID:{user.id}", detail=f"密码错误(第{user.fail_count}次)", ip=ip, ua=ua)
        return error("用户名或密码错误")

    # 5. 账号禁用检查
    if user.status == 0:
        return error("账号已被禁用，请联系管理员")

    # 6. 登录成功
    user.fail_count = 0
    user.lock_until = None
    db.session.commit()

    # 签发 JWT
    expires = timedelta(hours=current_app.config["JWT_EXPIRE_HOURS"])
    access_token = create_access_token(identity=str(user.id), expires_delta=expires)

    # 权限列表
    permissions = list(user.get_permissions())
    # 在线用户(Redis Set). 用 uid:token 映射（简化版, token 到期自动失效）
    redis_client.sadd("online_users", str(user.id))

    _log(operator_id=user.id, username=username, action="LOGIN_SUCCESS",
         target=f"用户ID:{user.id}", detail="登录成功", ip=ip, ua=ua)

    return success({
        "access_token": access_token,
        "user": user.to_dict(include_phone=True),
        "permissions": permissions,
    })


# ==================== 修改密码 ====================

@auth_bp.put("/password")
def change_password():
    """需登录，校验旧密码，更新为新密码"""
    user_id = _current_user_id()
    if not user_id:
        return error("请先登录", code=401, http_status=401)

    data = request.get_json(silent=True) or {}
    old_pw = data.get("old_password") or ""
    new_pw = data.get("new_password") or ""

    if not old_pw or not new_pw:
        return error("旧密码和新密码不能为空")

    ok, msg = check_password_complexity(new_pw)
    if not ok:
        return error(msg)

    user = User.query.get(user_id)
    if not user:
        return error("用户不存在")

    if not verify_password(old_pw, user.password_hash):
        return error("旧密码错误")

    user.password_hash = hash_password(new_pw)
    db.session.commit()

    ip = request.remote_addr
    _log(operator_id=user.id, username=user.username, action="PASSWORD_CHANGE",
         target=f"用户ID:{user.id}", detail="修改密码", ip=ip,
         ua=request.headers.get("User-Agent", "")[:255])

    return success(message="密码修改成功，请重新登录")


# ==================== 辅助 ====================

def _current_user_id():
    """从 Flask g 对象获取当前用户 ID（由中间件设置）"""
    from flask import g
    return getattr(g, "current_user_id", None)


def _log(operator_id, username, action, target, detail, ip, ua):
    """快速写审计日志，不回滚业务"""
    try:
        from app.models.log import OperationLog
        log = OperationLog(
            operator_id=operator_id,
            username=username,
            action=action,
            target=target,
            detail=detail,
            ip=ip,
            user_agent=ua,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()  # 日志失败不影响业务
