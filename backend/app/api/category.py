"""设备分类管理蓝图——简单 CRUD。删除前检查分类下是否还有设备。"""
from flask import Blueprint, request
from app.extensions import db
from app.models import DeviceCategory, Device
from app.utils.response import success, error
from app.utils.auth_helper import require_permission
from app.utils.validators import sanitize_input, check_required
from app.utils.audit import log_action

category_bp = Blueprint("category", __name__)


@category_bp.get("")
@require_permission("device:list")
def list_categories():
    cats = DeviceCategory.query.order_by(DeviceCategory.id).all()
    return success([c.to_dict() for c in cats])


@category_bp.post("")
@require_permission("category:manage")
def create_category():
    data = request.get_json(silent=True) or {}
    name = sanitize_input((data.get("name") or "").strip())
    ok, msg = check_required(name, "分类名称")
    if not ok:
        return error(msg)
    if DeviceCategory.query.filter_by(name=name).first():
        return error("该分类已存在")

    cat = DeviceCategory(name=name,
                         description=sanitize_input((data.get("description") or "").strip()))
    db.session.add(cat)
    db.session.commit()
    log_action("CATEGORY_CREATE", f"分类ID:{cat.id}", name)
    return success({"id": cat.id}, "分类添加成功")


@category_bp.put("/<int:cid>")
@require_permission("category:manage")
def update_category(cid):
    cat = DeviceCategory.query.get(cid)
    if not cat:
        return error("分类不存在")
    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = sanitize_input(data["name"].strip())
        if not name:
            return error("分类名称不能为空")
        exists = DeviceCategory.query.filter(
            DeviceCategory.name == name, DeviceCategory.id != cid).first()
        if exists:
            return error("该分类名已被使用")
        cat.name = name
    if "description" in data:
        cat.description = sanitize_input((data["description"] or "").strip())
    db.session.commit()
    log_action("CATEGORY_UPDATE", f"分类ID:{cid}", None)
    return success(message="分类更新成功")


@category_bp.delete("/<int:cid>")
@require_permission("category:manage")
def delete_category(cid):
    cat = DeviceCategory.query.get(cid)
    if not cat:
        return error("分类不存在")
    # 检查分类下是否还有未删除设备
    has_device = Device.query.filter_by(category_id=cid, is_deleted=0).first()
    if has_device:
        return error("该分类下还有设备，请先迁移或删除设备")
    db.session.delete(cat)
    db.session.commit()
    log_action("CATEGORY_DELETE", f"分类ID:{cid}", cat.name)
    return success(message="分类已删除")
