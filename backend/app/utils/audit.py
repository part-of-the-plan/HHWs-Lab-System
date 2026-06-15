"""共享审计日志工具：业务代码统一调用 log_action() 写操作日志。

设计：日志写入失败不影响主业务（独立 try/except + rollback）。
注意：调用前主业务应已 commit，或在同一 session 内 log 后统一 commit。
本函数自带 commit，适合"主业务 commit 后补记日志"的场景。
"""
from flask import request, g
from app.extensions import db


def log_action(action, target=None, detail=None):
    """记录一条操作日志。自动从请求上下文取 操作者/IP/UA。

    :param action: 操作类型枚举，如 DEVICE_CREATE / BORROW_APPROVE
    :param target: 操作目标，如 "设备ID:15"
    :param detail: 详情字符串（可传 JSON 字符串）
    """
    try:
        from app.models.log import OperationLog
        operator_id = getattr(g, "current_user_id", None)
        username = None
        user = getattr(g, "current_user", None)
        if user is not None:
            username = user.username

        log = OperationLog(
            operator_id=operator_id,
            username=username,
            action=action,
            target=target,
            detail=detail,
            ip=request.remote_addr if request else None,
            user_agent=(request.headers.get("User-Agent", "")[:255]
                        if request else None),
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
