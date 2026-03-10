#!/bin/bash

# ==============================================
# QuantAI Ecosystem - 开发服务器启动脚本
# ==============================================

set -e

echo "🚀 Starting QuantAI Ecosystem Development Server..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📌 Python version: $python_version"

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
fi

# 创建日志目录
mkdir -p logs

# 检查数据库连接
echo "🔍 Checking database connection..."
python3 -c "
from src.core.database import check_db_connection
if check_db_connection():
    print('✅ Database connection OK')
    exit(0)
else:
    print('❌ Database connection FAILED')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Cannot start server. Please check your database configuration."
    exit(1
fi

# 启动开发服务器
echo "🌐 Starting development server on http://0.0.0.0:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
