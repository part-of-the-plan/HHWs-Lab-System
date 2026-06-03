"""用户模型（users 表）"""
from datetime import datetime
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False, comment="格式 盐$哈希(SM3)")
    real_name = db.Column(db.String(50), nullable=False)
    phone_enc = db.Column(db.String(255), comment="SM4加密后的手机号(hex)")
    email = db.Column(db.String(100), unique=True)
    status = db.Column(db.Integer, nullable=False, default=1, comment="1正常 0禁用")
    fail_count = db.Column(db.Integer, nullable=False, default=0, comment="连续登录失败次数")
    lock_until = db.Column(db.DateTime, comment="锁定截止时间, NULL=未锁")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：该用户拥有哪些角色（多对多，经 user_roles 桥表）
    roles = db.relationship("Role", secondary="user_roles", back_populates="users",
                            lazy="joined")

    # 关系：该用户的借用记录
    borrow_records = db.relationship("BorrowRecord", back_populates="user",
                                     foreign_keys="BorrowRecord.user_id")

    def is_locked(self):
        if not self.lock_until:
            return False
        return self.lock_until > datetime.utcnow()

    def get_permissions(self):
        """返回该用户所有权限标识集合(去重)"""
        perms = set()
        for role in self.roles:
            for rp in role.permissions:
                perms.add(rp.perm_code)
        return perms

    def to_dict(self, include_phone=False):
        d = {
            "id": self.id,
            "username": self.username,
            "real_name": self.real_name,
            "email": self.email,
            "status": self.status,
            "created_at": str(self.created_at) if self.created_at else None,
        }
        if include_phone:
            from app.utils.crypto import decrypt_field, mask_phone
            raw = decrypt_field(self.phone_enc) if self.phone_enc else ""
            d["phone"] = mask_phone(raw)
            d["phone_full"] = raw  # 管理员导出时用
        return d
