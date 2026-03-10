# 🤖 Quant Trade System - Claude Code 配置指南

> **最后更新**: 2026-03-09  
> **作者**: OpenClaw Assistant  
> **目的**: 确保 Claude Code 在正确的项目目录中运行

---

## 🚨 问题诊断

### 当前问题
检测到 **所有 Claude Code 进程都在错误的目录中运行**：
* ❌ **当前工作目录**: `/Users/yubing` (用户主目录)
* ✅ **正确工作目录**: `/Users/yubing/quant-trade-system/`

### 后果
* Claude Code 无法正确访问项目文件
* 相对路径引用会出错
* VS Code 集成可能无法正常工作
* 自动补全和代码理解可能基于错误的上下文

---

## 🛠️ 解决方案

### 1. 使用专用启动脚本

我们已经创建了专用启动脚本，确保 Claude Code 在正确的目录中启动：

```bash
# 在项目目录中运行
cd /Users/yubing/quant-trade-system/

# 使用专用脚本启动 Claude Code
./scripts/start_quant_trade_claude.sh

# 或使用完整路径
/Users/yubing/quant-trade-system/scripts/start_quant_trade_claude.sh
```

**脚本功能**:
- ✅ 自动切换到正确的项目目录
- ✅ 验证依赖项（项目目录、Claude 可执行文件）
- ✅ 显示当前进程状态
- ✅ 传递所有参数给 Claude Code
- ✅ 错误处理和诊断信息

### 2. 添加终端别名（推荐）

将以下别名添加到 `~/.zshrc` 或 `~/.bashrc`：

```bash
# Quant Trade System Claude Code 别名
alias qclaude='/Users/yubing/quant-trade-system/scripts/start_quant_trade_claude.sh'
```

然后重新加载配置：
```bash
source ~/.zshrc  # 或 source ~/.bashrc
```

现在可以使用简化的命令：
```bash
qclaude                        # 启动新会话
qclaude --resume SESSION_ID    # 恢复特定会话
qclaude --help                 # 显示帮助
```

### 3. 检查当前状态

使用诊断脚本检查 Claude Code 进程状态：

```bash
./scripts/check_claude_status.sh
```

**输出示例**:
```
🔍 Claude Code 进程状态检查
=============================
📊 搜索 Claude Code 进程...
找到 10 个 Claude Code 进程

PID      | 运行时间 | 工作目录 | 状态
---------|----------|----------|--------
48279    | 02:15:32 | /Users/yubing | ❌ 错误
34487    | 03:45:21 | /Users/yubing | ❌ 错误
...

📈 统计结果:
  ✅ 正确目录: 0 个进程
  ❌ 错误目录: 10 个进程
  ❓ 未知状态: 0 个进程
```

### 4. 修复现有进程问题

如果需要修复当前运行的进程：

```bash
# 查看所有 Claude Code 进程
ps aux | grep "claude --output-format" | grep -v grep

# 停止错误进程（谨慎操作）
kill [PID列表]

# 在正确目录重新启动
cd /Users/yubing/quant-trade-system/
./scripts/start_quant_trade_claude.sh
```

---

## 📋 可用脚本

| 脚本文件 | 用途 | 使用示例 |
|---------|------|----------|
| `start_quant_trade_claude.sh` | **主启动脚本** | `./scripts/start_quant_trade_claude.sh --resume abc123` |
| `check_claude_status.sh` | **状态诊断** | `./scripts/check_claude_status.sh` |
| `setup_claude_env.sh` | **环境配置** | `./scripts/setup_claude_env.sh` |

---

## 🔍 技术细节

### Claude Code 路径
- **可执行文件**: `/Users/yubing/.vscode/extensions/anthropic.claude-code-2.1.71-darwin-x64/resources/native-binary/claude`
- **项目目录**: `/Users/yubing/quant-trade-system/`

### 典型参数
默认参数（从当前进程获取）：
```
--output-format stream-json
--verbose
--input-format stream-json  
--max-thinking-tokens 31999
--model default
--permission-prompt-tool stdio
--setting-sources user,project,local
--permission-mode default
--include-partial-messages
--debug
--debug-to-stderr
--enable-auth-status
--no-chrome
```

---

## ⚠️ 注意事项

1. **VS Code 集成**: 如果你使用 VS Code，确保工作区打开的是 `/Users/yubing/quant-trade-system/` 文件夹
2. **会话恢复**: 恢复会话时，Claude Code 会基于当前工作目录查找会话数据
3. **权限**: 确保脚本有执行权限 (`chmod +x scripts/*.sh`)
4. **参数传递**: 启动脚本会传递所有参数到 Claude Code 可执行文件

---

## 🚀 快速开始

### 对于新用户
```bash
cd /Users/yubing/quant-trade-system/

# 1. 检查当前状态
./scripts/check_claude_status.sh

# 2. 设置环境（可选）
./scripts/setup_claude_env.sh

# 3. 启动 Claude Code
./scripts/start_quant_trade_claude.sh

# 4. 添加别名到配置文件
echo "alias qclaude='$(pwd)/scripts/start_quant_trade_claude.sh'" >> ~/.zshrc
source ~/.zshrc
```

### 对于现有用户（修复问题）
```bash
# 1. 停止错误进程
kill 48279 34487 33949 35679 35804 33328 35751 63882 36062 33889

# 2. 在正确目录启动
cd /Users/yubing/quant-trade-system/
./scripts/start_quant_trade_claude.sh
```

---

## ❓ 常见问题

**Q: 为什么工作目录很重要？**
A: Claude Code 需要正确的项目上下文才能：
   - 访问项目文件（`CLAUDE.md`, `README.md` 等）
   - 理解项目结构
   - 提供准确的代码补全和建议
   - 正确解析相对路径

**Q: 如何确认 Claude Code 在正确目录中运行？**
A: 运行 `./scripts/check_claude_status.sh` 或检查进程：
```bash
lsof -p [PID] | grep cwd
```

**Q: 启动脚本失败怎么办？**
A: 检查：
   1. 项目目录是否存在
   2. Claude Code 安装是否完整
   3. 脚本执行权限
   4. 错误输出信息

---

## 📞 支持

如果问题持续存在，请联系：
- **项目维护者**: QuantDev Team  
- **自动化助手**: OpenClaw Assistant
- **检查更新时间**: 2026-03-09

---

## ✅ 验证配置成功

配置成功后，你应该看到：
1. `./scripts/check_claude_status.sh` 显示所有进程在正确目录
2. Claude Code 可以正确访问项目文件
3. VS Code 集成正常工作
4. 相对路径引用正确解析

---

**🎯 记住: 所有量化交易开发都应该在 `/Users/yubing/quant-trade-system/` 目录中进行！**