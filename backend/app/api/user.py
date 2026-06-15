"""用户管理蓝图——超管用：用户列表/编辑/角色分配/启停。

要点：
- 手机号加密存储，列表脱敏返回（mask_phone）
- 角色分配在一个事务内完成（删旧 + 插新）
- 不能禁用/降级自己，防止超管锁死
"""
from flask import Blueprint, request
from app.extensions import db
from app.models import User, Role, UserRole
from app.utils.response import success, error
from app.utils.auth_helper import require_permission, get_current_user_id
from app.utils.validators import sanitize_input
from app.utils.audit import log_action
from app.utils.crypto import encrypt_field, decrypt_field, mask_phone
from sqlalchemy import or_


user_bp = Blueprint("user", __name__)


# ==================== 用户列表（分页 + 筛选）====================

@user_bp.get("")
@require_permission("user:list")
def list_users():
    """用户列表，支持按用户名/真实姓名模糊搜索，手机号脱敏返回。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    keyword = request.args.get("keyword", "").strip()

    query = User.query

    if keyword:
        query = query.filter(
            or_(
                User.username.like(f"%{keyword}%"),
                User.real_name.like(f"%{keyword}%"),
            )
        )

    query = query.order_by(User.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for u in pagination.items:
        phone_raw = decrypt_field(u.phone_enc) if u.phone_enc else ""
        items.append({
            "id": u.id,
            "username": u.username,
            "real_name": u.real_name,
            "email": u.email,
            "phone": mask_phone(phone_raw),
            "status": u.status,
            "role_ids": [r.id for r in u.roles],
            "role_names": [r.role_name for r in u.roles],
            "created_at": str(u.created_at) if u.created_at else None,
            "updated_at": str(u.updated_at) if u.updated_at else None,
        })

    return success({
        "items": items,
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
    })


# ==================== 编辑用户 ====================

@user_bp.put("/<int:uid>")
@require_permission("user:update")
def update_user(uid):
    """编辑用户信息：真实姓名 / 邮箱 / 手机号（提交明文，后端加密存储）。"""
    user = User.query.get(uid)
    if not user:
        return error("用户不存在")

    data = request.get_json(silent=True) or {}

    if "real_name" in data:
        user.real_name = sanitize_input((data["real_name"] or "").strip())
    if "email" in data:
        user.email = sanitize_input((data["email"] or "").strip()) or None
    if "phone" in data:
        phone = sanitize_input((data["phone"] or "").strip())
        user.phone_enc = encrypt_field(phone) if phone else None

    db.session.commit()
    log_action("USER_UPDATE", f"用户ID:{uid}", None)
    return success(message="用户信息已更新")


# ==================== 分配角色 ====================

@user_bp.put("/<int:uid>/roles")
@require_permission("user:assign")
def assign_roles(uid):
    """分配角色：先删旧 user_roles，再插新的（同一事务）。
    传空 role_ids 即清空所有角色。
    防止超管移除自己的角色。
    """
    if uid == get_current_user_id():
        return error("不能修改自己的角色，防止锁死")

    user = User.query.get(uid)
    if not user:
        return error("用户不存在")

    data = request.get_json(silent=True) or {}
    role_ids = data.get("role_ids", [])

    # 校验角色ID是否存在
    if role_ids:
        existing_ids = {r.id for r in Role.query.filter(Role.id.in_(role_ids)).all()}
        invalid = set(role_ids) - existing_ids
        if invalid:
            return error(f"无效的角色ID: {', '.join(map(str, invalid))}")

    try:
        UserRole.query.filter_by(user_id=uid).delete()
        for rid in role_ids:
            db.session.add(UserRole(user_id=uid, role_id=rid))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error("角色分配失败")

    # 记日志
    role_names = []
    if role_ids:
        role_names = [r.role_name for r in Role.query.filter(Role.id.in_(role_ids)).all()]
    log_action("USER_ROLE_ASSIGN", f"用户ID:{uid}",
               f"角色: {', '.join(role_names) if role_names else '无'}")

    return success(message="角色分配成功")


# ==================== 启用 / 禁用 ====================

@user_bp.put("/<int:uid>/status")
@require_permission("user:status")
def toggle_status(uid):
    """启用/禁用用户。不能禁用自己。"""
    if uid == get_current_user_id():
        return error("不能禁用或降级自己的账号")

    user = User.query.get(uid)
    if not user:
        return error("用户不存在")

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    if new_status not in (0, 1):
        return error("status 必须为 0(禁用) 或 1(启用)")

    user.status = new_status
    db.session.commit()

    action = "USER_ENABLE" if new_status == 1 else "USER_DISABLE"
    log_action(action, f"用户ID:{uid}", None)
    return success(message="用户状态已更新")
