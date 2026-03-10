#!/bin/bash

# ============================================================================
# Quant-Trade System 数据库备份脚本
# 版本: v1.0.0
# 创建日期: 2026-03-11
# ============================================================================

set -e

# 配置变量
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-quant_trio}"
DB_USER="${DB_USER:-quant_trio}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/quant-trade}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)

# 备份文件名
BACKUP_FILE="${BACKUP_DIR}/quant_trade_${TIMESTAMP}.sql.gz"
LATEST_LINK="${BACKUP_DIR}/latest.sql.gz"

echo "=========================================="
echo "Quant-Trade System 数据库备份"
echo "=========================================="
echo "时间: $(date)"
echo "数据库: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo "备份目录: ${BACKUP_DIR}"
echo ""

# 执行备份
echo "正在备份数据库..."
PGPASSWORD="${DB_PASSWORD:-quant_trio_pass}" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-acl \
    | gzip > "$BACKUP_FILE"

# 创建最新备份的符号链接
ln -sf "$BACKUP_FILE" "$LATEST_LINK"

# 计算备份大小
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "备份完成: $BACKUP_FILE"
echo "备份大小: $BACKUP_SIZE"

# 清理旧备份
echo ""
echo "清理 ${RETENTION_DAYS} 天前的旧备份..."
find "$BACKUP_DIR" -name "quant_trade_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
echo "清理完成"

# 备份验证
echo ""
echo "验证备份完整性..."
if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo "✅ 备份文件完整性验证通过"
else
    echo "❌ 备份文件完整性验证失败"
    exit 1
fi

# 发送通知（可选）
if [ -n "$NOTIFICATION_WEBHOOK" ]; then
    curl -s -X POST "$NOTIFICATION_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"数据库备份完成: ${BACKUP_FILE} (${BACKUP_SIZE})\"}" \
        > /dev/null 2>&1 || true
fi

echo ""
echo "=========================================="
echo "备份任务完成"
echo "=========================================="

# 输出备份统计
echo ""
echo "备份统计:"
echo "  - 备份文件: $BACKUP_FILE"
echo "  - 备份大小: $BACKUP_SIZE"
echo "  - 保留天数: $RETENTION_DAYS"
echo "  - 当前备份数: $(ls -1 ${BACKUP_DIR}/quant_trade_*.sql.gz 2>/dev/null | wc -l)"
