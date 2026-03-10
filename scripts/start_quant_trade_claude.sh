#!/bin/bash

# ============================================
# Quant Trade System - Claude Code 启动脚本
# 版本: 1.0.0
# 作者: OpenClaw Assistant
# 日期: 2026-03-09
# ============================================

# 项目根目录（必须与项目实际位置匹配）
PROJECT_DIR="/Users/yubing/quant-trade-system"

# Claude Code 可执行文件路径
CLAUDE_EXEC="/Users/yubing/.vscode/extensions/anthropic.claude-code-2.1.71-darwin-x64/resources/native-binary/claude"

# ============================================
# 函数：显示使用帮助
# ============================================
show_help() {
    echo "🗂️  Quant Trade System Claude Code 启动脚本"
    echo "=========================================="
    echo "用法: $0 [Claude Code 参数]"
    echo ""
    echo "示例:"
    echo "  $0 --help                   # 显示 Claude Code 帮助"
    echo "  $0                          # 启动默认会话"
    echo "  $0 --resume SESSION_ID      # 恢复指定会话"
    echo ""
    echo "项目目录: $PROJECT_DIR"
    echo "Claude 路径: $CLAUDE_EXEC"
    echo ""
    echo "📢 重要: 所有 Claude Code 操作将在项目目录中执行！"
}

# ============================================
# 函数：检查依赖项
# ============================================
check_dependencies() {
    # 检查项目目录是否存在
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "❌ 错误: 项目目录不存在: $PROJECT_DIR"
        echo "请确保量化交易项目目录正确设置"
        exit 1
    fi
    
    # 检查 Claude Code 可执行文件
    if [ ! -x "$CLAUDE_EXEC" ]; then
        echo "❌ 错误: Claude Code 可执行文件不存在或不可执行: $CLAUDE_EXEC"
        echo "请检查 VSCode 扩展安装情况"
        exit 1
    fi
    
    echo "✅ 依赖项检查通过"
    echo "  项目目录: $PROJECT_DIR"
    echo "  Claude 可执行文件: $CLAUDE_EXEC"
}

# ============================================
# 函数：显示当前进程信息
# ============================================
show_current_processes() {
    echo "📊 当前 Claude Code 进程:"
    echo "-------------------------"
    # 统计进程数量
    PROCESS_COUNT=$(ps aux | grep -i "claude --output-format" | grep -v grep | wc -l | tr -d ' ')
    if [ "$PROCESS_COUNT" -gt 0 ]; then
        echo "  运行中: $PROCESS_COUNT 个进程"
        ps aux | grep -i "claude --output-format" | grep -v grep | awk '{print "   PID " $2 " (" $11 ")"}'
    else
        echo "  无运行中的 Claude Code 进程"
    fi
    echo ""
}

# ============================================
# 主程序
# ============================================

# 显示欢迎信息
echo "🚀 启动 Quant Trade System Claude Code"
echo "======================================"
date

# 检查帮助请求
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# 显示当前进程状态
show_current_processes

# 检查依赖项
check_dependencies

# 切换到项目目录
echo "📂 切换到项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR" || {
    echo "❌ 错误: 无法切换到项目目录"
    exit 1
}

echo "✅ 当前工作目录: $(pwd)"
echo "📁 项目内容:"
ls -la | head -10

# 检查项目文件
echo ""
echo "🔍 检查项目关键文件:"
if [ -f "CLAUDE.md" ]; then
    echo "  ✅ CLAUDE.md 存在"
else
    echo "  ⚠️  CLAUDE.md 不存在"
fi

if [ -f "README.md" ]; then
    echo "  ✅ README.md 存在"
else
    echo "  ⚠️  README.md 不存在"
fi

# 构建 Claude Code 命令
echo ""
echo "🤖 启动 Claude Code..."
echo "  命令: $CLAUDE_EXEC $*"

# 执行 Claude Code
echo "======================================"
exec "$CLAUDE_EXEC" "$@"

# 注意: exec 会替换当前进程，所以这之后的代码不会执行
# 如果 exec 失败，才会执行下面的代码
echo "❌ 错误: Claude Code 启动失败"
exit 127