#!/bin/bash

# ============================================================================
# Quant-Trade System 数据库恢复脚本
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

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Quant-Trade System 数据库恢复"
echo "=========================================="

# 检查参数
if [ -z "$1" ]; then
    echo -e "${YELLOW}用法: $0 <备份文件|latest>${NC}"
    echo ""
    echo "可用的备份文件:"
    ls -lht "${BACKUP_DIR}"/quant_trade_*.sql.gz 2>/dev/null | head -10 || echo "  无备份文件"
    echo ""
    echo "示例:"
    echo "  $0 latest                    # 恢复最新备份"
    echo "  $0 quant_trade_20260311.sql.gz  # 恢复指定备份"
    exit 1
fi

# 确定备份文件
if [ "$1" == "latest" ]; then
    BACKUP_FILE="${BACKUP_DIR}/latest.sql.gz"
    if [ ! -L "$BACKUP_FILE" ]; then
        echo -e "${RED}错误: 找不到最新备份${NC}"
        exit 1
    fi
    BACKUP_FILE=$(readlink "$BACKUP_FILE")
else
    BACKUP_FILE="$1"
    if [ ! -f "$BACKUP_FILE" ]; then
        BACKUP_FILE="${BACKUP_DIR}/$1"
    fi
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}错误: 备份文件不存在: $BACKUP_FILE${NC}"
    exit 1
fi

echo "备份文件: $BACKUP_FILE"
echo "目标数据库: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo ""

# 警告确认
echo -e "${RED}⚠️  警告: 此操作将覆盖当前数据库的所有数据！${NC}"
echo -e "${RED}⚠️  建议先备份当前数据库！${NC}"
echo ""
read -p "确认要恢复数据库吗？(输入 YES 继续): " confirm

if [ "$confirm" != "YES" ]; then
    echo "操作已取消"
    exit 0
fi

echo ""
echo "开始恢复..."

# 创建恢复前的备份
PRE_RESTORE_BACKUP="${BACKUP_DIR}/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
echo "创建恢复前备份: $PRE_RESTORE_BACKUP"
PGPASSWORD="${DB_PASSWORD:-quant_trio_pass}" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-acl \
    | gzip > "$PRE_RESTORE_BACKUP" 2>/dev/null || true

# 恢复数据库
echo "正在恢复数据库..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="${DB_PASSWORD:-quant_trio_pass}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -v ON_ERROR_STOP=1 \
    > /dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 数据库恢复成功${NC}"
    echo "恢复前备份保存在: $PRE_RESTORE_BACKUP"
else
    echo -e "${RED}❌ 数据库恢复失败${NC}"
    echo "可以使用以下命令回滚:"
    echo "  $0 $PRE_RESTORE_BACKUP"
    exit 1
fi

echo ""
echo "=========================================="
echo "恢复任务完成"
echo "=========================================="
