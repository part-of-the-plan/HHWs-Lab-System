"""操作日志模型（operation_logs 表，只追加写）"""
from datetime import datetime
from app.extensions import db


class OperationLog(db.Model):
    __tablename__ = "operation_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    operator_id = db.Column(db.BigInteger, comment="操作者ID, 可空")
    username = db.Column(db.String(50), comment="冗余存储, 免联表")
    action = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(100))
    detail = db.Column(db.Text, comment="JSON 记录具体改动")
    ip = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        from app.utils.timezone import to_beijing_time
        return {
            "id": self.id,
            "operator_id": self.operator_id,
            "username": self.username,
            "action": self.action,
            "target": self.target,
            "detail": self.detail,
            "ip": self.ip,
            "user_agent": self.user_agent,
            "created_at": to_beijing_time(self.created_at),
        }
