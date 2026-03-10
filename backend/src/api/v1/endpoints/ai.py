"""
AI 功能 API 端点

提供 AI 策略生成、智能选股、市场分析等 AI 功能。
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from loguru import logger

from src.services.ai.glm import glm5_service
from src.services.ai.mcp import mcp_service, generate_strategy_with_tools


router = APIRouter(prefix="/ai", tags=["AI Intelligence"])


# ========================================
# Pydantic 模型
# ========================================

class StrategyGenerationRequest(BaseModel):
    """AI 策略生成请求"""
    strategy_type: str = Field(..., description="策略类型（如：动量、反转、套利）")
    market_condition: str = Field(..., description="市场状况描述")
    risk_tolerance: str = Field(default="medium", description="风险承受能力")


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
    """
    if not glm5_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="GLM-5 API 未配置，AI 功能不可用"
        )

    try:
        logger.info(f"Generating strategy: {request.strategy_type}")

        result = await glm5_service.generate_strategy(
            strategy_type=request.strategy_type,
            market_condition=request.market_condition,
            risk_tolerance=request.risk_tolerance
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
