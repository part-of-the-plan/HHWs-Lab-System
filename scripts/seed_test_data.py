"""测试数据播种脚本 —— 一行命令填满数据库。

用法（本机，Docker MySQL 在跑时）：
    cd project
    python scripts/seed_test_data.py

幂等：同名用户/设备已存在则跳过，可以反复跑不重复造。

队友只需编辑下面四个区块的内容，不动代码逻辑。
"""
import sys
from pathlib import Path

# 把 backend 加到 sys.path，让脚本能找到 app 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app import create_app
from app.extensions import db
from app.models import (
    User, Role, UserRole, Device, DeviceCategory, BorrowRecord,
)
from app.utils.crypto import hash_password, encrypt_field
from datetime import date, timedelta, datetime

# ═══════════════════════════════════════════════════════════════
# 📝 区块 1：设备分类（队友直接改下面的名称和描述）
# ═══════════════════════════════════════════════════════════════
CATEGORIES = [
    ("电子测量仪器", "示波器、信号发生器、频谱仪等"),
    ("计算机设备", "笔记本、台式机、服务器等"),
    ("光学仪器", "显微镜、光谱仪、激光器等"),
    ("机械工具", "3D打印机、CNC、电钻等"),
    ("网络设备", "交换机、路由器、防火墙等"),
]

# ═══════════════════════════════════════════════════════════════
# 📝 区块 2：设备清单（队友在下面填真实设备）
#   name=设备名  model=型号  category=分类名(上面写的)  location=位置
# ═══════════════════════════════════════════════════════════════
DEVICES = [
    # ---- 电子测量仪器 ----
    ("数字示波器",       "DSO-X 2014A",    "电子测量仪器", "A栋302-柜C-第2层"),
    ("函数信号发生器",   "DG1022Z",         "电子测量仪器", "A栋302-柜C-第3层"),
    ("频谱分析仪",       "N9320B",          "电子测量仪器", "A栋302-柜D-第1层"),
    ("万用表",           "Fluke 87V",       "电子测量仪器", "A栋302-柜A-第1层"),
    # ---- 计算机设备 ----
    ("高性能笔记本",     "ThinkPad X1",     "计算机设备",   "A栋301-桌面"),
    ("台式工作站",       "Dell Precision",  "计算机设备",   "A栋301-桌面"),
    ("开发测试服务器",   "HP ProLiant DL360","计算机设备",  "A栋301-机房"),
    ("开发板套件",       "Raspberry Pi 4",  "计算机设备",   "A栋301-柜B"),
    # ---- 光学仪器 ----
    ("光学显微镜",       "Olympus CX23",    "光学仪器",     "A栋304-实验台A"),
    ("紫外光谱仪",       "UV-2600i",        "光学仪器",     "A栋304-实验台B"),
    ("激光器",           "He-Ne 632.8nm",   "光学仪器",     "A栋304-柜E"),
    # ---- 机械工具 ----
    ("3D打印机",         "Ultimaker S5",    "机械工具",     "A栋303-工作台A"),
    ("CNC雕刻机",        "Shapeoko 4",      "机械工具",     "A栋303-工作台B"),
    ("数字焊台",         "Hakko FX-951",    "机械工具",     "A栋303-柜F"),
    # ---- 网络设备 ----
    ("三层交换机",       "Cisco C9300",     "网络设备",     "A栋301-机柜"),
    ("无线路由器",       "TP-Link AX6000",  "网络设备",     "A栋301-桌面"),
]

# ═══════════════════════════════════════════════════════════════
# 📝 区块 3：测试用户（队友改名字）
# ═══════════════════════════════════════════════════════════════
TEST_USERS = [
    {"username": "zhangsan",  "password": "Zh@ng123", "real_name": "张三", "phone": "13800001111", "role": "NORMAL_USER"},
    {"username": "lisi",      "password": "Li@si456",  "real_name": "李四", "phone": "13800002222", "role": "NORMAL_USER"},
    {"username": "wangwu",    "password": "W@ngwu789", "real_name": "王五", "phone": "13800003333", "role": "NORMAL_USER"},
    {"username": "labadmin1", "password": "L@b88888",  "real_name": "赵管理员", "phone": "13800004444", "role": "LAB_ADMIN"},
]

# ═══════════════════════════════════════════════════════════════
# 📝 区块 4：借用记录（队友配"谁借什么设备，什么状态"）
#   状态选: PENDING / APPROVED / BORROWED / RETURNED / REJECTED
#   username 必须是上面 TEST_USERS 里有的
#   device_name 必须是上面 DEVICES 里有的
# ═══════════════════════════════════════════════════════════════
BORROWS = [
    # (用户名,   设备名,         状态,       预计借N天, 备注)
    ("zhangsan",  "数字示波器",   "BORROWED",     7,    "毕业设计电路测试"),
    ("zhangsan",  "万用表",       "RETURNED",    14,    "已完成实验"),
    ("lisi",      "3D打印机",     "PENDING",      5,    "课程作业打印模型"),
    ("lisi",      "函数信号发生器","BORROWED",    10,    "信号处理实验"),
    ("wangwu",    "光学显微镜",   "RETURN_PENDING", 3,  "材料观察实验"),
    ("wangwu",    "高性能笔记本", "REJECTED",      7,    "外出调研"),
    ("wangwu",    "开发板套件",   "BORROWED",    21,    "嵌入式开发项目"),
    ("zhangsan",  "台式工作站",   "OVERDUE",      -5,   "延期未还（设为PENDING天数=-5模拟逾期）"),
]

# ═══════════════════════════════════════════════════════════════
# 以下是执行逻辑，队友不用看
# ═══════════════════════════════════════════════════════════════

app = create_app()


def run():
    with app.app_context():
        # --- 分类 ---
        cat_map = {}
        for name, desc in CATEGORIES:
            cat = DeviceCategory.query.filter_by(name=name).first()
            if not cat:
                cat = DeviceCategory(name=name, description=desc)
                db.session.add(cat)
                print(f"[CATEGORY] + {name}")
            cat_map[name] = cat
        db.session.commit()

        # --- 角色映射 ---
        role_map = {r.role_code: r for r in Role.query.all()}

        # --- 用户 ---
        user_map = {}
        for u in TEST_USERS:
            if User.query.filter_by(username=u["username"]).first():
                print(f"[USER]  跳过（已存在）: {u['username']}")
                user_map[u["username"]] = User.query.filter_by(username=u["username"]).first()
                continue
            user = User(
                username=u["username"],
                password_hash=hash_password(u["password"]),
                real_name=u["real_name"],
                phone_enc=encrypt_field(u["phone"]),
                status=1,
            )
            db.session.add(user)
            db.session.flush()
            role = role_map.get(u["role"])
            if role:
                db.session.add(UserRole(user_id=user.id, role_id=role.id))
            print(f"[USER]   + {u['username']} → {u['role']}")
            user_map[u["username"]] = user
        db.session.commit()

        # --- 设备 ---
        dev_map = {}
        for name, model, cat_name, location in DEVICES:
            if Device.query.filter_by(name=name, is_deleted=0).first():
                print(f"[DEVICE] 跳过（已存在）: {name}")
                dev_map[name] = Device.query.filter_by(name=name, is_deleted=0).first()
                continue
            cat = cat_map.get(cat_name)
            if not cat:
                print(f"[DEVICE] 跳过（分类不存在）: {cat_name}")
                continue
            prefix = "".join(c for c in cat.name if c.isalnum())[:3].upper() or "DEV"
            count = Device.query.filter_by(category_id=cat.id).count()
            dev_no = f"LAB-{prefix}-{count + 1:03d}"
            dev = Device(
                device_no=dev_no,
                name=name,
                model=model,
                category_id=cat.id,
                location=location,
                status="IDLE",
                is_deleted=0,
            )
            db.session.add(dev)
            print(f"[DEVICE] + {dev_no} {name}")
            dev_map[name] = dev
        db.session.commit()

        # --- 借用记录 ---
        today = date.today()
        created = 0
        for i, (user_name, dev_name, status, delta_days, remark) in enumerate(BORROWS):
            user = user_map.get(user_name)
            dev = dev_map.get(dev_name)
            if not user or not dev:
                print(f"[BORROW] 跳过（用户或设备不存在）: {user_name} → {dev_name}")
                continue

            # 按分钟错开申请时间
            apply_dt = datetime.utcnow() - timedelta(days=abs(delta_days), minutes=i * 7)
            expected = (apply_dt + timedelta(days=abs(delta_days) if delta_days > 0 else 5)).date()
            if expected < today:
                expected = today + timedelta(days=5)

            record = BorrowRecord(
                user_id=user.id,
                device_id=dev.id,
                apply_time=apply_dt,
                apply_reason=remark,
                expected_return_date=expected,
                status=status,
            )

            # 根据状态补审批/归还字段
            superadmin = User.query.filter_by(username="superadmin").first()
            if status in ("APPROVED", "BORROWED", "RETURN_PENDING", "RETURNED", "OVERDUE"):
                record.approver_id = superadmin.id if superadmin else None
                record.approve_time = apply_dt + timedelta(hours=1)
            if status == "OVERDUE":
                record.status = "BORROWED"
                record.expected_return_date = date.today() - timedelta(days=3)
            if status == "REJECTED":
                record.approver_id = superadmin.id if superadmin else None
                record.approve_time = apply_dt + timedelta(hours=1)
                record.reject_reason = "该设备暂不可借用，请联系管理员"
            if status == "RETURN_PENDING":
                record.actual_return_time = apply_dt + timedelta(days=abs(delta_days))
                dev.status = "BORROWED"
            if status == "RETURNED":
                record.approve_time = apply_dt + timedelta(hours=1)
                record.actual_return_time = apply_dt + timedelta(days=abs(delta_days))
                record.return_confirmer_id = superadmin.id if superadmin else None
                record.return_confirm_time = apply_dt + timedelta(days=abs(delta_days) + 1)
                dev.status = "IDLE"

            if status in ("BORROWED", "RETURN_PENDING", "OVERDUE"):
                dev.status = "BORROWED"

            db.session.add(record)
            db.session.commit()
            print(f"[BORROW] + {user_name} → {dev_name} [{status}]")
            created += 1

        print(f"\n✅ 完成！新增 {len(user_map)} 个用户，{len(dev_map)} 台设备，{created} 条借用记录")


if __name__ == "__main__":
    run()
