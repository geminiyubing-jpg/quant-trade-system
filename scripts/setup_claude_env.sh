#!/bin/bash

# ============================================
# Quant Trade System Claude 环境配置脚本
# 创建此脚本是为了确保 Claude Code 在正确的项目上下文中运行
# ============================================

echo "🔧 设置 Quant Trade System Claude 环境"
echo "======================================"

# 项目根目录
PROJECT_DIR="/Users/yubing/quant-trade-system"

# 1. 检查当前 Claude Code 进程状态
echo "📊 分析当前 Claude Code 状态..."
PROCESSES=$(ps aux | grep -i "claude --output-format" | grep -v grep)
PROCESS_COUNT=$(echo "$PROCESSES" | wc -l | tr -d ' ')
CWD_LIST=$(for pid in $(echo "$PROCESSES" | awk '{print $2}'); do lsof -p $pid 2>/dev/null | grep cwd | awk '{print $9 " (PID " pid ")"}'; done)

echo "  当前运行 Claude Code 进程数: $PROCESS_COUNT"
if [ "$PROCESS_COUNT" -gt 0 ]; then
    echo "  当前工作目录:"
    echo "$CWD_LIST" | while read line; do
        echo "    $line"
    done
    
    # 检查是否有进程在正确目录
    IN_CORRECT_DIR=$(echo "$CWD_LIST" | grep -c "$PROJECT_DIR")
    if [ "$IN_CORRECT_DIR" -eq 0 ]; then
        echo "  ⚠️  警告: 无进程在正确的项目目录中运行"
    else
        echo "  ✅ 有进程在正确目录: $PROJECT_DIR"
    fi
fi

# 2. 创建设置脚本
echo ""
echo "📝 创建启动脚本..."
SCRIPT_PATH="$PROJECT_DIR/scripts/start_quant_trade_claude.sh"
if [ -f "$SCRIPT_PATH" ]; then
    echo "  ✅ 启动脚本已存在: $SCRIPT_PATH"
    echo "  使用: $SCRIPT_PATH [Claude Code 参数]"
else
    echo "  ❌ 启动脚本不存在，请先运行 start_quant_trade_claude.sh 创建脚本"
fi

# 3. 创建快捷别名（可选）
echo ""
echo "💡 建议设置终端别名:"
echo "  添加到 ~/.zshrc 或 ~/.bashrc:"
echo "  alias qclaude='cd $PROJECT_DIR && ./scripts/start_quant_trade_claude.sh'"
echo ""
echo "  或使用完整路径:"
echo "  alias qclaude='$PROJECT_DIR/scripts/start_quant_trade_claude.sh'"

# 4. 检查项目状态
echo ""
echo "📁 检查项目状态..."
cd "$PROJECT_DIR" || { echo "❌ 无法进入项目目录"; exit 1; }
echo "  项目目录: $(pwd)"
echo "  文件数量: $(find . -type f | grep -v "\.git" | wc -l)"
echo "  后端文件: $(find backend -type f 2>/dev/null | wc -l)"
echo "  前端文件: $(find frontend -type f 2>/dev/null | wc -l)"

# 5. 建议的后续步骤
echo ""
echo "🚀 建议的后续步骤:"
echo "  1. 启动新的 Claude Code: ./scripts/start_quant_trade_claude.sh"
echo "  2. 恢复之前的会话: ./scripts/start_quant_trade_claude.sh --resume SESSION_ID"
echo "  3. 停止错误进程（如果需要）: kill [PID列表]"
echo "  4. 添加别名到配置文件"

echo ""
echo "📋 重要提醒:"
echo "  所有量化交易开发都应该在 $PROJECT_DIR 中执行"
echo "  Claude Code 需要正确的项目上下文才能访问项目文件"

echo ""
echo "✅ 环境配置检查完成"
date
