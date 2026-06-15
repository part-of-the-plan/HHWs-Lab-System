"""角色列表接口——供前端角色分配下拉框使用。"""
from flask import Blueprint
from app.models import Role
from app.utils.response import success
from app.utils.auth_helper import require_permission

roles_bp = Blueprint("roles", __name__)


@roles_bp.get("")
@require_permission("user:assign")
def list_roles():
    """返回所有角色，供分配角色弹窗使用。"""
    roles = Role.query.order_by(Role.id).all()
    return success([r.to_dict() for r in roles])
