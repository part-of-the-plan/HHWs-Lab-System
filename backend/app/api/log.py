"""操作日志查看蓝图——超管/安全审计用：日志列表（分页+筛选）。

要点：
- 只读，无写操作
- 支持按 action 类型 / 用户名 / 时间范围筛选
- 按时间倒序，最新在前
"""
from datetime import datetime

from flask import Blueprint, request
from app.extensions import db
from app.models.log import OperationLog
from app.utils.response import success
from app.utils.auth_helper import require_permission


log_bp = Blueprint("log", __name__)


@log_bp.get("")
@require_permission("log:view")
def list_logs():
    """操作日志列表，支持分页 + action/用户名/时间范围筛选。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    action = request.args.get("action", "").strip()
    username = request.args.get("username", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    query = OperationLog.query

    if action:
        query = query.filter(OperationLog.action == action)
    if username:
        query = query.filter(OperationLog.username.like(f"%{username}%"))
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(OperationLog.created_at >= dt_from)
        except ValueError:
            pass  # 忽略无效日期
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            # 日期范围包含当天全天
            from datetime import timedelta
            query = query.filter(OperationLog.created_at < dt_to + timedelta(days=1))
        except ValueError:
            pass

    query = query.order_by(OperationLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success({
        "items": [r.to_dict() for r in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
    })
