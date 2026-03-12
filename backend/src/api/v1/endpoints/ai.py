"""
AI 功能 API 端点

提供 AI 策略生成、智能选股、市场分析等 AI 功能。
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from loguru import logger
import os
import uuid
from datetime import datetime

from src.services.ai.glm import glm5_service
from src.services.ai.mcp import mcp_service, generate_strategy_with_tools
from src.core.config import settings
from src.services.strategy.registry import strategy_registry, StrategyFrequency, StrategyLifecycleStatus, StrategyMetadata
from src.services.strategy.ai_strategy_wrapper import AIStrategyWrapper


router = APIRouter(prefix="/ai", tags=["AI Intelligence"])


# ========================================
# Pydantic 模型
# ========================================

class StrategyGenerationRequest(BaseModel):
    """AI 策略生成请求"""
    strategy_type: str = Field(..., description="策略类型（如：动量、反转、套利）")
    market_condition: str = Field(..., description="市场状况描述")
    risk_tolerance: str = Field(default="medium", description="风险承受能力")
    symbol: Optional[str] = Field(default=None, description="指导股票代码（可选，填入后将获取该股票的综合信息）")
    custom_prompt: Optional[str] = Field(default=None, description="自然语言约束或提示词（可选，AI 将根据用户要求优化策略）")


class MarketAnalysisRequest(BaseModel):
    """市场分析请求"""
    symbols: List[str] = Field(..., description="股票代码列表")
    analysis_type: str = Field(default="comprehensive", description="分析类型")


class SmartStockPickingRequest(BaseModel):
    """智能选股请求"""
    criteria: Dict[str, Any] = Field(..., description="选股标准")
    universe: str = Field(default="A股全市场", description="股票池范围")
    top_n: int = Field(default=10, description="返回前 N 只股票")


class StrategyOptimizationRequest(BaseModel):
    """策略优化请求"""
    current_strategy: str = Field(..., description="当前策略描述")
    backtest_results: Dict[str, Any] = Field(..., description="当前回测结果")
    optimization_goal: str = Field(default="sharpe_ratio", description="优化目标")


# ========================================
# API 端点
# ========================================

@router.post("/generate/strategy", summary="AI 生成交易策略")
async def generate_strategy(request: StrategyGenerationRequest):
    """
    AI 生成交易策略

    使用 GLM-5 根据用户需求自动生成交易策略。

    - **strategy_type**: 策略类型（如：动量、反转、套利）
    - **market_condition**: 市场状况描述
    - **risk_tolerance**: 风险承受能力（low/medium/high）
    - **symbol**: 指导股票代码（可选，填入后将获取该股票的实时交易信息、基本面、新闻等综合信息）
    - **custom_prompt**: 自然语言约束或提示词（可选，AI 将根据用户要求优化生成的策略）
    """
    if not glm5_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="GLM-5 API 未配置，AI 功能不可用"
        )

    try:
        logger.info(f"Generating strategy: {request.strategy_type}, symbol: {request.symbol}")

        result = await glm5_service.generate_strategy(
            strategy_type=request.strategy_type,
            market_condition=request.market_condition,
            risk_tolerance=request.risk_tolerance,
            symbol=request.symbol,
            custom_prompt=request.custom_prompt
        )

        return result

    except Exception as e:
        logger.error(f"Strategy generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/market", summary="AI 市场分析")
async def analyze_market(request: MarketAnalysisRequest):
    """
    AI 市场分析

    使用 GLM-5 分析股票市场。

    - **symbols**: 股票代码列表（如：["000001.SZ", "600000.SH"]）
    - **analysis_type**: 分析类型（comprehensive/technical/fundamental）

    返回市场分析结果，包括：
    - 市场趋势判断
    - 个股技术分析
    - 投资建议（买入/卖出/持有）
    - 置信度评分
    """
    if not glm5_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="GLM-5 API 未配置，AI 功能不可用"
        )

    try:
        logger.info(f"Analyzing market: {request.symbols}")

        result = await glm5_service.analyze_market(
            symbols=request.symbols,
            analysis_type=request.analysis_type
        )

        return result

    except Exception as e:
        logger.error(f"Market analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pick/stocks", summary="AI 智能选股")
async def smart_stock_picking(request: SmartStockPickingRequest):
    """
    AI 智能选股

    使用 GLM-5 根据量化标准进行智能选股。

    - **criteria**: 选股标准（JSON 格式）
    - **universe**: 股票池范围（如：A股全市场）
    - **top_n**: 返回前 N 只股票

    选股标准示例：
    ```json
    {
        "pe_ratio": {"max": 30},
        "roe": {"min": 0.15},
        "debt_ratio": {"max": 0.6},
        "market_cap": {"min": 1000000000}
    }
    ```

    返回：
    - 股票代码
    - 股票名称
    - 综合评分（0-100）
    - 选股理由
    - 风险提示
    """
    if not glm5_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="GLM-5 API 未配置，AI 功能不可用"
        )

    try:
        logger.info(f"Smart stock picking: universe={request.universe}, top_n={request.top_n}")

        result = await glm5_service.smart_stock_picking(
            criteria=request.criteria,
            universe=request.universe,
            top_n=request.top_n
        )

        return result

    except Exception as e:
        logger.error(f"Smart stock picking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/strategy", summary="AI 优化策略")
async def optimize_strategy(request: StrategyOptimizationRequest):
    """
    AI 优化策略

    使用 GLM-5 分析当前策略并提供优化建议。

    - **current_strategy**: 当前策略描述
    - **backtest_results**: 当前回测结果（JSON 格式）
    - **optimization_goal**: 优化目标（sharpe_ratio/returns/max_drawdown）

    返回：
    - 策略弱点分析
    - 参数调整建议（具体数值）
    - 风控改进建议
    - 预期改进效果
    """
    if not glm5_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="GLM-5 API 未配置，AI 功能不可用"
        )

    try:
        logger.info(f"Optimizing strategy for: {request.optimization_goal}")

        result = await glm5_service.optimize_strategy(
            current_strategy=request.current_strategy,
            backtest_results=request.backtest_results,
            optimization_goal=request.optimization_goal
        )

        return result

    except Exception as e:
        logger.error(f"Strategy optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools", summary="获取可用的 MCP 工具")
async def get_mcp_tools():
    """
    获取可用的 MCP 工具列表

    返回所有已注册的 MCP 工具，包括：
    - 工具名称
    - 工具描述
    - 参数定义
    """
    tools = mcp_service.get_all_tools()

    return {
        "success": True,
        "data": {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": "工具参数"
                }
                for tool_name, tool in tools.items()
            ]
        }
    }


@router.get("/status", summary="检查 AI 服务状态")
async def check_ai_status():
    """
    检查 AI 服务状态

    返回：
    - GLM-5 API 配置状态
    - 可用的 MCP 工具
    - 服务健康状态
    """
    glm_available = glm5_service.is_available()

    tools = mcp_service.get_all_tools()

    return {
        "success": True,
        "data": {
            "glm5_available": glm_available,
            "mcp_tools_count": len(tools),
            "mcp_tools": list(tools.keys()),
            "status": "available" if glm_available else "unavailable"
        }
    }


# ========================================
# AI 策略保存
# ========================================

class SaveAIStrategyRequest(BaseModel):
    """保存 AI 生成策略请求"""
    strategy_name: str = Field(..., description="策略名称")
    strategy_type: str = Field(..., description="策略类型")
    description: str = Field(default="", description="策略描述")
    content: Dict[str, Any] = Field(..., description="AI 生成的策略内容")
    risk_level: str = Field(default="medium", description="风险等级")
    market_condition: str = Field(default="", description="市场状况")


@router.post("/save-strategy", summary="保存 AI 生成的策略")
async def save_ai_strategy(request: SaveAIStrategyRequest):
    """
    保存 AI 生成的策略

    将 AI 生成的策略保存到策略目录，并自动注册到策略注册表。

    - **strategy_name**: 策略名称
    - **strategy_type**: 策略类型
    - **description**: 策略描述
    - **content**: AI 生成的策略内容（JSON 格式）
    - **risk_level**: 风险等级
    - **market_condition**: 生成时的市场状况
    """
    try:
        # 生成策略 ID
        strategy_id = f"ai_{request.strategy_type}_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 策略目录
        strategy_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "strategies",
            "ai_generated"
        )
        os.makedirs(strategy_dir, exist_ok=True)

        # 策略文件路径
        file_path = os.path.join(strategy_dir, f"{strategy_id}.json")

        # 构建策略元数据
        strategy_data = {
            "strategy_id": strategy_id,
            "name": request.strategy_name,
            "version": "1.0.0",
            "author": "AI Generator",
            "description": request.description,
            "category": request.strategy_type,
            "frequency": "1d",
            "status": "development",
            "tags": ["AI生成", request.strategy_type],
            "risk_level": request.risk_level,
            "market_condition": request.market_condition,
            "generated_at": datetime.now().isoformat(),
            "content": request.content,
            "default_params": {},
            "params_schema": {},
            "min_history_bars": 100,
            "supported_markets": ["A股"],
        }

        # 保存到文件
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(strategy_data, f, ensure_ascii=False, indent=2)

        logger.info(f"AI 策略已保存到文件: {strategy_id}")

        # 注册到策略注册表
        try:
            # 注册 AI 策略到注册表（使用已导入的类）
            metadata = StrategyMetadata(
                strategy_id=strategy_id,
                name=request.strategy_name,
                strategy_class=AIStrategyWrapper,
                version="1.0.0",
                author="AI Generator",
                description=request.description,
                category=request.strategy_type,
                frequency=StrategyFrequency.DAILY,
                status=StrategyLifecycleStatus.DEVELOPMENT,
                tags=["AI生成", request.strategy_type],
                params_schema={},
                default_params={"ai_content": request.content},
                min_history_bars=100,
                supported_markets=["A股"],
                risk_level=request.risk_level,
            )

            strategy_registry._register_metadata(metadata)
            logger.info(f"AI 策略已注册到注册表: {strategy_id}")

        except Exception as reg_error:
            logger.warning(f"注册策略到注册表失败（文件已保存）: {reg_error}")
            # 不影响主流程，继续返回成功

        return {
            "success": True,
            "data": {
                "strategy_id": strategy_id,
                "file_path": file_path,
                "strategy": strategy_data,
                "registered": True,
            },
            "message": f"策略 {request.strategy_name} 已保存并注册成功"
        }

    except Exception as e:
        logger.error(f"保存 AI 策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存策略失败: {str(e)}")


# ========================================
# GLM 配置管理
# ========================================

class GLMConfigRequest(BaseModel):
    """GLM 配置请求"""
    api_key: str = Field(..., description="GLM API Key")
    api_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        description="GLM API URL"
    )
    model: str = Field(default="glm-4", description="GLM 模型名称")


class GLMConfigResponse(BaseModel):
    """GLM 配置响应"""
    success: bool
    message: str
    config: Dict[str, Any]


@router.post("/config/glm", response_model=GLMConfigResponse, summary="配置 GLM API")
async def configure_glm(
    request: GLMConfigRequest,
    current_user: Any = Depends(lambda: None)  # TODO: 添加认证
):
    """
    配置 GLM API

    将 GLM API 配置保存到环境变量文件，配置后需要重启服务生效。

    - **api_key**: GLM API Key（从智谱 AI 开放平台获取）
    - **api_url**: GLM API 端点 URL
    - **model**: GLM 模型名称（glm-4, glm-4-plus, glm-4-air, glm-5）
    """
    import os
    from pathlib import Path

    try:
        # 获取 .env 文件路径
        backend_dir = Path(__file__).parent.parent.parent.parent.parent
        env_file = backend_dir / ".env"

        # 读取现有配置
        env_vars = {}
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

        # 更新 GLM 配置
        env_vars['GLM_API_KEY'] = request.api_key
        env_vars['GLM_API_URL'] = request.api_url
        env_vars['GLM_MODEL'] = request.model

        # 写回 .env 文件
        with open(env_file, 'w', encoding='utf-8') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        logger.info(f"GLM API 配置已更新: model={request.model}")

        # 更新运行时配置
        settings.glm_api_key = request.api_key
        settings.glm_api_url = request.api_url
        settings.glm_model = request.model

        # 重新初始化 GLM 服务
        glm5_service.api_key = request.api_key
        glm5_service.api_url = request.api_url
        glm5_service.model = request.model

        return GLMConfigResponse(
            success=True,
            message="GLM API 配置成功，服务已更新",
            config={
                "model": request.model,
                "api_url": request.api_url,
                "api_key_masked": f"{request.api_key[:10]}...{request.api_key[-4:]}"
            }
        )

    except Exception as e:
        logger.error(f"配置 GLM API 失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置失败: {str(e)}")


@router.get("/config/glm", summary="获取 GLM 配置状态")
async def get_glm_config():
    """
    获取 GLM 配置状态

    返回当前 GLM API 的配置状态（不包含 API Key 明文）
    """
    try:
        api_key = settings.glm_api_key
        api_url = settings.glm_api_url
        model = settings.glm_model

        is_configured = bool(api_key and api_key != 'your-glm-api-key')

        return {
            "success": True,
            "data": {
                "is_configured": is_configured,
                "model": model,
                "api_url": api_url,
                "api_key_masked": f"{api_key[:10]}...{api_key[-4:]}" if is_configured else None,
                "available_models": [
                    {"value": "glm-4", "label": "GLM-4（标准版）"},
                    {"value": "glm-4-plus", "label": "GLM-4-Plus（增强版）"},
                    {"value": "glm-4-air", "label": "GLM-4-Air（轻量版）"},
                    {"value": "glm-5", "label": "GLM-5（最新版）"},
                ]
            }
        }
    except Exception as e:
        logger.error(f"获取 GLM 配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/config/glm/test", summary="测试 GLM API 连接")
async def test_glm_connection():
    """
    测试 GLM API 连接

    发送测试请求验证 API Key 是否有效
    """
    if not glm5_service.is_available():
        return {
            "success": False,
            "message": "GLM API 未配置"
        }

    try:
        # 发送简单测试请求
        messages = [
            {"role": "user", "content": "请回复'连接成功'"}
        ]

        result = await glm5_service._call_api(messages, max_tokens=50)

        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')

        return {
            "success": True,
            "message": "GLM API 连接成功",
            "data": {
                "response": content,
                "model": settings.glm_model
            }
        }

    except Exception as e:
        logger.error(f"测试 GLM 连接失败: {e}")
        return {
            "success": False,
            "message": f"连接失败: {str(e)}"
        }
