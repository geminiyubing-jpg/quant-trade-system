"""
==============================================
QuantAI Ecosystem - 市场动态 API 端点
==============================================

提供市场动态相关的 REST API：
- 经济周期判断
- 资产配置推荐
- 宏观指标查询
- 新闻情感分析
- AI Agent 对话
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from src.core.security import get_current_user
from src.services.market_dynamics.merrill_clock_engine import (
    MerrillClockEngine,
    EconomicPhase,
    get_merrill_clock_engine
)
from src.services.market_dynamics.macro_agent import (
    MacroAgent,
    get_macro_agent
)
from src.services.market_dynamics.news_sentiment_analyzer import (
    NewsSentimentAnalyzer,
    get_news_sentiment_analyzer
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market-dynamics", tags=["Market Dynamics"])


# ==========================================
# 请求/响应模型
# ==========================================

class PhaseJudgmentRequest(BaseModel):
    """周期判断请求"""
    country: str = Field(default="CN", description="国家代码: CN/US/EU")


class AssetAllocationRequest(BaseModel):
    """资产配置请求"""
    country: str = Field(default="CN", description="国家代码")
    risk_preference: str = Field(default="moderate", description="风险偏好: conservative/moderate/aggressive")


class NewsAnalysisRequest(BaseModel):
    """新闻分析请求"""
    title: str = Field(..., description="新闻标题")
    content: str = Field(default="", description="新闻内容")
    source: str = Field(default="", description="新闻来源")


class AgentQueryRequest(BaseModel):
    """Agent查询请求"""
    query: str = Field(..., description="用户查询")
    country: str = Field(default="CN", description="默认国家")
    risk_preference: str = Field(default="moderate", description="默认风险偏好")


class PhaseJudgmentResponse(BaseModel):
    """周期判断响应"""
    judgment_id: str
    country: str
    phase: str
    phase_name: str
    confidence: float
    growth_score: float
    inflation_score: float
    reasoning: str
    alternative_phases: List[dict]
    judgment_time: datetime


class AssetAllocationResponse(BaseModel):
    """资产配置响应"""
    allocation_id: str
    phase: str
    phase_name: str
    equities_weight: float
    bonds_weight: float
    commodities_weight: float
    cash_weight: float
    sector_recommendations: List[dict]
    risk_level: str
    expected_return: float
    expected_volatility: float
    rationale: str


class NewsSentimentResponse(BaseModel):
    """新闻情感响应"""
    sentiment_id: str
    title: str
    summary: str
    sentiment_score: float
    sentiment_label: str
    confidence: float
    topics: List[str]
    impact_level: str


class AgentQueryResponse(BaseModel):
    """Agent查询响应"""
    query: str
    response: str
    tools_used: List[str]
    execution_time_ms: int
    status: str


class MarketOverviewResponse(BaseModel):
    """市场概览响应"""
    country: str
    main_index: dict
    market_breadth: dict
    sentiment: str
    phase_judgment: Optional[PhaseJudgmentResponse]
    allocation_recommendation: Optional[dict]


# ==========================================
# 阶段名称映射
# ==========================================

PHASE_NAMES = {
    EconomicPhase.RECESSION: "衰退期 (冬)",
    EconomicPhase.RECOVERY: "复苏期 (春)",
    EconomicPhase.OVERHEAT: "过热期 (夏)",
    EconomicPhase.STAGFLATION: "滞胀期 (秋)"
}


# ==========================================
# API 端点
# ==========================================

@router.get("/overview", response_model=MarketOverviewResponse)
async def get_market_overview(
    country: str = Query(default="CN", description="国家代码"),
    current_user = Depends(get_current_user)
):
    """
    获取市场概览

    包含：
    - 主要指数
    - 市场宽度
    - 经济周期判断
    - 资产配置建议
    """
    logger.info(f"获取市场概览: country={country}")

    try:
        # 获取美林时钟引擎
        engine = get_merrill_clock_engine()

        # 获取宏观指标
        from src.services.market_dynamics.macro_data_pipeline import get_macro_data_pipeline
        pipeline = await get_macro_data_pipeline()
        indicators = await pipeline.fetch_all_indicators([country])

        # 判断周期
        judgment = engine.judge_phase(country, indicators)

        # 生成配置
        allocation = engine.generate_allocation(judgment, "moderate")

        # 构建响应
        # 模拟市场数据
        if country == "CN":
            main_index = {
                "name": "上证指数",
                "value": 3250.50,
                "change": 0.015,
                "change_percent": 1.5
            }
            market_breadth = {
                "advancing": 2500,
                "declining": 1800,
                "unchanged": 200
            }
            sentiment = "neutral"
        else:
            main_index = {
                "name": "S&P 500",
                "value": 5200.00,
                "change": 0.008,
                "change_percent": 0.8
            }
            market_breadth = {
                "advancing": 280,
                "declining": 220,
                "unchanged": 10
            }
            sentiment = "positive"

        return MarketOverviewResponse(
            country=country,
            main_index=main_index,
            market_breadth=market_breadth,
            sentiment=sentiment,
            phase_judgment=PhaseJudgmentResponse(
                judgment_id=judgment.judgment_id,
                country=judgment.country,
                phase=judgment.phase.value,
                phase_name=PHASE_NAMES.get(judgment.phase, judgment.phase.value),
                confidence=judgment.confidence,
                growth_score=judgment.growth_score,
                inflation_score=judgment.inflation_score,
                reasoning=judgment.reasoning,
                alternative_phases=[{"phase": p.value, "probability": prob} for p, prob in judgment.alternative_phases],
                judgment_time=judgment.judgment_time
            ),
            allocation_recommendation={
                "equities": allocation.equities_weight,
                "bonds": allocation.bonds_weight,
                "commodities": allocation.commodities_weight,
                "cash": allocation.cash_weight,
                "sectors": allocation.sector_recommendations[:3]
            }
        )

    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/phase-judgment", response_model=PhaseJudgmentResponse)
async def judge_economic_phase(
    request: PhaseJudgmentRequest,
    current_user = Depends(get_current_user)
):
    """
    判断经济周期阶段

    基于美林时钟框架判断当前经济所处阶段
    """
    logger.info(f"判断经济周期: country={request.country}")

    try:
        engine = get_merrill_clock_engine()

        # 获取宏观指标
        from src.services.market_dynamics.macro_data_pipeline import get_macro_data_pipeline
        pipeline = await get_macro_data_pipeline()
        indicators = await pipeline.fetch_all_indicators([request.country])

        # 判断周期
        judgment = engine.judge_phase(request.country, indicators)

        return PhaseJudgmentResponse(
            judgment_id=judgment.judgment_id,
            country=judgment.country,
            phase=judgment.phase.value,
            phase_name=PHASE_NAMES.get(judgment.phase, judgment.phase.value),
            confidence=judgment.confidence,
            growth_score=judgment.growth_score,
            inflation_score=judgment.inflation_score,
            reasoning=judgment.reasoning,
            alternative_phases=[{"phase": p.value, "probability": prob} for p, prob in judgment.alternative_phases],
            judgment_time=judgment.judgment_time
        )

    except Exception as e:
        logger.error(f"判断经济周期失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/asset-allocation", response_model=AssetAllocationResponse)
async def get_asset_allocation(
    request: AssetAllocationRequest,
    current_user = Depends(get_current_user)
):
    """
    获取资产配置建议

    基于当前经济周期提供资产配置建议
    """
    logger.info(f"获取资产配置: country={request.country}, risk={request.risk_preference}")

    try:
        engine = get_merrill_clock_engine()

        # 获取最新判断
        judgment = engine.get_latest_judgment(request.country)

        if not judgment:
            # 如果没有缓存判断，重新判断
            from src.services.market_dynamics.macro_data_pipeline import get_macro_data_pipeline
            pipeline = await get_macro_data_pipeline()
            indicators = await pipeline.fetch_all_indicators([request.country])
            judgment = engine.judge_phase(request.country, indicators)

        # 生成配置
        allocation = engine.generate_allocation(judgment, request.risk_preference)

        return AssetAllocationResponse(
            allocation_id=allocation.allocation_id,
            phase=allocation.phase.value,
            phase_name=PHASE_NAMES.get(allocation.phase, allocation.phase.value),
            equities_weight=allocation.equities_weight,
            bonds_weight=allocation.bonds_weight,
            commodities_weight=allocation.commodities_weight,
            cash_weight=allocation.cash_weight,
            sector_recommendations=allocation.sector_recommendations,
            risk_level=allocation.risk_level,
            expected_return=allocation.expected_return,
            expected_volatility=allocation.expected_volatility,
            rationale=allocation.rationale
        )

    except Exception as e:
        logger.error(f"获取资产配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news-sentiment", response_model=NewsSentimentResponse)
async def analyze_news_sentiment(
    request: NewsAnalysisRequest,
    current_user = Depends(get_current_user)
):
    """
    分析新闻情感

    使用NLP分析财经新闻的情感倾向
    """
    logger.info(f"分析新闻情感: title={request.title[:50]}")

    try:
        analyzer = get_news_sentiment_analyzer()
        result = await analyzer.analyze(
            title=request.title,
            content=request.content,
            source=request.source
        )

        return NewsSentimentResponse(
            sentiment_id=result.sentiment_id,
            title=result.title,
            summary=result.summary,
            sentiment_score=result.sentiment_score,
            sentiment_label=result.sentiment_label,
            confidence=result.confidence,
            topics=result.topics,
            impact_level=result.impact_level
        )

    except Exception as e:
        logger.error(f"分析新闻情感失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/query", response_model=AgentQueryResponse)
async def query_macro_agent(
    request: AgentQueryRequest,
    current_user = Depends(get_current_user)
):
    """
    查询宏观分析 Agent

    使用 AI Agent 进行智能宏观分析
    """
    logger.info(f"Agent查询: query={request.query[:50]}")

    try:
        agent = get_macro_agent()
        response = await agent.analyze(
            user_query=request.query,
            user_id=current_user.id if current_user else None
        )

        return AgentQueryResponse(
            query=response.query,
            response=response.response,
            tools_used=response.tools_used,
            execution_time_ms=response.execution_time_ms,
            status=response.status
        )

    except Exception as e:
        logger.error(f"Agent查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/merrill-clock/info")
async def get_merrill_clock_info():
    """
    获取美林时钟框架说明
    """
    return {
        "framework": "Merrill Lynch Investment Clock",
        "description": "基于经济增长和通胀的经济周期分析框架",
        "phases": [
            {
                "name": "recession",
                "name_cn": "衰退期 (冬)",
                "characteristics": "经济下行 + 通胀下行",
                "best_asset": "债券",
                "description": "经济活动放缓，通胀压力减轻，央行可能降息刺激经济"
            },
            {
                "name": "recovery",
                "name_cn": "复苏期 (春)",
                "characteristics": "经济上行 + 通胀下行",
                "best_asset": "股票",
                "description": "经济开始复苏，企业盈利改善，通胀仍处于低位"
            },
            {
                "name": "overheat",
                "name_cn": "过热期 (夏)",
                "characteristics": "经济上行 + 通胀上行",
                "best_asset": "商品",
                "description": "经济强劲增长，通胀压力上升，央行可能加息抑制过热"
            },
            {
                "name": "stagflation",
                "name_cn": "滞胀期 (秋)",
                "characteristics": "经济下行 + 通胀上行",
                "best_asset": "现金",
                "description": "经济增长放缓但通胀高企，是投资环境最差的阶段"
            }
        ],
        "key_indicators": {
            "growth": ["GDP增长率", "PMI", "工业增加值", "失业率"],
            "inflation": ["CPI", "PPI", "核心PCE", "工资增长率"]
        }
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "market-dynamics",
        "timestamp": datetime.utcnow().isoformat()
    }
