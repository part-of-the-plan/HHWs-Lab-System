"""设备管理蓝图——CRUD + 分类管理。

要点：
- 列表查询支持分页 + 多条件筛选（ORM 链式拼接，无注入风险）
- 删除用软删除（is_deleted=1），且有未完结借用记录时禁止删除
- 设备编号自动生成（分类编码 + 序号）
- 字段粒度按权限：有 device:create/update 看完整字段，否则基础字段
"""
from datetime import datetime

from flask import Blueprint, request, g
from app.extensions import db
from app.models import Device, DeviceCategory, BorrowRecord
from app.utils.response import success, error
from app.utils.auth_helper import require_permission
from app.utils.validators import sanitize_input, check_required
from app.utils.audit import log_action

device_bp = Blueprint("device", __name__)

# 未完结状态：有这些记录的设备不可删
UNFINISHED = ["PENDING", "APPROVED", "BORROWED", "RETURN_PENDING", "OVERDUE"]


# ==================== 设备列表（分页+筛选）====================

@device_bp.get("")
@require_permission("device:list")
def list_devices():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    keyword = request.args.get("keyword", "").strip()
    category_id = request.args.get("category_id", type=int)
    status = request.args.get("status", "").strip()
    location = request.args.get("location", "").strip()

    query = Device.query.filter(Device.is_deleted == 0)

    # 动态拼接筛选条件（SQLAlchemy 链式，参数化，无注入）
    if keyword:
        query = query.filter(Device.name.like(f"%{keyword}%"))
    if category_id:
        query = query.filter(Device.category_id == category_id)
    if status:
        query = query.filter(Device.status == status)
    if location:
        query = query.filter(Device.location.like(f"%{location}%"))

    query = query.order_by(Device.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 字段粒度：有管理权限看完整字段
    perms = getattr(g, "current_permissions", set())
    full = "device:create" in perms or "device:update" in perms

    return success({
        "items": [d.to_dict(full=full) for d in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
    })


# ==================== 设备详情 ====================

@device_bp.get("/<int:did>")
@require_permission("device:list")
def get_device(did):
    device = Device.query.filter_by(id=did, is_deleted=0).first()
    if not device:
        return error("设备不存在")
    perms = getattr(g, "current_permissions", set())
    full = "device:create" in perms or "device:update" in perms
    return success(device.to_dict(full=full))


# ==================== 添加设备 ====================

@device_bp.post("")
@require_permission("device:create")
def create_device():
    data = request.get_json(silent=True) or {}

    name = sanitize_input((data.get("name") or "").strip())
    category_id = data.get("category_id")

    ok, msg = check_required(name, "设备名称")
    if not ok:
        return error(msg)
    if not category_id:
        return error("请选择设备分类")

    category = DeviceCategory.query.get(category_id)
    if not category:
        return error("所选分类不存在")

    # 自动生成设备编号：LAB-{分类前3字母大写}-{序号}
    device_no = _generate_device_no(category)

    device = Device(
        device_no=device_no,
        name=name,
        model=sanitize_input((data.get("model") or "").strip()),
        category_id=category_id,
        location=sanitize_input((data.get("location") or "").strip()),
        status=data.get("status", "IDLE"),
        purchase_date=_parse_date(data.get("purchase_date")),
        asset_value=data.get("asset_value") or None,
        image_url=sanitize_input((data.get("image_url") or "").strip()),
        remark=sanitize_input((data.get("remark") or "").strip()),
    )
    db.session.add(device)
    db.session.commit()

    log_action("DEVICE_CREATE", f"设备ID:{device.id}", f"设备编号:{device_no}")
    return success({"id": device.id, "device_no": device_no}, "设备添加成功")


# ==================== 编辑设备 ====================

@device_bp.put("/<int:did>")
@require_permission("device:update")
def update_device(did):
    device = Device.query.filter_by(id=did, is_deleted=0).first()
    if not device:
        return error("设备不存在")

    data = request.get_json(silent=True) or {}

    # 业务规则：借出中的设备不能直接改为报废
    new_status = data.get("status")
    if new_status == "SCRAPPED" and device.status == "BORROWED":
        return error("设备借出中，不能直接报废")

    if "name" in data:
        device.name = sanitize_input(data["name"].strip())
    if "model" in data:
        device.model = sanitize_input((data["model"] or "").strip())
    if "category_id" in data and data["category_id"]:
        if not DeviceCategory.query.get(data["category_id"]):
            return error("所选分类不存在")
        device.category_id = data["category_id"]
    if "location" in data:
        device.location = sanitize_input((data["location"] or "").strip())
    if new_status:
        device.status = new_status
    if "purchase_date" in data:
        device.purchase_date = _parse_date(data["purchase_date"])
    if "asset_value" in data:
        device.asset_value = data["asset_value"] or None
    if "image_url" in data:
        device.image_url = sanitize_input((data["image_url"] or "").strip())
    if "remark" in data:
        device.remark = sanitize_input((data["remark"] or "").strip())

    db.session.commit()
    log_action("DEVICE_UPDATE", f"设备ID:{did}", None)
    return success(message="设备更新成功")


# ==================== 删除设备（软删除）====================

@device_bp.delete("/<int:did>")
@require_permission("device:delete")
def delete_device(did):
    device = Device.query.filter_by(id=did, is_deleted=0).first()
    if not device:
        return error("设备不存在")

    # 检查未完结借用记录
    unfinished = BorrowRecord.query.filter(
        BorrowRecord.device_id == did,
        BorrowRecord.status.in_(UNFINISHED)
    ).first()
    if unfinished:
        return error("该设备存在未完结的借用记录，无法删除")

    device.is_deleted = 1
    db.session.commit()
    log_action("DEVICE_DELETE", f"设备ID:{did}", f"设备编号:{device.device_no}")
    return success(message="设备已删除")


# ==================== 辅助函数 ====================

def _generate_device_no(category):
    """生成设备编号：LAB-{分类名前3字符}-{3位序号}"""
    prefix = "".join(c for c in category.name if c.isalnum())[:3].upper()
    if not prefix:
        prefix = "DEV"
    count = Device.query.filter_by(category_id=category.id).count()
    return f"LAB-{prefix}-{count + 1:03d}"


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
