"""RBAC 角色与权限模型（roles / permissions / user_roles / role_permissions 4表）"""
from app.extensions import db


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    role_code = db.Column(db.String(50), nullable=False, unique=True)
    role_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))

    users = db.relationship("User", secondary="user_roles", back_populates="roles",
                            lazy="joined")
    # role_permissions 在 Permission 侧定义,这里反向引用
    permissions = db.relationship(
        "Permission", secondary="role_permissions",
        backref=db.backref("roles", lazy="joined"),
        lazy="joined"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "role_code": self.role_code,
            "role_name": self.role_name,
            "description": self.description,
            "user_count": len(self.users) if self.users else 0,
        }


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    perm_code = db.Column(db.String(50), nullable=False, unique=True)
    perm_name = db.Column(db.String(50), nullable=False)
    module = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "perm_code": self.perm_code,
            "perm_name": self.perm_name,
            "module": self.module,
        }


class UserRole(db.Model):
    __tablename__ = "user_roles"
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"),
                        primary_key=True)
    role_id = db.Column(db.BigInteger, db.ForeignKey("roles.id", ondelete="CASCADE"),
                        primary_key=True)


class RolePermission(db.Model):
    __tablename__ = "role_permissions"
    role_id = db.Column(db.BigInteger, db.ForeignKey("roles.id", ondelete="CASCADE"),
                        primary_key=True)
    perm_id = db.Column(db.BigInteger, db.ForeignKey("permissions.id", ondelete="CASCADE"),
                        primary_key=True)
