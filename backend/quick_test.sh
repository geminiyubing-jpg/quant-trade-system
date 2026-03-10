#!/bin/bash
# ==============================================
# 快速测试脚本
# ==============================================

echo "🚀 快速测试 QuantAI Ecosystem"
echo ""

# 测试 1: 健康检查
echo "1️⃣ 健康检查..."
curl -s http://localhost:8000/health | jq '.status'

# 测试 2: 登录
echo ""
echo "2️⃣ 用户登录..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user", "password": "testpass123"}' | jq -r '.access_token')
echo "Token: ${TOKEN:0:20}..."

# 测试 3: 获取用户信息
echo ""
echo "3️⃣ 获取用户信息..."
curl -s http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" | jq '.username, .email'

# 测试 4: 风控检查
echo ""
echo "4️⃣ 风险控制检查..."
curl -s "http://localhost:8000/api/v1/risk/check-order?symbol=000001.SZ&side=BUY&quantity=100&price=10.50" \
  -X POST \
  -H "Authorization: Bearer $TOKEN" | jq 'length'

echo ""
echo "✅ 快速测试完成！"
echo ""
echo "📊 完整测试: ./run_all_tests.sh"
echo "📖 API 文档: http://localhost:8000/docs"
