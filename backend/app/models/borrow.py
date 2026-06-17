"""借用记录模型（borrow_records 表，核心业务）"""
from datetime import datetime, date
from app.extensions import db


class BorrowRecord(db.Model):
    __tablename__ = "borrow_records"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    device_id = db.Column(db.BigInteger, db.ForeignKey("devices.id"), nullable=False)
    apply_time = db.Column(db.DateTime, default=datetime.utcnow)
    apply_reason = db.Column(db.String(255))
    expected_return_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PENDING")
    approver_id = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    approve_time = db.Column(db.DateTime)
    reject_reason = db.Column(db.String(255))
    actual_return_time = db.Column(db.DateTime)
    return_confirm_time = db.Column(db.DateTime)
    return_confirmer_id = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    remark = db.Column(db.String(255))

    user = db.relationship("User", back_populates="borrow_records",
                           foreign_keys=[user_id])
    device = db.relationship("Device", back_populates="borrow_records")
    approver = db.relationship("User", foreign_keys=[approver_id])
    return_confirmer = db.relationship("User", foreign_keys=[return_confirmer_id])

    # ---- 逾期判断（方式一:查询时判断,即方案推荐方式）----
    def is_overdue(self):
        if self.status == "BORROWED" and self.expected_return_date:
            return self.expected_return_date < date.today()
        return self.status == "OVERDUE"

    def effective_status(self):
        """逻辑状态：BORROWED 但逾期 → 返回 OVERDUE"""
        if self.status == "BORROWED" and self.is_overdue():
            return "OVERDUE"
        return self.status

    def to_dict(self):
        from app.utils.timezone import to_beijing_time
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.real_name if self.user else None,
            "device_id": self.device_id,
            "device_name": self.device.name if self.device else None,
            "device_no": self.device.device_no if self.device else None,
            "apply_time": to_beijing_time(self.apply_time),
            "apply_reason": self.apply_reason,
            "expected_return_date": str(self.expected_return_date) if self.expected_return_date else None,
            "status": self.effective_status(),
            "is_overdue": self.is_overdue(),
            "approver_name": self.approver.real_name if self.approver else None,
            "approve_time": to_beijing_time(self.approve_time),
            "reject_reason": self.reject_reason,
            "actual_return_time": to_beijing_time(self.actual_return_time),
            "return_confirm_time": to_beijing_time(self.return_confirm_time),
            "return_confirmer_name": self.return_confirmer.real_name if self.return_confirmer else None,
            "remark": self.remark,
        }
