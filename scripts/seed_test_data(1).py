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
    ("音频设备", "麦克风、扬声器、音频分析仪等"),
    ("存储设备", "硬盘、U盘、SD卡等"),
    ("电源设备", "稳压电源、UPS、适配器等"),
    ("物联网设备", "传感器、网关、RFID设备等"),
    ("教学实验设备", "通用教学实验箱、实训平台"),
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
    ("逻辑分析仪",       "Tektronix TLA7012","电子测量仪器", "A栋302-柜C-第4层"),
    ("信号分析仪",       "Keysight N9020B",  "电子测量仪器", "A栋302-柜D-第2层"),
    ("直流稳压电源",     "GW INSTEK GPD-3303S","电子测量仪器","A栋302-柜A-第2层"),
    ("LCR数字电桥",      "TH2811D",          "电子测量仪器", "A栋302-柜B-第1层"),
    ("高压探头",         "P5100",            "电子测量仪器", "A栋302-柜B-第2层"),
    ("频率计数器",       "Agilent 53131A",    "电子测量仪器", "A栋302-柜D-第3层"),

    # ---- 计算机设备 ----
    ("高性能笔记本",     "ThinkPad X1",     "计算机设备",   "A栋301-桌面"),
    ("台式工作站",       "Dell Precision",  "计算机设备",   "A栋301-桌面"),
    ("开发测试服务器",   "HP ProLiant DL360","计算机设备",  "A栋301-机房"),
    ("开发板套件",       "Raspberry Pi 4",  "计算机设备",   "A栋301-柜B"),
    ("图形工作站",       "NVIDIA DGX Station","计算机设备", "A栋301-机房"),
    ("嵌入式开发板",     "NVIDIA Jetson Nano","计算机设备", "A栋301-柜B"),
    ("迷你主机",         "Intel NUC 11",     "计算机设备",   "A栋301-柜C"),
    ("便携式一体机",     "HP EliteOne",      "计算机设备",   "A栋301-桌面"),
    ("FPGA开发板",       "Xilinx ZedBoard",  "计算机设备",   "A栋301-柜B"),
    ("人工智能开发套件", "HUAWEI Atlas 200", "计算机设备",   "A栋301-柜C"),

    # ---- 光学仪器 ----
    ("光学显微镜",       "Olympus CX23",    "光学仪器",     "A栋304-实验台A"),
    ("紫外光谱仪",       "UV-2600i",        "光学仪器",     "A栋304-实验台B"),
    ("激光器",           "He-Ne 632.8nm",   "光学仪器",     "A栋304-柜E"),
    ("红外热像仪",       "FLIR E60",        "光学仪器",     "A栋304-实验台C"),
    ("体视显微镜",       "Leica M125",      "光学仪器",     "A栋304-柜E"),
    ("激光测距仪",       "Leica DISTO",     "光学仪器",     "A栋304-柜E"),
    ("光学平台",         "RS 400mm",        "光学仪器",     "A栋304-实验台D"),
    ("光纤光谱仪",       "Ocean Optics",    "光学仪器",     "A栋304-实验台B"),

    # ---- 机械工具 ----
    ("3D打印机",         "Ultimaker S5",    "机械工具",     "A栋303-工作台A"),
    ("CNC雕刻机",        "Shapeoko 4",      "机械工具",     "A栋303-工作台B"),
    ("数字焊台",         "Hakko FX-951",    "机械工具",     "A栋303-柜F"),
    ("热风枪",           "QUICK 857D",      "机械工具",     "A栋303-柜F"),
    ("微型台钻",         "BENCH DRILL",     "机械工具",     "A栋303-工作台C"),
    ("精密螺丝刀套装",   "VESSEL 2200PC",   "机械工具",     "A栋303-工具柜"),
    ("剪钳套件",         "Tsunoda CCP-100", "机械工具",     "A栋303-工具柜"),

    # ---- 网络设备 ----
    ("三层交换机",       "Cisco C9300",     "网络设备",     "A栋301-机柜"),
    ("无线路由器",       "TP-Link AX6000",  "网络设备",     "A栋301-桌面"),
    ("企业级防火墙",     "Huawei USG6000",  "网络设备",     "A栋301-机柜"),
    ("POE交换机",        "H3C S1850",       "网络设备",     "A栋301-机柜"),
    ("无线AP",           "Cisco 9120AX",    "网络设备",     "A栋301-天花板"),

    # ---- 音频设备 ----
    ("电容麦克风",       "Rode NT1-A",      "音频设备",     "A栋305-录音室"),
    ("监听音箱",         "Genelec 8040B",   "音频设备",     "A栋305-录音室"),
    ("音频接口",         "Focusrite 4i4",   "音频设备",     "A栋305-录音桌"),
    ("噪声分析仪",       "NTI Audio XL2",   "音频设备",     "A栋305-柜G"),

    # ---- 存储设备 ----
    ("移动硬盘",         "WD My Passport 4TB","存储设备", "A栋301-柜A"),
    ("固态U盘",          "SanDisk 1TB",      "存储设备",     "A栋301-柜A"),
    ("NAS存储服务器",    "Synology DS224+",  "存储设备",     "A栋301-机房"),
    ("工业SD卡",         "SanDisk Industrial","存储设备",  "A栋301-柜A"),

    # ---- 电源设备 ----
    ("可编程电源",       "Agilent N6705B",  "电源设备",     "A栋302-柜A-第2层"),
    ("UPS不间断电源",    "APC BK650M2",     "电源设备",     "A栋301-机柜"),
    ("电池测试仪",       "Hioki BT3554",    "电源设备",     "A栋302-柜A-第3层"),
    ("电子负载",         "Chroma 6330A",    "电源设备",     "A栋302-柜B-第3层"),

    # ---- 物联网设备 ----
    ("温湿度传感器",     "SHT31",           "物联网设备",   "A栋306-实验架"),
    ("RFID读写器",       "MFRC-522",        "物联网设备",   "A栋306-实验架"),
    ("LoRa网关",         "RAK7248",         "物联网设备",   "A栋306-机柜"),
    ("空气质量传感器",   "PMS5003",         "物联网设备",   "A栋306-实验架"),

    # ---- 教学实验设备 ----
    ("单片机实验箱",     "STC89C52",        "教学实验设备", "A栋307-实验台"),
    ("模拟电路实验箱",   "SA-200",          "教学实验设备", "A栋307-实验台"),
    ("数字电路实验箱",   "SB-300",          "教学实验设备", "A栋307-实验台"),
    ("通信原理实验箱",   "TX-3000",         "教学实验设备", "A栋307-实验台"),
]

# ═══════════════════════════════════════════════════════════════
# 📝 区块 3：测试用户（队友改名字）
# ═══════════════════════════════════════════════════════════════
TEST_USERS = [
    {"username": "zhangsan",  "password": "Zh@ng123", "real_name": "张三", "phone": "13800001111", "role": "NORMAL_USER"},
    {"username": "lisi",      "password": "Li@si456",  "real_name": "李四", "phone": "13800002222", "role": "NORMAL_USER"},
    {"username": "wangwu",    "password": "W@ngwu789", "real_name": "王五", "phone": "13800003333", "role": "NORMAL_USER"},
    {"username": "labadmin1", "password": "L@b88888",  "real_name": "赵管理员", "phone": "13800004444", "role": "LAB_ADMIN"},
    {"username": "zhaoliu",   "password": "Zh@o666",   "real_name": "赵六", "phone": "13800005555", "role": "NORMAL_USER"},
    {"username": "sunqi",     "password": "Su@n777",   "real_name": "孙七", "phone": "13800006666", "role": "NORMAL_USER"},
    {"username": "zhouba",    "password": "Zh@u888",   "real_name": "周八", "phone": "13800007777", "role": "NORMAL_USER"},
    {"username": "labadmin2", "password": "L@b99999",  "real_name": "钱管理员", "phone": "13800008888", "role": "LAB_ADMIN"},
    {"username": "wujian",    "password": "Wu@j123",    "real_name": "吴九", "phone": "13800009999", "role": "NORMAL_USER"},
    {"username": "zhengsan",  "password": "Zh@ng456",  "real_name": "郑十", "phone": "13800010000", "role": "NORMAL_USER"},
    {"username": "wangyi",    "password": "W@ng123",    "real_name": "王一", "phone": "13800011111", "role": "NORMAL_USER"},
    {"username": "fengyi",    "password": "F@ng123",    "real_name": "冯一", "phone": "13800012222", "role": "NORMAL_USER"},
    {"username": "chenyi",    "password": "Ch@n123",    "real_name": "陈一", "phone": "13800013333", "role": "NORMAL_USER"},
    {"username": "labadmin3", "password": "L@b77777",  "real_name": "孙管理员", "phone": "13800014444", "role": "LAB_ADMIN"},
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
    ("zhaoliu",   "迷你主机",     "APPROVED",      3,    "数据处理任务"),
    ("zhaoliu",   "移动硬盘",     "BORROWED",      5,    "数据备份"),
    ("sunqi",     "信号分析仪",   "PENDING",       7,    "射频测试"),
    ("sunqi",     "可编程电源",   "RETURNED",     10,    "电路测试完成"),
    ("zhouba",    "电容麦克风",   "BORROWED",      3,    "语音采集实验"),
    ("zhouba",    "红外热像仪",   "RETURN_PENDING", 2,   "温度检测"),
    ("lisi",      "体视显微镜",   "REJECTED",      5,    "设备维护中"),
    ("zhangsan",  "图形工作站",   "OVERDUE",      -3,   "计算任务延期"),
    ("wujian",    "FPGA开发板",   "BORROWED",      7,    "数字逻辑设计"),
    ("wujian",    "数字焊台",     "RETURNED",      5,    "硬件焊接实训"),
    ("zhengsan",  "三层交换机",   "PENDING",       4,    "网络配置实验"),
    ("zhengsan",  "监听音箱",     "BORROWED",      7,    "音频算法测试"),
    ("wangyi",    "LoRa网关",     "APPROVED",      5,    "物联网组网实验"),
    ("wangyi",    "温湿度传感器", "BORROWED",      7,    "环境数据采集"),
    ("fengyi",    "直流稳压电源", "RETURNED",      3,    "电路供电测试"),
    ("fengyi",    "电子负载",     "BORROWED",      5,    "电源性能测试"),
    ("chenyi",    "单片机实验箱", "BORROWED",     14,    "课程设计项目"),
    ("chenyi",    "模拟电路实验箱","RETURN_PENDING",7,   "模电实验"),
    ("zhaoliu",   "UPS不间断电源","PENDING",       2,    "实验室临时供电"),
    ("sunqi",     "音频接口",     "BORROWED",      5,    "录音与信号采集"),
    ("zhouba",    "激光测距仪",   "RETURNED",      4,    "距离检测实验"),
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