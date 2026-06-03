"""输入校验：密码复杂度 / XSS 过滤 / 通用校验。所有校验函数返回 (is_valid, error_message)。"""
import re
import html


# ---- 密码复杂度 ----
def check_password_complexity(password: str):
    """强制口令复杂度：8位以上, 至少包含大写/小写/数字/特殊符号中的3种"""
    if len(password) < 8:
        return False, "密码长度至少8位"
    kinds = 0
    if re.search(r"[A-Z]", password):
        kinds += 1
    if re.search(r"[a-z]", password):
        kinds += 1
    if re.search(r"\d", password):
        kinds += 1
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?`~|\\]', password):
        kinds += 1
    if kinds < 3:
        return False, "密码必须包含大写字母、小写字母、数字、特殊符号中的至少三种"
    return True, ""


# ---- 通用校验 ----
def check_username(username: str):
    if not username or len(username) < 4 or len(username) > 20:
        return False, "用户名长度需在4-20位之间"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "用户名只允许字母、数字、下划线"
    return True, ""


def check_phone(phone: str):
    if not phone:
        return True, ""  # 手机号可选
    if not re.match(r"^1[3-9]\d{9}$", phone):
        return False, "手机号格式不正确"
    return True, ""


def check_email(email: str):
    if not email:
        return True, ""  # 邮箱可选
    if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
        return False, "邮箱格式不正确"
    return True, ""


def check_required(value, field_name: str):
    if not value or not str(value).strip():
        return False, f"{field_name}不能为空"
    return True, ""


# ---- XSS 防护 ----
def sanitize_input(text: str) -> str:
    """输入转义：把 HTML 特殊字符转成实体,防 XSS"""
    if not text:
        return text
    return html.escape(str(text))


def sanitize_dict(d: dict, fields: list = None) -> dict:
    """对 dict 中指定字段(或全部字符串字段)做 sanitize"""
    if d is None:
        return {}
    targets = fields if fields else d.keys()
    for k in targets:
        if k in d and isinstance(d[k], str):
            d[k] = sanitize_input(d[k])
    return d


# ---- 路径安全 ----
def is_safe_path(filename: str) -> bool:
    """检查文件名是否包含目录遍历危险片段"""
    dangerous = ["../", "..\\", "/etc/", "C:\\", "\\windows\\"]
    lower = filename.lower()
    for d in dangerous:
        if d in lower:
            return False
    return True
