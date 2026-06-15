"""数据统计蓝图——看板用：设备概览 / 借用趋势 / 设备利用率。

要点：
- 返回格式 {labels: [...], values: [...]}，前端 ECharts 直接用
- 聚合查询用 SQLAlchemy 原生，复杂场景可回退 text()
"""
from datetime import datetime, date, timedelta

from flask import Blueprint
from sqlalchemy import func, text

from app.extensions import db
from app.models import Device, BorrowRecord
from app.utils.response import success
from app.utils.auth_helper import require_permission


stats_bp = Blueprint("stats", __name__)


# ==================== 设备概览 ====================

@stats_bp.get("/overview")
@require_permission("stats:view")
def overview():
    """各状态设备数量 + 逾期设备数。
    返回: {statuses: {labels, values}, overdue_count: int}
    """
    # 各状态设备数量
    rows = (
        db.session.query(Device.status, func.count(Device.id))
        .filter(Device.is_deleted == 0)
        .group_by(Device.status)
        .all()
    )

    labels = []
    values = []
    for status, cnt in rows:
        labels.append(status)
        values.append(cnt)

    # 逾期借用数（超过预计归还日且未归还）
    today = date.today()
    overdue_count = BorrowRecord.query.filter(
        BorrowRecord.status.in_(["BORROWED", "OVERDUE"]),
        BorrowRecord.expected_return_date < today,
    ).count()

    return success({
        "statuses": {"labels": labels, "values": values},
        "overdue_count": overdue_count,
    })


# ==================== 借用趋势（最近30天）====================

@stats_bp.get("/trend")
@require_permission("stats:view")
def trend():
    """最近30天每日借用申请数。
    返回: {labels: [日期...], values: [数量...]}
    """
    days = 30
    start_date = date.today() - timedelta(days=days - 1)

    rows = (
        db.session.query(
            func.date(BorrowRecord.apply_time).label("d"),
            func.count(BorrowRecord.id),
        )
        .filter(BorrowRecord.apply_time >= start_date)
        .group_by(func.date(BorrowRecord.apply_time))
        .order_by("d")
        .all()
    )

    # 补全没有数据的日期（填 0）
    data_map = {str(r[0]): r[1] for r in rows}
    labels = []
    values = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        ds = str(d)
        labels.append(ds)
        values.append(data_map.get(ds, 0))

    return success({"labels": labels, "values": values})


# ==================== 设备利用率 TOP10 ====================

@stats_bp.get("/utilization")
@require_permission("stats:view")
def utilization():
    """借用次数 TOP10 设备。
    返回: {labels: [设备名...], values: [借用次数...]}
    """
    rows = (
        db.session.query(
            Device.name,
            func.count(BorrowRecord.id),
        )
        .join(BorrowRecord, BorrowRecord.device_id == Device.id)
        .filter(Device.is_deleted == 0)
        .group_by(Device.id, Device.name)
        .order_by(func.count(BorrowRecord.id).desc())
        .limit(10)
        .all()
    )

    return success({
        "labels": [r[0] for r in rows],
        "values": [r[1] for r in rows],
    })
