"""配置文件：所有可变参数从环境变量读取，实现配置与代码分离。"""
import os
from dotenv import load_dotenv

load_dotenv()


def _bool(key, default="false"):
    return os.getenv(key, default).lower() in ("1", "true", "yes")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # ---- 数据库 ----
    DB_USER = os.getenv("DB_USER", "lab_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "lab_pass123")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "lab_device_db")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Redis ----
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))

    # ---- JWT ----
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "2"))

    # ---- 加密后端开关：gmssl(主) / openssl(兜底) ----
    CRYPTO_BACKEND = os.getenv("CRYPTO_BACKEND", "gmssl")
    SM4_KEY = os.getenv("SM4_KEY", "0123456789abcdeffedcba9876543210")

    # ---- 业务规则 ----
    MAX_BORROW_COUNT = int(os.getenv("MAX_BORROW_COUNT", "3"))
    MAX_BORROW_DAYS = int(os.getenv("MAX_BORROW_DAYS", "30"))
    LOGIN_FAIL_LIMIT = int(os.getenv("LOGIN_FAIL_LIMIT", "5"))
    LOGIN_LOCK_MINUTES = int(os.getenv("LOGIN_LOCK_MINUTES", "10"))
    CAPTCHA_EXPIRE_SECONDS = int(os.getenv("CAPTCHA_EXPIRE_SECONDS", "60"))

    # ---- 初始超管 ----
    INIT_SUPERADMIN_USERNAME = os.getenv("INIT_SUPERADMIN_USERNAME", "superadmin")
    INIT_SUPERADMIN_PASSWORD = os.getenv("INIT_SUPERADMIN_PASSWORD", "Admin@123456")
