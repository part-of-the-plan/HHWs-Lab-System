"""数据模型统一导入（所有模型注册到 db.Model.metadata，Migrate 才能识别）"""
from .user import User
from .role import Role, Permission, UserRole, RolePermission
from .device import Device, DeviceCategory
from .borrow import BorrowRecord
from .log import OperationLog

__all__ = [
    "User", "Role", "Permission", "UserRole", "RolePermission",
    "Device", "DeviceCategory",
    "BorrowRecord",
    "OperationLog",
]
