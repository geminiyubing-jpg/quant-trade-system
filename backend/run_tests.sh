#!/bin/bash
# ==============================================
# Quant-Trade System - 测试运行脚本
# ==============================================

set -e

echo "=============================================="
echo "QuantAI Ecosystem - 测试套件"
echo "=============================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 pytest 是否安装
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}警告: pytest 未安装${NC}"
    echo "请运行: pip3 install pytest pytest-cov"
    exit 1
fi

# 运行测试
echo -e "${GREEN}开始运行测试...${NC}"
echo ""

# 测试数据服务
echo "1️⃣  测试数据服务..."
pytest tests/test_services/test_data_service.py -v --tb=short || echo "⚠️  数据服务测试失败"
echo ""

# 测试回测服务
echo "2️⃣  测试回测服务..."
pytest tests/test_services/test_backtest_service.py -v --tb=short || echo "⚠️  回测服务测试失败"
echo ""

# 测试风控服务
echo "3️⃣  测试风控服务..."
pytest tests/test_services/test_risk_service.py -v --tb=short || echo "⚠️  风控服务测试失败"
echo ""

# 运行所有测试并生成覆盖率报告
echo "4️⃣  生成测试覆盖率报告..."
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html || echo "⚠️  覆盖率测试失败"
echo ""

echo "=============================================="
echo -e "${GREEN}✅ 测试完成！${NC}"
echo "=============================================="
echo ""
echo "📊 覆盖率报告: htmlcov/index.html"
echo ""
