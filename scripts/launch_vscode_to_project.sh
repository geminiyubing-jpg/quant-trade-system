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
