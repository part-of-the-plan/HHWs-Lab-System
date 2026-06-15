#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# MySQL 数据库自动备份脚本
#
# 用法：
#   bash deploy/backup.sh                 # 手动备份一次
#   配合 crontab 每天凌晨 3 点自动备份：
#     crontab -e
#     0 3 * * * /opt/lab/project/deploy/backup.sh >> /var/log/lab-backup.log 2>&1
#
# 凭据从 backend/.env 读取，不硬编码。
# 备份文件 gzip 压缩，保留最近 7 天，自动清理旧文件。
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

# 脚本所在目录 -> 项目根 -> backend/.env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../backend/.env"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/lab-db}"
KEEP_DAYS=7

if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] 找不到 $ENV_FILE，无法读取数据库凭据" >&2
    exit 1
fi

# 从 .env 提取数据库配置（只取等号右值，忽略注释/行内注释）
get_env() {
    grep -E "^${1}=" "$ENV_FILE" | head -1 | cut -d= -f2- | sed 's/[[:space:]]*#.*$//' | xargs
}
DB_HOST="$(get_env DB_HOST)"
DB_PORT="$(get_env DB_PORT)"
DB_NAME="$(get_env DB_NAME)"
DB_USER="$(get_env DB_USER)"
DB_PASSWORD="$(get_env DB_PASSWORD)"

mkdir -p "$BACKUP_DIR"
# 时间戳由 date 生成（服务器系统时间，可信）
TS="$(date +%Y%m%d_%H%M%S)"
OUT="${BACKUP_DIR}/${DB_NAME}_${TS}.sql.gz"

echo ">> 备份 ${DB_NAME} -> ${OUT}"

# 用 MYSQL_PWD 传密码，避免密码出现在 ps 进程列表里
MYSQL_PWD="$DB_PASSWORD" mysqldump \
    -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" \
    --single-transaction --quick --routines --default-character-set=utf8mb4 \
    "$DB_NAME" | gzip > "$OUT"

echo ">> 备份完成，大小：$(du -h "$OUT" | cut -f1)"

# 清理超过 KEEP_DAYS 天的旧备份
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -type f -mtime "+${KEEP_DAYS}" -delete
echo ">> 已清理 ${KEEP_DAYS} 天前的旧备份"
