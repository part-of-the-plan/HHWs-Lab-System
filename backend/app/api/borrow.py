"""借用管理蓝图——系统最核心、最易出错的业务流。

⚠ 核心纪律（docs/数据库设计说明.md 第四节）：
   审批通过 / 确认归还，必须在【同一数据库事务】内
   同时更新 borrow_records.status 和 devices.status，
   否则会出现"记录说借出但设备还空闲"的数据不一致。

状态机：
  PENDING ──approve──> APPROVED ──(用户取走,这里简化为approve即BORROWED)──> BORROWED
  PENDING ──reject──> REJECTED
  BORROWED ──return-apply──> RETURN_PENDING ──confirm-return──> RETURNED
  BORROWED 超过预计归还日 ──> OVERDUE（查询时动态判定，见 model.effective_status）
"""
from datetime import datetime, date, timedelta

from flask import Blueprint, request, g, current_app
from sqlalchemy import and_

from app.extensions import db
from app.models import BorrowRecord, Device, User
from app.utils.response import success, error
from app.utils.auth_helper import require_permission, get_current_user_id
from app.utils.validators import sanitize_input
from app.utils.audit import log_action

borrow_bp = Blueprint("borrow", __name__)


# ==================== 申请借用 ====================

@borrow_bp.post("")
@require_permission("borrow:apply")
def apply_borrow():
    data = request.get_json(silent=True) or {}
    device_id = data.get("device_id")
    reason = sanitize_input((data.get("apply_reason") or "").strip())
    expected_str = (data.get("expected_return_date") or "").strip()

    if not device_id:
        return error("请选择要借用的设备")
    if not expected_str:
        return error("请填写预计归还日期")

    # 解析日期
    try:
        expected = datetime.strptime(expected_str, "%Y-%m-%d").date()
    except ValueError:
        return error("预计归还日期格式不正确(YYYY-MM-DD)")

    # 日期合法性：不能是过去，不能超过最大借用天数
    today = date.today()
    if expected < today:
        return error("预计归还日期不能早于今天")
    max_days = current_app.config["MAX_BORROW_DAYS"]
    if expected > today + timedelta(days=max_days):
        return error(f"借用天数不能超过{max_days}天")

    user_id = get_current_user_id()

    # 设备存在性 + 状态校验
    device = Device.query.filter_by(id=device_id, is_deleted=0).first()
    if not device:
        return error("设备不存在")
    if device.status != "IDLE":
        return error("该设备当前不可借用")

    # 重复申请校验：同一用户对同一设备已有 PENDING
    dup = BorrowRecord.query.filter_by(
        user_id=user_id, device_id=device_id, status="PENDING").first()
    if dup:
        return error("你已申请过该设备，请等待审批")

    # 同时借用数量上限
    max_count = current_app.config["MAX_BORROW_COUNT"]
    active = BorrowRecord.query.filter(
        BorrowRecord.user_id == user_id,
        BorrowRecord.status.in_(["PENDING", "APPROVED", "BORROWED", "RETURN_PENDING"])
    ).count()
    if active >= max_count:
        return error(f"你当前借用/申请中的设备已达上限({max_count}台)")

    # 逾期限制：有逾期未还设备的用户禁止借用新设备
    overdue_count = BorrowRecord.query.filter(
        BorrowRecord.user_id == user_id,
        BorrowRecord.status == "BORROWED",
        BorrowRecord.expected_return_date < date.today()
    ).count()
    if overdue_count > 0:
        return error(f"你有 {overdue_count} 条逾期未还记录，请先归还后再申请借用")

    # 创建记录（PENDING，此时不改设备状态——尚未批准）
    record = BorrowRecord(
        user_id=user_id,
        device_id=device_id,
        apply_reason=reason,
        expected_return_date=expected,
        status="PENDING",
    )
    db.session.add(record)
    db.session.commit()

    log_action("BORROW_APPLY", f"设备ID:{device_id}", f"借用记录ID:{record.id}")
    return success({"id": record.id}, "申请已提交，等待审批")


# ==================== 审批通过 ====================

@borrow_bp.put("/<int:rid>/approve")
@require_permission("borrow:approve")
def approve_borrow(rid):
    """通过：事务内 更新记录状态 + 设备状态→借出。含并发行锁。"""
    record = BorrowRecord.query.get(rid)
    if not record:
        return error("借用记录不存在")
    if record.status != "PENDING":
        return error("该申请不是待审批状态，无法操作")

    try:
        # 行锁锁定设备，防并发：两人同时申请同一设备时只有一个能批准
        device = Device.query.with_for_update().filter_by(
            id=record.device_id, is_deleted=0).first()
        if not device:
            db.session.rollback()
            return error("设备不存在")
        if device.status != "IDLE":
            db.session.rollback()
            return error("该设备已被借出，无法批准")

        # ── 同一事务：改记录 + 改设备 ──
        record.status = "BORROWED"     # 简化流程：审批通过即视为借出
        record.approver_id = get_current_user_id()
        record.approve_time = datetime.utcnow()
        device.status = "BORROWED"

        db.session.commit()
    except Exception:
        db.session.rollback()
        return error("审批失败，请重试")

    log_action("BORROW_APPROVE", f"借用记录ID:{rid}", f"设备ID:{record.device_id}")
    return success(message="已通过，设备状态更新为借出")


# ==================== 审批驳回 ====================

@borrow_bp.put("/<int:rid>/reject")
@require_permission("borrow:approve")
def reject_borrow(rid):
    data = request.get_json(silent=True) or {}
    reason = sanitize_input((data.get("reject_reason") or "").strip())
    if not reason:
        return error("请填写驳回理由")

    record = BorrowRecord.query.get(rid)
    if not record:
        return error("借用记录不存在")
    if record.status != "PENDING":
        return error("该申请不是待审批状态，无法操作")

    # 驳回不动设备状态
    record.status = "REJECTED"
    record.approver_id = get_current_user_id()
    record.approve_time = datetime.utcnow()
    record.reject_reason = reason
    db.session.commit()

    log_action("BORROW_REJECT", f"借用记录ID:{rid}", reason)
    return success(message="已驳回")


# ==================== 用户申请归还 ====================

@borrow_bp.put("/<int:rid>/return-apply")
@require_permission("record:self")
def return_apply(rid):
    record = BorrowRecord.query.get(rid)
    if not record:
        return error("借用记录不存在")
    # 只能还自己的
    if record.user_id != get_current_user_id():
        return error("无权操作该记录", code=403, http_status=403)
    if record.status not in ("BORROWED", "OVERDUE"):
        return error("该记录当前状态不可申请归还")

    # 申请归还：记录状态→待确认，设备仍保持借出（管理员还没收到实物）
    record.status = "RETURN_PENDING"
    record.actual_return_time = datetime.utcnow()
    db.session.commit()

    log_action("BORROW_RETURN_APPLY", f"借用记录ID:{rid}", None)
    return success(message="已申请归还，等待管理员确认")


# ==================== 管理员确认归还 ====================

@borrow_bp.put("/<int:rid>/confirm-return")
@require_permission("borrow:return")
def confirm_return(rid):
    """确认归还：事务内 更新记录状态 + 设备状态→空闲。"""
    data = request.get_json(silent=True) or {}
    remark = sanitize_input((data.get("remark") or "").strip())

    record = BorrowRecord.query.get(rid)
    if not record:
        return error("借用记录不存在")
    if record.status != "RETURN_PENDING":
        return error("该记录不是待确认归还状态")

    try:
        device = Device.query.with_for_update().get(record.device_id)
        # ── 同一事务：改记录 + 改设备 ──
        record.status = "RETURNED"
        record.return_confirm_time = datetime.utcnow()
        record.return_confirmer_id = get_current_user_id()
        if remark:
            record.remark = remark
        if device:
            device.status = "IDLE"
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error("确认归还失败，请重试")

    log_action("BORROW_CONFIRM_RETURN", f"借用记录ID:{rid}", remark or None)
    return success(message="已确认归还，设备状态更新为空闲")


# ==================== 借用记录查询 ====================

@borrow_bp.get("")
def list_borrows():
    """记录查询：
       - 有 record:all 权限 → 看全部
       - 否则只能看自己的（record:self）
       支持分页 + 状态筛选 + 设备名筛选。
    """
    # 鉴权：必须有 self 或 all 之一
    perms = getattr(g, "current_permissions", set())
    if "record:all" not in perms and "record:self" not in perms:
        return error("无权限", code=403, http_status=403)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    status_filter = request.args.get("status")
    keyword = request.args.get("keyword", "").strip()

    query = BorrowRecord.query

    # 数据行级隔离：无 record:all 只能看自己
    if "record:all" not in perms:
        query = query.filter(BorrowRecord.user_id == get_current_user_id())

    if status_filter:
        query = query.filter(BorrowRecord.status == status_filter)

    if keyword:
        query = query.join(Device).filter(Device.name.like(f"%{keyword}%"))

    query = query.order_by(BorrowRecord.apply_time.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success({
        "items": [r.to_dict() for r in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
    })
