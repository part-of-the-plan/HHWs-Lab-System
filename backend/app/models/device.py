"""设备管理模型（device_categories / devices 2表）"""
from datetime import datetime
from app.extensions import db


class DeviceCategory(db.Model):
    __tablename__ = "device_categories"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))

    # 关系：该分类下所有设备
    devices = db.relationship("Device", back_populates="category", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_no = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100))
    category_id = db.Column(db.BigInteger, db.ForeignKey("device_categories.id"),
                            nullable=False)
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), nullable=False, default="IDLE")
    purchase_date = db.Column(db.Date)
    asset_value = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.String(255))
    remark = db.Column(db.String(255))
    is_deleted = db.Column(db.Integer, nullable=False, default=0, comment="软删除 1已删")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("DeviceCategory", back_populates="devices")
    borrow_records = db.relationship("BorrowRecord", back_populates="device")

    def is_available(self):
        return self.status == "IDLE" and not self.is_deleted

    def to_dict(self, full=False):
        d = {
            "id": self.id,
            "device_no": self.device_no,
            "name": self.name,
            "model": self.model,
            "category_name": self.category.name if self.category else None,
            "category_id": self.category_id,
            "location": self.location,
            "status": self.status,
        }
        if full:
            d.update({
                "purchase_date": str(self.purchase_date) if self.purchase_date else None,
                "asset_value": float(self.asset_value) if self.asset_value else None,
                "image_url": self.image_url,
                "remark": self.remark,
            })
        return d
