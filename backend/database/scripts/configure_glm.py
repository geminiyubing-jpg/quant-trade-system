#!/usr/bin/env python3
"""
GLM-5 配置助手脚本

用于配置和测试 GLM-5 API 连接

用法:
    cd backend
    python database/scripts/configure_glm.py setup <your-api-key>  # 配置 API Key
    python database/scripts/configure_glm.py test                  # 测试连接
    python database/scripts/configure_glm.py status                # 查看状态
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import httpx
from dotenv import load_dotenv


def get_env_file_path() -> Path:
    """获取 .env 文件路径"""
    return Path(__file__).parent.parent.parent / ".env"


def read_env_file() -> dict:
    """读取 .env 文件"""
    env_file = get_env_file_path()
    if not env_file.exists():
        return {}

    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def write_env_file(env_vars: dict):
    """写入 .env 文件"""
    env_file = get_env_file_path()

    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# ==============================================\n")
        f.write("# QuantAI Ecosystem - 环境变量配置\n")
        f.write("# ==============================================\n\n")

        # 应用配置
        f.write("# 应用配置\n")
        f.write(f"APP_NAME={env_vars.get('APP_NAME', 'QuantAI_Ecosystem')}\n")
        f.write(f"APP_VERSION={env_vars.get('APP_VERSION', '2.0.0')}\n")
        f.write(f"APP_ENV={env_vars.get('APP_ENV', 'development')}\n")
        f.write(f"DEBUG={env_vars.get('DEBUG', 'true')}\n")
        f.write(f"LOG_LEVEL={env_vars.get('LOG_LEVEL', 'INFO')}\n\n")

        # 服务器配置
        f.write("# 服务器配置\n")
        f.write(f"HOST={env_vars.get('HOST', '0.0.0.0')}\n")
        f.write(f"PORT={env_vars.get('PORT', '8000')}\n")
        f.write(f"WORKERS={env_vars.get('WORKERS', '4')}\n\n")

        # 数据库配置
        f.write("# 数据库配置\n")
        f.write(f"POSTGRES_HOST={env_vars.get('POSTGRES_HOST', 'localhost')}\n")
        f.write(f"POSTGRES_PORT={env_vars.get('POSTGRES_PORT', '5432')}\n")
        f.write(f"POSTGRES_USER={env_vars.get('POSTGRES_USER', 'quant_trio')}\n")
        f.write(f"POSTGRES_PASSWORD={env_vars.get('POSTGRES_PASSWORD', 'quant_trio_pass')}\n")
        f.write(f"POSTGRES_DB={env_vars.get('POSTGRES_DB', 'quant_trio')}\n\n")

        # Redis 配置
        f.write("# Redis 配置\n")
        f.write(f"REDIS_HOST={env_vars.get('REDIS_HOST', 'localhost')}\n")
        f.write(f"REDIS_PORT={env_vars.get('REDIS_PORT', '6379')}\n")
        f.write(f"REDIS_PASSWORD={env_vars.get('REDIS_PASSWORD', '')}\n")
        f.write(f"REDIS_DB={env_vars.get('REDIS_DB', '0')}\n\n")

        # 认证配置
        f.write("# 认证配置\n")
        f.write(f"SECRET_KEY={env_vars.get('SECRET_KEY', 'change-this-secret-key')}\n")
        f.write(f"ALGORITHM={env_vars.get('ALGORITHM', 'HS256')}\n")
        f.write(f"ACCESS_TOKEN_EXPIRE_MINUTES={env_vars.get('ACCESS_TOKEN_EXPIRE_MINUTES', '30')}\n\n")

        # API 密钥
        f.write("# 外部 API 密钥\n")
        f.write(f"TUSHARE_TOKEN={env_vars.get('TUSHARE_TOKEN', '')}\n")
        f.write(f"ALPHA_VANTAGE_API_KEY={env_vars.get('ALPHA_VANTAGE_API_KEY', '')}\n")
        f.write(f"OPENAI_API_KEY={env_vars.get('OPENAI_API_KEY', '')}\n\n")

        # GLM 配置（重点）
        f.write("# GLM API 配置（智谱 AI）\n")
        f.write(f"GLM_API_KEY={env_vars.get('GLM_API_KEY', '')}\n")
        f.write(f"GLM_API_URL={env_vars.get('GLM_API_URL', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')}\n")
        f.write(f"GLM_MODEL={env_vars.get('GLM_MODEL', 'glm-4')}\n\n")

        # 交易配置
        f.write("# 交易配置\n")
        f.write(f"DEFAULT_MAX_SLIPPAGE={env_vars.get('DEFAULT_MAX_SLIPPAGE', '0.001')}\n")
        f.write(f"DEFAULT_MAX_POSITION_RATIO={env_vars.get('DEFAULT_MAX_POSITION_RATIO', '0.3')}\n")
        f.write(f"DEFAULT_MAX_DAILY_LOSS_RATIO={env_vars.get('DEFAULT_MAX_DAILY_LOSS_RATIO', '0.05')}\n\n")

        # 风控配置
        f.write("# 风控配置\n")
        f.write(f"RISK_CONTROL_ENABLED={env_vars.get('RISK_CONTROL_ENABLED', 'true')}\n")
        f.write(f"RISK_CHECK_INTERVAL={env_vars.get('RISK_CHECK_INTERVAL', '60')}\n\n")

        # 日志配置
        f.write("# 日志配置\n")
        f.write(f"LOG_FILE_PATH={env_vars.get('LOG_FILE_PATH', 'logs/app.log')}\n")
        f.write(f"LOG_RETENTION_DAYS={env_vars.get('LOG_RETENTION_DAYS', '30')}\n")


def setup_glm(api_key: str, model: str = "glm-4"):
    """配置 GLM API Key"""
    env_vars = read_env_file()
    env_vars['GLM_API_KEY'] = api_key
    env_vars['GLM_MODEL'] = model
    env_vars['GLM_API_URL'] = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
    write_env_file(env_vars)

    print("=" * 60)
    print("✅ GLM-5 配置已更新！")
    print("=" * 60)
    print(f"\n📝 配置信息:")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"   Model: {model}")
    print(f"   API URL: https://open.bigmodel.cn/api/paas/v4/chat/completions")
    print("\n⚠️  请重启后端服务使配置生效:")
    print("   cd backend && source venv/bin/activate && uvicorn src.main:app --reload")


async def test_glm_connection():
    """测试 GLM API 连接"""
    load_dotenv()

    api_key = os.getenv('GLM_API_KEY')
    api_url = os.getenv('GLM_API_URL', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
    model = os.getenv('GLM_MODEL', 'glm-4')

    print("=" * 60)
    print("🔍 测试 GLM-5 API 连接")
    print("=" * 60)

    if not api_key or api_key == 'your-glm-api-key':
        print("\n❌ GLM_API_KEY 未配置或使用占位符")
        print("\n请运行以下命令配置:")
        print("   python database/scripts/configure_glm.py setup <your-api-key>")
        return False

    print(f"\n📝 当前配置:")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"   Model: {model}")
    print(f"   API URL: {api_url}")

    print("\n🔄 正在测试连接...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "你好，请回复'GLM连接成功'"}
        ],
        "max_tokens": 50
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f"\n✅ 连接成功！")
                print(f"   响应: {content}")
                return True
            else:
                print(f"\n❌ 连接失败！")
                print(f"   状态码: {response.status_code}")
                print(f"   错误: {response.text}")
                return False

    except Exception as e:
        print(f"\n❌ 连接异常: {e}")
        return False


def show_status():
    """显示 GLM 配置状态"""
    load_dotenv()

    api_key = os.getenv('GLM_API_KEY')
    model = os.getenv('GLM_MODEL', 'glm-4')
    api_url = os.getenv('GLM_API_URL', '')

    print("=" * 60)
    print("📊 GLM-5 配置状态")
    print("=" * 60)

    if not api_key or api_key == 'your-glm-api-key':
        print("\n❌ 状态: 未配置")
        print("\n请运行以下命令配置:")
        print("   python database/scripts/configure_glm.py setup <your-api-key>")
    else:
        print("\n✅ 状态: 已配置")
        print(f"\n📝 配置详情:")
        print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
        print(f"   Model: {model}")
        print(f"   API URL: {api_url}")

    print("\n" + "=" * 60)
    print("🔧 可用命令:")
    print("=" * 60)
    print("   python database/scripts/configure_glm.py setup <api-key>  # 配置")
    print("   python database/scripts/configure_glm.py test             # 测试连接")
    print("   python database/scripts/configure_glm.py status           # 查看状态")


def show_usage_guide():
    """显示使用指南"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║            GLM-5 自动调用功能使用指南                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  配置完成后，系统会自动调用 GLM-5 完成以下任务:                 ║
║                                                              ║
║  1. AI 策略生成                                              ║
║     POST /api/v1/ai/generate/strategy                        ║
║     - 根据市场状况自动生成交易策略                             ║
║     - 包含入场/出场条件和风控规则                              ║
║                                                              ║
║  2. AI 市场分析                                              ║
║     POST /api/v1/ai/analyze/market                           ║
║     - 分析股票市场趋势                                        ║
║     - 提供投资建议和置信度评分                                 ║
║                                                              ║
║  3. AI 智能选股                                              ║
║     POST /api/v1/ai/pick/stocks                              ║
║     - 根据量化标准筛选股票                                     ║
║     - 提供选股理由和风险提示                                   ║
║                                                              ║
║  4. AI 策略优化                                              ║
║     POST /api/v1/ai/optimize/strategy                        ║
║     - 分析策略弱点                                           ║
║     - 提供参数调整建议                                        ║
║                                                              ║
║  5. 美林时钟经济周期判断                                       ║
║     自动分析宏观经济数据，判断经济周期                          ║
║                                                              ║
║  模型选择:                                                    ║
║  - glm-4: 标准版（推荐）                                      ║
║  - glm-4-plus: 增强版（更强推理能力）                          ║
║  - glm-4-air: 轻量版（更快响应）                              ║
║  - glm-5: 最新版（当前用户使用的模型）                         ║
║                                                              ║
║  获取 API Key:                                               ║
║  1. 访问 https://open.bigmodel.cn/                           ║
║  2. 注册/登录账号                                             ║
║  3. 进入「API 密钥」页面创建密钥                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_usage_guide()
        show_status()
        return

    command = sys.argv[1].lower()

    if command == 'setup':
        if len(sys.argv) < 3:
            print("❌ 请提供 API Key")
            print("用法: python configure_glm.py setup <your-api-key> [model]")
            return
        api_key = sys.argv[2]
        model = sys.argv[3] if len(sys.argv) > 3 else "glm-4"
        setup_glm(api_key, model)

    elif command == 'test':
        asyncio.run(test_glm_connection())

    elif command == 'status':
        show_status()

    else:
        print(f"❌ 未知命令: {command}")
        print("可用命令: setup, test, status")


if __name__ == '__main__':
    main()
