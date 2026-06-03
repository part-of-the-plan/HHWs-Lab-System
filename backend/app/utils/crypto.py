"""加密工具：唯一的加解密出入口。

设计目标（方案第六层）：换算法只改这一个文件。
- 主实现 gmssl：国密 SM3 哈希 + SM4 对称加密（真项目跑这套，国产化论点成立）
- 兜底 openssl：hashlib(SHA-256) + cryptography(AES)，gmssl 卡住时一键切换先跑通业务

切换方式：.env 里 CRYPTO_BACKEND=gmssl 或 openssl
"""
import os
import hashlib
from flask import current_app


# ====================================================================
# 密码哈希：加盐。存储格式统一为 "盐值$哈希值"，与后端无关
# ====================================================================
def hash_password(password: str) -> str:
    """生成 16 字节随机盐，盐+密码做哈希，返回 '盐$哈希'。"""
    salt = os.urandom(16).hex()
    digest = _hash_with_salt(password, salt)
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """用存储里的盐重新哈希，比对是否一致。"""
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    return _hash_with_salt(password, salt) == digest


def _hash_with_salt(password: str, salt: str) -> str:
    data = (salt + password).encode("utf-8")
    backend = current_app.config.get("CRYPTO_BACKEND", "gmssl")
    if backend == "gmssl":
        from gmssl import sm3, func
        return sm3.sm3_hash(func.bytes_to_list(data))      # 国密 SM3
    else:
        return hashlib.sha256(data).hexdigest()            # 兜底 SHA-256


# ====================================================================
# 敏感字段对称加解密：手机号等。返回 hex 字符串入库
# ====================================================================
def encrypt_field(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    backend = current_app.config.get("CRYPTO_BACKEND", "gmssl")
    key = current_app.config["SM4_KEY"]
    if backend == "gmssl":
        return _sm4_encrypt(plaintext, key)
    else:
        return _aes_encrypt(plaintext, key)


def decrypt_field(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    backend = current_app.config.get("CRYPTO_BACKEND", "gmssl")
    key = current_app.config["SM4_KEY"]
    try:
        if backend == "gmssl":
            return _sm4_decrypt(ciphertext, key)
        else:
            return _aes_decrypt(ciphertext, key)
    except Exception:
        return ""   # 解密失败（如换了 backend/key）不抛异常，返回空


# ---- gmssl SM4 实现 ----
def _sm4_encrypt(plaintext: str, key_hex: str) -> str:
    from gmssl.sm4 import CryptSM4, SM4_ENCRYPT
    c = CryptSM4()
    c.set_key(bytes.fromhex(key_hex), SM4_ENCRYPT)
    return c.crypt_ecb(plaintext.encode("utf-8")).hex()


def _sm4_decrypt(ciphertext_hex: str, key_hex: str) -> str:
    from gmssl.sm4 import CryptSM4, SM4_DECRYPT
    c = CryptSM4()
    c.set_key(bytes.fromhex(key_hex), SM4_DECRYPT)
    return c.crypt_ecb(bytes.fromhex(ciphertext_hex)).decode("utf-8")


# ---- 兜底 AES 实现（cryptography）----
def _aes_encrypt(plaintext: str, key_hex: str) -> str:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    key = bytes.fromhex(key_hex)
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ct = enc.update(padded) + enc.finalize()
    return (iv + ct).hex()


def _aes_decrypt(ciphertext_hex: str, key_hex: str) -> str:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    raw = bytes.fromhex(ciphertext_hex)
    key = bytes.fromhex(key_hex)
    iv, ct = raw[:16], raw[16:]
    dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = dec.update(ct) + dec.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")


# ====================================================================
# 脱敏显示：138****8000
# ====================================================================
def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]
