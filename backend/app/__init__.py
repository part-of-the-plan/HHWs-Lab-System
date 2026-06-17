"""Flask 应用工厂。"""
from flask import Flask, request
from flask_cors import CORS

from .config import get_config
from .extensions import db, migrate, jwt, init_redis


def create_app(config_class=None):
    app = Flask(__name__)
    # 不显式传入时按 FLASK_ENV 自动选 Development / Production
    app.config.from_object(config_class or get_config())

    # ── 反向代理修正：生产经 Nginx 反代，request.remote_addr 默认是 127.0.0.1
    # 用 ProxyFix 信任 Nginx 透传的 X-Forwarded-For，审计日志才能记到真实客户端 IP。
    # 只信任 1 层代理（我们只有 Nginx 一层），避免客户端伪造 XFF 头。
    if app.config.get("IS_PRODUCTION"):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    init_redis(app)

    # 接口限流：用 Redis 做计数器，Gunicorn 多 worker 共享
    from .extensions import limiter
    app.config["RATELIMIT_STORAGE_URI"] = (
        f"redis://{app.config['REDIS_HOST']}:{app.config['REDIS_PORT']}"
    )
    limiter.init_app(app)

    # ── CORS：生产按 .env 的 CORS_ORIGINS 白名单收紧，开发放开 ──
    origins = app.config.get("CORS_ORIGINS", "")
    if app.config.get("IS_PRODUCTION") and origins:
        allow = [o.strip() for o in origins.split(",") if o.strip()]
    else:
        allow = "*"
    CORS(app, resources={r"/api/*": {"origins": allow}}, supports_credentials=True)

    # ── 导入所有模型（确保 db.Model.metadata 里有它们，Migrate 才能识别）──
    from .models import (
        User, Role, Permission, UserRole, RolePermission,
        Device, DeviceCategory, BorrowRecord, OperationLog,
    )

    # ── 注册蓝图 ──
    from .api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from .api.device import device_bp
    app.register_blueprint(device_bp, url_prefix="/api/devices")

    from .api.category import category_bp
    app.register_blueprint(category_bp, url_prefix="/api/categories")

    from .api.borrow import borrow_bp
    app.register_blueprint(borrow_bp, url_prefix="/api/borrows")

    from .api.user import user_bp
    app.register_blueprint(user_bp, url_prefix="/api/users")

    from .api.log import log_bp
    app.register_blueprint(log_bp, url_prefix="/api/logs")

    from .api.roles import roles_bp
    app.register_blueprint(roles_bp, url_prefix="/api/roles")

    from .api.stats import stats_bp
    app.register_blueprint(stats_bp, url_prefix="/api/stats")

    # ── 注册中间件 ──
    from .middlewares.auth_middleware import register_auth_middleware
    register_auth_middleware(app)

    # ── CSRF 防护：对所有写请求校验 X-CSRF-Token 头 ──
    from .utils.csrf import check_csrf

    @app.before_request
    def _csrf_check():
        result = check_csrf()
        if result is not None:
            return result

    # ── 目录遍历防护：拒绝含 ../ 等危险片段的请求 ──
    from .utils.validators import is_safe_path

    @app.before_request
    def _path_traversal_check():
        # 1. 检查 URL 路径本身
        if not is_safe_path(request.path):
            return _json_error("请求路径包含非法字符", code=400, http_status=400)

        # 2. 检查 JSON body / form / query args 里的字符串值
        sources = []
        if request.is_json:
            try:
                sources.append(request.get_json(silent=True) or {})
            except Exception:
                pass
        if request.form:
            sources.append(request.form.to_dict())
        if request.args:
            sources.append(request.args.to_dict())

        def _check(obj):
            if isinstance(obj, str):
                if not is_safe_path(obj):
                    return True
            elif isinstance(obj, dict):
                for v in obj.values():
                    if _check(v):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if _check(item):
                        return True
            return False

        for src in sources:
            if _check(src):
                return _json_error("请求数据包含非法字符", code=400, http_status=400)

        return None

    # ── 全局错误处理器：未捕获异常统一返回 JSON，而非 HTML 错误页 ──
    from .utils.response import error as _json_error

    @app.errorhandler(400)
    def _bad_request(e):
        return _json_error("请求参数有误", code=400, http_status=400)

    @app.errorhandler(401)
    def _unauthorized(e):
        return _json_error("未登录或登录已过期", code=401, http_status=401)

    @app.errorhandler(403)
    def _forbidden(e):
        return _json_error("无此操作权限", code=403, http_status=403)

    @app.errorhandler(404)
    def _not_found(e):
        return _json_error("接口不存在", code=404, http_status=404)

    @app.errorhandler(500)
    def _server_error(e):
        # 生产不暴露 traceback；开发暴露错误信息方便调试
        if app.config.get("IS_PRODUCTION"):
            return _json_error("服务器内部错误", code=500, http_status=500)
        return _json_error(f"服务器错误: {str(e)}", code=500, http_status=500)

    # ── CLI：数据库种子数据 ──
    @app.cli.command("init-db")
    def init_db_command():
        """创建所有表 + 写入种子数据（三角色+权限+超管账号）。
        用法: flask init-db
        """
        db.create_all()
        _seed_data()
        print("[init-db] 数据库初始化完成。")

    # ── 健康检查 ──
    @app.get("/api/health")
    def health():
        return {"code": 0, "message": "ok", "data": {"status": "running"}}

    # ── 安全响应头（Nginx 也会加，这里后端兜底，直连时也安全）──
    @app.after_request
    def set_security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if app.config.get("IS_PRODUCTION"):
            resp.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return resp

    return app


def _seed_data():
    """写入种子数据：三角色 + 权限 + 角色权限关联 + 超管账号。
    幂等：已有数据时跳过。
    """
    from .models import Role, Permission, RolePermission, User, UserRole
    from .utils.crypto import hash_password

    # 角色
    if Role.query.count() == 0:
        db.session.add_all([
            Role(role_code="SUPER_ADMIN", role_name="超级管理员",
                 description="系统最高权限,可管理用户与角色分配"),
            Role(role_code="LAB_ADMIN", role_name="实验室管理员",
                 description="管理设备与审批借用"),
            Role(role_code="NORMAL_USER", role_name="普通用户",
                 description="浏览设备/申请借用/查看本人记录"),
        ])
        db.session.flush()

    # 权限
    if Permission.query.count() == 0:
        perms = [
            ("device:list", "查看设备列表", "device"),
            ("device:create", "添加设备", "device"),
            ("device:update", "编辑设备", "device"),
            ("device:delete", "删除设备", "device"),
            ("category:manage", "管理设备分类", "device"),
            ("borrow:apply", "申请借用", "borrow"),
            ("borrow:approve", "审批借用", "borrow"),
            ("borrow:return", "确认归还", "borrow"),
            ("record:self", "查看本人记录", "record"),
            ("record:all", "查看全部记录", "record"),
            ("user:list", "查看用户列表", "user"),
            ("user:update", "编辑用户", "user"),
            ("user:assign", "分配角色", "user"),
            ("user:status", "启用禁用账号", "user"),
            ("log:view", "查看操作日志", "security"),
            ("security:view", "安全监控面板", "security"),
            ("stats:view", "数据统计看板", "stats"),
            ("role:manage", "角色权限管理", "system"),
        ]
        for code, name, mod in perms:
            db.session.add(Permission(perm_code=code, perm_name=name, module=mod))
        db.session.flush()

    # 角色-权限关联
    if RolePermission.query.count() == 0:
        super_admin = Role.query.filter_by(role_code="SUPER_ADMIN").first()
        lab_admin = Role.query.filter_by(role_code="LAB_ADMIN").first()
        normal_user = Role.query.filter_by(role_code="NORMAL_USER").first()

        # 超管：全部权限
        all_perms = Permission.query.all()
        for p in all_perms:
            db.session.add(RolePermission(role_id=super_admin.id, perm_id=p.id))

        # 实验室管理员
        lab_admin_codes = [
            "device:list", "device:create", "device:update", "device:delete",
            "category:manage", "borrow:approve", "borrow:return",
            "record:all", "stats:view",
        ]
        for code in lab_admin_codes:
            p = Permission.query.filter_by(perm_code=code).first()
            if p:
                db.session.add(RolePermission(role_id=lab_admin.id, perm_id=p.id))

        # 普通用户
        normal_codes = ["device:list", "borrow:apply", "record:self"]
        for code in normal_codes:
            p = Permission.query.filter_by(perm_code=code).first()
            if p:
                db.session.add(RolePermission(role_id=normal_user.id, perm_id=p.id))

    # 超管账号（仅当 users 表为空时创建，防止重复）
    from flask import current_app
    if User.query.count() == 0:
        uname = current_app.config["INIT_SUPERADMIN_USERNAME"]
        pwd = current_app.config["INIT_SUPERADMIN_PASSWORD"]
        user = User(
            username=uname,
            password_hash=hash_password(pwd),
            real_name="系统管理员",
            status=1,
        )
        db.session.add(user)
        db.session.flush()

        super_admin = Role.query.filter_by(role_code="SUPER_ADMIN").first()
        if super_admin:
            db.session.add(UserRole(user_id=user.id, role_id=super_admin.id))

    db.session.commit()
