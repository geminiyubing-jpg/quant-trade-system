#!/bin/bash

# ============================================
# VS Code Claude Code 上下文修复脚本
# 专门针对 VS Code 集成场景
# ============================================

echo "🔧 VS Code Claude Code 上下文修复"
echo "===================================="
date
echo ""

# 项目正确目录
PROJECT_DIR="/Users/yubing/quant-trade-system"

# 1. 检查当前状态
echo "📊 当前 Claude Code 进程状态..."
cd "$PROJECT_DIR" || { echo "❌ 无法进入项目目录"; exit 1; }
./scripts/check_claude_status.sh

echo ""
echo "🔍 VS Code 进程分析..."
echo "------------------------------------"

# 查找 VS Code 进程
VSCODE_PIDS=$(pgrep -f "Visual Studio Code" 2>/dev/null || pgrep -f "Code\.app" 2>/dev/null || pgrep -f "VSCodium" 2>/dev/null)

if [ -z "$VSCODE_PIDS" ]; then
    echo "⚠️  未找到正在运行的 VS Code 进程"
    echo ""
    echo "💡 建议: 使用以下命令启动 VS Code:"
    echo "  open -a \"Visual Studio Code\" \"$PROJECT_DIR\""
    echo "  或者"
    echo "  cd \"$PROJECT_DIR\" && open -a \"Visual Studio Code\" ."
else
    echo "✅ 找到 VS Code 进程:"
    for pid in $VSCODE_PIDS; do
        PROCESS_NAME=$(ps -p $pid -o command= | head -1)
        CWD=$(lsof -p $pid 2>/dev/null | grep "cwd" | awk '{print $9}')
        echo "  PID $pid: $PROCESS_NAME"
        echo "      工作目录: $CWD"
        
        if [ "$CWD" = "$PROJECT_DIR" ]; then
            echo "      ✅ 正确的工作目录"
        elif [ "$CWD" = "/Users/yubing" ]; then
            echo "      ⚠️  警告: 在用户主目录，不是项目目录"
        else
            echo "      ⚠️  当前目录: $CWD"
        fi
    done
    echo ""
fi

# 2. 解决方案
echo "🚀 解决方案 - VS Code 集成场景"
echo "===================================="

echo ""
echo "📋 选项1: 重新启动 VS Code 到正确目录"
echo "------------------------------------"
echo "执行以下任一命令:"
echo "  1. 使用 open 命令:"
echo "     open -a \"Visual Studio Code\" \"$PROJECT_DIR\""
echo ""
echo "  2. 或先切换目录:"
echo "     cd \"$PROJECT_DIR\" && open -a \"Visual Studio Code\" ."
echo ""
echo "  3. 或关闭当前 VS Code，然后在终端执行:"
echo "     cd \"$PROJECT_DIR\""
echo "     open ."
echo "     # 然后选择用 VS Code 打开"
echo ""

echo "📋 选项2: 在现有 VS Code 中调整工作目录"
echo "------------------------------------"
echo "如果 VS Code 已经打开:"
echo "  1. 菜单栏选择: File → Close Folder (关闭当前工作区)"
echo "  2. 菜单栏选择: File → Open Folder..."
echo "  3. 导航到: $PROJECT_DIR"
echo "  4. 选择 \"Open\""
echo "  5. VS Code 会重启，现在工作目录就正确了"
echo ""

echo "📋 选项3: 创建 VS Code 工作区文件（推荐）"
echo "------------------------------------"
echo "创建工作区文件以确保 VS Code 始终打开正确目录:"
echo ""
echo "  1. 在终端执行:"
echo "     cd \"$PROJECT_DIR\""
echo "     cat > quant-trade.code-workspace << 'EOF'"
echo "     {"
echo "       \"folders\": ["
echo "         {"
echo "           \"path\": \".\""
echo "         }"
echo "       ],"
echo "       \"settings\": {}"
echo "     }"
echo "     EOF"
echo ""
echo "  2. 现在用以下命令启动 VS Code:"
echo "     open -a \"Visual Studio Code\" \"$PROJECT_DIR/quant-trade.code-workspace\""
echo ""

echo "📋 选项4: 使用自动修复脚本"
echo "------------------------------------"
echo "我们已经创建了自动修复脚本:"
echo ""
echo "  $PROJECT_DIR/scripts/start_quant_trade_claude.sh"
echo "    ➔ 用于命令行启动 Claude Code（非 VS Code 集成）"
echo ""
echo "  $PROJECT_DIR/scripts/launch_vscode_to_project.sh"
echo "    ➔ 专门用于启动 VS Code 到项目目录（即将创建）"
echo ""

echo "📋 选项5: 验证修复"
echo "------------------------------------"
echo "修复后，验证步骤:"
echo "  1. 在 VS Code 终端中运行:"
echo "     pwd"
echo "     # 应该显示: $PROJECT_DIR"
echo ""
echo "  2. 运行状态检查:"
echo "     cd \"$PROJECT_DIR\" && ./scripts/check_claude_status.sh"
echo ""
echo "  3. 检查 Claude Code 能否访问项目文件:"
echo "     ls -la backend/"
echo "     ls -la frontend/"
echo "     ls -la CLAUDE.md"
echo ""

# 3. 创建快捷脚本
echo ""
echo "🛠️ 创建专用 VS Code 启动脚本..."
LAUNCH_SCRIPT="$PROJECT_DIR/scripts/launch_vscode_to_project.sh"
cat > "$LAUNCH_SCRIPT" << 'EOF'
#!/bin/bash

# VS Code 项目启动脚本
# 确保每次都在正确目录启动 VS Code

PROJECT_DIR="/Users/yubing/quant-trade-system"

echo "🚀 启动 VS Code 到 Quant Trade System 项目..."
echo "项目目录: $PROJECT_DIR"

# 检查目录是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 错误: 项目目录不存在: $PROJECT_DIR"
    exit 1
fi

# 切换到项目目录
cd "$PROJECT_DIR"

echo "✅ 当前目录: $(pwd)"
echo "📁 项目内容:"
ls -la | head -10
echo ""

echo "🔧 检查项目文件..."
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

echo ""
echo "🤖 启动 VS Code..."
echo "  打开项目: $PROJECT_DIR"

# 尝试不同的方法启动 VS Code
if [ -d "/Applications/Visual Studio Code.app" ]; then
    open -a "Visual Studio Code" "$PROJECT_DIR"
elif [ -d "/Applications/VSCodium.app" ]; then
    open -a "VSCodium" "$PROJECT_DIR"
elif command -v code &> /dev/null; then
    code "$PROJECT_DIR"
else
    echo "⚠️  未找到 VS Code 或 VSCodium"
    echo "  请手动打开项目目录"
    open "$PROJECT_DIR"
fi

echo ""
echo "🎯 重要提示:"
echo "  1. 检查 VS Code 左下角或标题栏，应该显示 'quant-trade-system'"
echo "  2. 在 VS Code 终端中运行 'pwd' 确认工作目录"
echo "  3. Claude Code 现在应该能够正确访问项目文件"
echo ""
echo "✅ 启动命令已执行"
EOF

chmod +x "$LAUNCH_SCRIPT"
echo "✅ 创建脚本: $LAUNCH_SCRIPT"

echo ""
echo "🧪 使用示例:"
echo "  $LAUNCH_SCRIPT"
echo "  # 或"
echo "  cd \"$PROJECT_DIR\" && ./scripts/launch_vscode_to_project.sh"

# 4. 总结
echo ""
echo "📋 总结"
echo "===================================="
echo "✅ 已创建的脚本:"
echo "  1. check_claude_status.sh          # 检查状态"
echo "  2. start_quant_trade_claude.sh     # 命令行启动 Claude Code"
echo "  3. launch_vscode_to_project.sh     # 启动 VS Code（刚创建）"
echo "  4. setup_claude_env.sh             # 环境设置"
echo ""
echo "🎯 核心问题:"
echo "  VS Code 的工作目录必须设置为: $PROJECT_DIR"
echo "  Claude Code 扩展继承 VS Code 的工作目录"
echo ""
echo "🚦 下一步:"
echo "  执行: ./scripts/launch_vscode_to_project.sh"
echo "  或手动用 VS Code 打开: $PROJECT_DIR"
echo ""
echo "📞 如果问题持续:"
echo "  1. 关闭所有 VS Code 窗口"
echo "  2. 运行启动脚本"
echo "  3. 检查 Claude Code 是否能看到项目文件"
echo ""
echo "🔍 验证成功:"
echo "  ✅ ./scripts/check_claude_status.sh 显示所有进程在正确目录"
echo "  ✅ VS Code 终端中 'pwd' 显示项目目录"
echo "  ✅ Claude Code 可以访问后端/前端文件"

echo ""
echo "✅ VS Code Claude Code 上下文修复指南完成"
date