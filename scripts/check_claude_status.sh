#!/bin/bash

# ============================================
# Claude Code 状态检查脚本
# 检查当前所有 Claude Code 进程的工作目录
# ============================================

echo "🔍 Claude Code 进程状态检查"
echo "============================="
date
echo ""

# 项目正确目录
CORRECT_DIR="/Users/yubing/quant-trade-system"

# 查找所有 Claude Code 进程
echo "📊 搜索 Claude Code 进程..."
CLAUDE_PROCS=$(ps aux | grep "claude --output-format" | grep -v grep)


if [ -z "$CLAUDE_PROCS" ]; then
    echo "⚠️  没有找到正在运行的 Claude Code 进程"
    echo ""
    echo "💡 建议:"
    echo "  在正确目录启动: cd $CORRECT_DIR && ./scripts/start_quant_trade_claude.sh"
    exit 0
fi

# 统计进程数量
PROC_COUNT=$(echo "$CLAUDE_PROCS" | wc -l | tr -d ' ')
echo "找到 $PROC_COUNT 个 Claude Code 进程"
echo ""

# 显示每个进程的详细信息
echo "PID      | 运行时间 | 工作目录 | 状态"
echo "---------|----------|----------|--------"

# 计数器
CORRECT_COUNT=0
WRONG_COUNT=0

echo "$CLAUDE_PROCS" | while read line; do
    PID=$(echo $line | awk '{print $2}')
    ETIME=$(ps -o etime= -p $PID 2>/dev/null | tr -d ' ')
    CWD=$(lsof -p $PID 2>/dev/null | grep "cwd" | awk '{print $9}')
    
    # 检查工作目录是否正确
    if [ "$CWD" = "$CORRECT_DIR" ]; then
        STATUS="✅ 正确"
        COLOR="\033[32m"
        CORRECT_COUNT=$((CORRECT_COUNT + 1))
    elif [ -z "$CWD" ]; then
        STATUS="❓ 未知"
        COLOR="\033[33m"
    else
        STATUS="❌ 错误"
        COLOR="\033[31m"
        WRONG_COUNT=$((WRONG_COUNT + 1))
    fi
    
    # 显示进程信息
    echo -e "${PID:0:8} | ${ETIME:0:8} | ${CWD:-未知} | ${COLOR}${STATUS}\033[0m"
done

echo ""
echo "📈 统计结果:"
echo "  ✅ 正确目录: $CORRECT_COUNT 个进程"
echo "  ❌ 错误目录: $WRONG_COUNT 个进程"
echo "  ❓ 未知状态: $((PROC_COUNT - CORRECT_COUNT - WRONG_COUNT)) 个进程"
echo ""

# 显示具体问题
if [ $WRONG_COUNT -gt 0 ]; then
    echo "⚠️  发现问题:"
    echo "  - 有 $WRONG_COUNT 个进程不在正确的项目目录中运行"
    echo "  - 正确目录应该是: $CORRECT_DIR"
    echo ""
    echo "🔧 解决方案:"
    echo "  1. 停止错误进程: kill [PID列表]"
    echo "  2. 在正确目录启动: cd $CORRECT_DIR && ./scripts/start_quant_trade_claude.sh"
    echo "  3. 使用我们的启动脚本确保正确目录"
fi

# 显示正确的启动命令
echo ""
echo "🚀 正确的启动方式:"
echo "  $CORRECT_DIR/scripts/start_quant_trade_claude.sh [参数]"
echo ""
echo "📝 检查项目目录状态:"
cd "$CORRECT_DIR" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ 项目目录可访问: $(pwd)"
    echo "  📁 最近修改的文件:"
    find . -type f -mtime -7 -not -path "./.git/*" | head -5 | while read file; do
        echo "    - $file"
    done
else
    echo "  ❌ 无法访问项目目录: $CORRECT_DIR"
fi

echo ""
echo "✅ 检查完成"