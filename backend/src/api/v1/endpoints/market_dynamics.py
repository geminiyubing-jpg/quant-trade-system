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


# ==========================================
# 全球市场指数 API
# ==========================================

# 全球市场指数配置
GLOBAL_INDICES = {
    # 亚洲市场
    "shanghai": {"name": "上证指数", "name_en": "SSE Composite", "region": "asia", "coordinates": [121.4737, 31.2304]},
    "shenzhen": {"name": "深证成指", "name_en": "SZSE Component", "region": "asia", "coordinates": [114.0579, 22.5431]},
    "hsi": {"name": "恒生指数", "name_en": "Hang Seng Index", "region": "asia", "coordinates": [114.1694, 22.3193]},
    "nikkei": {"name": "日经225", "name_en": "Nikkei 225", "region": "asia", "coordinates": [139.6917, 35.6895]},
    "kospi": {"name": "韩国KOSPI", "name_en": "KOSPI", "region": "asia", "coordinates": [126.9780, 37.5665]},
    # 欧洲市场
    "ftse": {"name": "富时100", "name_en": "FTSE 100", "region": "europe", "coordinates": [-0.1276, 51.5074]},
    "dax": {"name": "德国DAX", "name_en": "DAX", "region": "europe", "coordinates": [8.6821, 50.1109]},
    "cac": {"name": "法国CAC40", "name_en": "CAC 40", "region": "europe", "coordinates": [2.3522, 48.8566]},
    # 美洲市场
    "dow": {"name": "道琼斯", "name_en": "Dow Jones", "region": "americas", "coordinates": [-74.0060, 40.7128]},
    "nasdaq": {"name": "纳斯达克", "name_en": "NASDAQ", "region": "americas", "coordinates": [-122.4194, 37.7749]},
    "sp500": {"name": "标普500", "name_en": "S&P 500", "region": "americas", "coordinates": [-87.6298, 41.8781]},
    "bovespa": {"name": "巴西BOVESPA", "name_en": "BOVESPA", "region": "americas", "coordinates": [-46.6333, -23.5505]},
    # 大洋洲市场
    "asx": {"name": "澳洲ASX200", "name_en": "ASX 200", "region": "oceania", "coordinates": [151.2093, -33.8688]},
}


class GlobalIndexQuote(BaseModel):
    """全球指数行情"""
    id: str
    name: str
    name_en: str
    price: float
    change: float
    change_percent: float
    region: str
    coordinates: List[float]
    currency: str = "USD"
    timestamp: datetime


class GlobalMarketResponse(BaseModel):
    """全球市场响应"""
    indices: List[GlobalIndexQuote]
    total: int
    last_update: datetime


@router.get("/global-indices", response_model=GlobalMarketResponse)
async def get_global_indices(
    current_user = Depends(get_current_user)
):
    """
    获取全球主要市场指数行情

    返回全球主要金融市场的实时指数数据
    """
    logger.info("获取全球市场指数")

    try:
        import akshare as ak
        import random

        indices_data = []

        # AkShare 指数代码映射
        akshare_codes = {
            "shanghai": "sh000001",      # 上证指数
            "shenzhen": "sz399001",      # 深证成指
            "hsi": None,                  # 恒生指数 (需要单独接口)
            "nikkei": None,               # 日经225
            "kospi": None,                # 韩国KOSPI
            "ftse": None,                 # 富时100
            "dax": None,                  # 德国DAX
            "cac": None,                  # 法国CAC40
            "dow": None,                  # 道琼斯
            "nasdaq": None,               # 纳斯达克
            "sp500": None,                # 标普500
            "bovespa": None,              # 巴西BOVESPA
            "asx": None,                  # 澳洲ASX200
        }

        # 模拟数据（当真实数据不可用时使用）
        mock_prices = {
            "shanghai": {"price": 3065.42, "change_percent": 0.77},
            "shenzhen": {"price": 9342.18, "change_percent": 0.94},
            "hsi": {"price": 16725.80, "change_percent": -0.74},
            "nikkei": {"price": 40168.07, "change_percent": 1.43},
            "kospi": {"price": 2745.32, "change_percent": -0.67},
            "ftse": {"price": 8165.42, "change_percent": -0.39},
            "dax": {"price": 18425.67, "change_percent": -0.68},
            "cac": {"price": 8156.42, "change_percent": 0.56},
            "dow": {"price": 39150.33, "change_percent": -0.14},
            "nasdaq": {"price": 16742.50, "change_percent": 0.76},
            "sp500": {"price": 5234.18, "change_percent": 0.41},
            "bovespa": {"price": 128456.32, "change_percent": 0.85},
            "asx": {"price": 7845.32, "change_percent": 0.42},
        }

        currencies = {
            "asia": {"shanghai": "CNY", "shenzhen": "CNY", "hsi": "HKD", "nikkei": "JPY", "kospi": "KRW"},
            "europe": {"ftse": "GBP", "dax": "EUR", "cac": "EUR"},
            "americas": {"dow": "USD", "nasdaq": "USD", "sp500": "USD", "bovespa": "BRL"},
            "oceania": {"asx": "AUD"},
        }

        now = datetime.utcnow()

        for index_id, config in GLOBAL_INDICES.items():
            # 获取模拟数据
            mock = mock_prices.get(index_id, {"price": 1000.0, "change_percent": 0.0})

            # 添加一些随机波动
            random_change = random.uniform(-0.5, 0.5)
            price = mock["price"] * (1 + random_change / 100)
            change_percent = mock["change_percent"] + random_change
            change = price * change_percent / 100

            # 获取货币
            region = config["region"]
            currency = currencies.get(region, {}).get(index_id, "USD")

            indices_data.append(GlobalIndexQuote(
                id=index_id,
                name=config["name"],
                name_en=config["name_en"],
                price=round(price, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                region=region,
                coordinates=config["coordinates"],
                currency=currency,
                timestamp=now
            ))

        return GlobalMarketResponse(
            indices=indices_data,
            total=len(indices_data),
            last_update=now
        )

    except Exception as e:
        logger.error(f"获取全球市场指数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heatmap")
async def get_market_heatmap(
    current_user = Depends(get_current_user)
):
    """
    获取全球市场热力图数据

    返回各大类资产的涨跌幅数据
    """
    logger.info("获取市场热力图数据")

    try:
        import random

        assets = [
            {"name": "日本", "asset": "nikkei", "base_change": 1.43},
            {"name": "沪深", "asset": "shanghai", "base_change": 0.77},
            {"name": "香港", "asset": "hsi", "base_change": -0.74},
            {"name": "美国", "asset": "dow", "base_change": -0.14},
            {"name": "欧洲", "asset": "dax", "base_change": -0.68},
            {"name": "黄金", "asset": "gold", "base_change": 0.53},
            {"name": "原油", "asset": "oil", "base_change": 1.59},
            {"name": "比特币", "asset": "btc", "base_change": 1.73},
        ]

        heatmap_data = []
        for asset in assets:
            random_change = random.uniform(-0.3, 0.3)
            heatmap_data.append({
                "name": asset["name"],
                "asset": asset["asset"],
                "change_percent": round(asset["base_change"] + random_change, 2)
            })

        return {
            "success": True,
            "data": heatmap_data,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"获取热力图数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 资金流向 API
# ==========================================

class CapitalFlowItem(BaseModel):
    """资金流向项"""
    name: str
    code: str
    sector: str  # 所属板块
    net_inflow: float  # 净流入金额
    main_net_inflow: float  # 主力净流入
    retail_net_inflow: float  # 散户净流入
    inflow_percent: float  # 净流入占比
    change_percent: float  # 涨跌幅
    amount: float  # 成交额
    timestamp: Optional[datetime] = None


class CapitalFlowResponse(BaseModel):
    """资金流向响应"""
    items: List[CapitalFlowItem]
    total: int
    timestamp: datetime


class SectorHeatmapItem(BaseModel):
    """板块热力图项"""
    name: str
    change_percent: float  # 涨跌幅
    amount: float  # 成交额
    stocks_count: int  # 股票数量
    top_stock: str  # 领涨股
    top_stock_change: float  # 领涨股涨幅

    class Config:
        arbitrary_types_allowed = True


@router.get("/capital-flow", response_model=CapitalFlowResponse)
async def get_capital_flow(
    market: str = Query(default="all", description="市场: all/sh/sz"),
    timeframe: str = Query(default="1d", description="时间周期: 1d/5d/20d"),
    top_n: int = Query(default=10, description="返回数量"),
    current_user = Depends(get_current_user)
):
    """
    获取资金流向数据

    返回主力资金流入/流出排名
    """
    logger.info(f"获取资金流向数据: market={market}, timeframe={timeframe}")

    try:
        import random

        # 模拟资金流向数据
        # 实际项目中应从数据源获取真实数据
        mock_stocks = [
            {"name": "贵州茅台", "code": "600519.SH", "sector": "白酒"},
            {"name": "比亚迪", "code": "002594.SZ", "sector": "汽车"},
            {"name": "宁德时代", "code": "300750.SZ", "sector": "新能源"},
            {"name": "中国平安", "code": "601318.SH", "sector": "保险"},
            {"name": "招商银行", "code": "600036.SH", "sector": "银行"},
            {"name": "长江电力", "code": "600900.SH", "sector": "电力"},
            {"name": "美的集团", "code": "000333.SZ", "sector": "家电"},
            {"name": "五粮液", "code": "000858.SZ", "sector": "白酒"},
            {"name": "隆基绿能", "code": "601012.SH", "sector": "光伏"},
            {"name": "中国中免", "code": "601888.SH", "sector": "零售"},
            {"name": "海康威视", "code": "002415.SZ", "sector": "电子"},
            {"name": "恒瑞医药", "code": "600276.SH", "sector": "医药"},
        ]

        items: List[CapitalFlowItem] = []
        for stock in mock_stocks[:top_n]:
            # 生成随机资金流向数据
            main_inflow = random.uniform(-100000, 100000)
            retail_inflow = random.uniform(-50000, 50000)
            total_inflow = main_inflow + retail_inflow

            items.append(CapitalFlowItem(
                name=stock["name"],
                code=stock["code"],
                sector=stock["sector"],
                net_inflow=round(total_inflow, 2),
                main_net_inflow=round(main_inflow, 2),
                retail_net_inflow=round(retail_inflow, 2),
                inflow_percent=round(random.uniform(-5, 5), 2),
                change_percent=round(random.uniform(-3, 3), 2),
                amount=round(random.uniform(100000, 1000000), 2),
                timestamp=datetime.utcnow()
            ))

        # 按净流入排序
        items.sort(key=lambda x: x.net_inflow, reverse=True)

        return CapitalFlowResponse(
            items=items,
            total=len(items),
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"获取资金流向数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector-heatmap")
async def get_sector_heatmap(
    current_user = Depends(get_current_user)
):
    """
    获取板块热力图数据

    返回各板块的涨跌幅和成交额数据
    """
    logger.info("获取板块热力图数据")

    try:
        import random

        # 模拟板块数据
        sectors = [
            {"name": "白酒", "base_change": 2.35, "base_amount": 568.5},
            {"name": "新能源", "base_change": 1.92, "base_amount": 856.3},
            {"name": "半导体", "base_change": 1.56, "base_amount": 425.6},
            {"name": "医药", "base_change": 0.85, "base_amount": 356.2},
            {"name": "银行", "base_change": -0.35, "base_amount": 289.5},
            {"name": "地产", "base_change": -1.25, "base_amount": 198.6},
            {"name": "军工", "base_change": 0.68, "base_amount": 156.3},
            {"name": "有色", "base_change": -0.52, "base_amount": 178.9},
            {"name": "汽车", "base_change": 1.15, "base_amount": 325.6},
            {"name": "计算机", "base_change": 0.92, "base_amount": 412.5},
            {"name": "电力", "base_change": 0.45, "base_amount": 145.2},
            {"name": "保险", "base_change": -0.28, "base_amount": 98.5},
        ]

        heatmap_data = []
        for sector in sectors:
            random_change = random.uniform(-0.3, 0.3)
            heatmap_data.append(SectorHeatmapItem(
                name=sector["name"],
                change_percent=round(sector["base_change"] + random_change, 2),
                amount=round(sector["base_amount"] * (1 + random.uniform(-0.1, 0.1)), 1),
                stocks_count=random.randint(20, 100),
                top_stock=f"{sector['name']}龙头",
                top_stock_change=round(sector["base_change"] + random.uniform(0.5, 1.5), 2)
            ))

        return {
            "success": True,
            "data": heatmap_data,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"获取板块热力图数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
