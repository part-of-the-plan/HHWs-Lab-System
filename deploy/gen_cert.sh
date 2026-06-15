#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 生成自签名 HTTPS 证书（课设演示用，浏览器会提示"不安全"属正常）
#
# 用法（在云服务器上）：
#   sudo bash deploy/gen_cert.sh                # 默认 CN=服务器公网IP
#   sudo bash deploy/gen_cert.sh lab.example.com   # 指定域名
#
# 生成结果：
#   /etc/nginx/ssl/lab.crt  证书（Nginx ssl_certificate）
#   /etc/nginx/ssl/lab.key  私钥（Nginx ssl_certificate_key）
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

# 证书绑定的域名/IP：传参优先，否则自动取公网 IP，再兜底 localhost
CN="${1:-}"
if [ -z "$CN" ]; then
    CN="$(curl -s --max-time 5 ifconfig.me || echo localhost)"
fi

SSL_DIR="/etc/nginx/ssl"
DAYS=3650   # 自签有效期 10 年，省得答辩期间过期

echo ">> 证书绑定 CN = ${CN}"
mkdir -p "$SSL_DIR"

# 生成私钥 + 自签证书（RSA 2048，SAN 同时写入，兼容新版浏览器）
openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "${SSL_DIR}/lab.key" \
    -out    "${SSL_DIR}/lab.crt" \
    -days   "${DAYS}" \
    -subj   "/C=CN/ST=Lab/L=Lab/O=LabDeviceMgmt/CN=${CN}" \
    -addext "subjectAltName=DNS:${CN},IP:${CN}" 2>/dev/null \
  || openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "${SSL_DIR}/lab.key" \
    -out    "${SSL_DIR}/lab.crt" \
    -days   "${DAYS}" \
    -subj   "/C=CN/ST=Lab/L=Lab/O=LabDeviceMgmt/CN=${CN}"
    # 兜底分支：CN 是域名而非 IP 时，IP:${CN} 会报错，去掉 addext 重来

# 私钥权限收紧，只有 root 可读
chmod 600 "${SSL_DIR}/lab.key"
chmod 644 "${SSL_DIR}/lab.crt"

echo ">> 证书已生成："
echo "   ${SSL_DIR}/lab.crt"
echo "   ${SSL_DIR}/lab.key"
echo ">> 接下来： sudo nginx -t && sudo systemctl reload nginx"
