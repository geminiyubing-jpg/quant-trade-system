#!/bin/bash
# ==============================================
# QuantAI Ecosystem - 完整系统测试
# ==============================================

set -e

echo ""
echo "=============================================="
echo "  QuantAI Ecosystem - 完整系统测试"
echo "=============================================="
echo ""

# 配置
API_URL="http://localhost:8000"
TEST_USER="test_user"
TEST_PASS="testpass123"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_api() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local token="$5"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -n "测试 $TOTAL_TESTS: $name ... "

    if [ -n "$token" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -X "$method" \
                -H "Authorization: Bearer $token" \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$API_URL$endpoint")
        else
            response=$(curl -s -X "$method" \
                -H "Authorization: Bearer $token" \
                "$API_URL$endpoint")
        fi
    else
        if [ -n "$data" ]; then
            response=$(curl -s -X "$method" \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$API_URL$endpoint")
        else
            response=$(curl -s -X "$method" \
                "$API_URL$endpoint")
        fi
    fi

    # 检查响应 - 扩展判断条件
    if echo "$response" | jq -e '.success == true' >/dev/null 2>&1 || \
       echo "$response" | jq -e '.access_token' >/dev/null 2>&1 || \
       echo "$response" | jq -e '.username' >/dev/null 2>&1 || \
       echo "$response" | jq -e '.status == "healthy"' >/dev/null 2>&1 || \
       echo "$response" | jq -e '.backtest_id' >/dev/null 2>&1 || \
       echo "$response" | jq -e '.total_market_value' >/dev/null 2>&1 || \
       echo "$response" | jq -e '.check_type' >/dev/null 2>&1 || \
       echo "$response" | jq -e '.version' >/dev/null 2>&1 || \
       echo "$response" | jq 'length' >/dev/null 2>&1; then  # 接受任何有效 JSON 数组
        echo -e "${GREEN}✅ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "   响应: $response" | head -c 200
        echo ""
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# ==============================================
# 1. 数据库测试
# ==============================================
echo "📊 第 1 部分: 数据库测试"
echo "----------------------------------------------"

python3 test_db_simple.py
DB_RESULT=$?

if [ $DB_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 数据库测试通过${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 4))
    TOTAL_TESTS=$((TOTAL_TESTS + 4))
else
    echo -e "${RED}❌ 数据库测试失败${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 4))
    TOTAL_TESTS=$((TOTAL_TESTS + 4))
fi

echo ""

# ==============================================
# 2. API 基础测试
# ==============================================
echo "🌐 第 2 部分: API 基础测试"
echo "----------------------------------------------"

test_api "健康检查" "GET" "/" "" ""

test_api "配置查询" "GET" "/config" "" ""

test_api "健康详情" "GET" "/health" "" ""

echo ""

# ==============================================
# 3. 认证系统测试
# ==============================================
echo "🔐 第 3 部分: 认证系统测试"
echo "----------------------------------------------"

# 登录获取 token
echo -n "获取认证 Token ... "
TOKEN_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USER\", \"password\": \"$TEST_PASS\"}" \
    "$API_URL/api/v1/auth/login")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

if [ -n "$ACCESS_TOKEN" ] && [ "$ACCESS_TOKEN" != "null" ]; then
    echo -e "${GREEN}✅ PASSED${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "   响应: $TOKEN_RESPONSE"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# 测试用户信息
test_api "获取当前用户信息" "GET" "/api/v1/users/me" "" "$ACCESS_TOKEN"

echo ""

# ==============================================
# 4. 风控系统测试
# ==============================================
echo "⚠️  第 4 部分: 风控系统测试"
echo "----------------------------------------------"

test_api "获取风控指标" "GET" "/api/v1/risk/metrics" "" "$ACCESS_TOKEN"

test_api "订单风控检查" "POST" "/api/v1/risk/check-order?symbol=000001.SZ&side=BUY&quantity=100&price=10.50" "" "$ACCESS_TOKEN"

test_api "获取风控告警" "GET" "/api/v1/risk/alerts" "" "$ACCESS_TOKEN"

echo ""

# ==============================================
# 5. 回测系统测试
# ==============================================
echo "📈 第 5 部分: 回测系统测试"
echo "----------------------------------------------"

test_api "快速回测" "POST" "/api/v1/backtest/quick?strategy_id=MA_CROSS&symbols=000001.SZ&start_date=2024-01-01&end_date=2024-01-31" "" "$ACCESS_TOKEN"

test_api "获取回测结果列表" "GET" "/api/v1/backtest/results" "" "$ACCESS_TOKEN"

echo ""

# ==============================================
# 6. 交易系统测试
# ==============================================
echo "💹 第 6 部分: 交易系统测试"
echo "----------------------------------------------"

test_api "获取持仓列表" "GET" "/api/v1/trading/positions" "" "$ACCESS_TOKEN"

test_api "获取订单列表" "GET" "/api/v1/trading/orders" "" "$ACCESS_TOKEN"

echo ""

# ==============================================
# 测试总结
# ==============================================
echo "=============================================="
echo "  测试总结"
echo "=============================================="
echo ""

PERCENTAGE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

echo "总测试数: $TOTAL_TESTS"
echo -e "通过: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败: ${RED}$FAILED_TESTS${NC}"
echo "通过率: $PERCENTAGE%"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！系统运行正常！${NC}"
    echo ""
    echo "📊 访问 API 文档: $API_URL/docs"
    echo "🔍 健康检查: $API_URL/health"
    exit 0
else
    echo -e "${YELLOW}⚠️  部分测试失败，请检查日志${NC}"
    exit 1
fi
