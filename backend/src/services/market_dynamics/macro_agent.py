"""
==============================================
QuantAI Ecosystem - AI 宏观分析 Agent
==============================================

基于 LangChain 的智能宏观分析 Agent：
- 多工具调用
- 推理可追溯
- Fallback 机制
"""

import logging
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .merrill_clock_engine import (
    MerrillClockEngine,
    EconomicPhase,
    PhaseJudgment,
    AssetAllocation
)

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Agent响应"""
    query: str
    response: str
    tools_used: List[str]
    intermediate_steps: List[Dict[str, Any]]
    execution_time_ms: int
    tokens_used: int
    status: str
    error_message: Optional[str] = None


class MacroAgent:
    """
    宏观分析 AI Agent

    功能：
    - 多工具调用
    - 推理可追溯
    - Fallback 机制
    - 结果存储
    """

    def __init__(
        self,
        merrill_engine: MerrillClockEngine,
        data_pipeline=None,
        news_analyzer=None,
        llm=None,
        db=None
    ):
        self.merrill_engine = merrill_engine
        self.data_pipeline = data_pipeline
        self.news_analyzer = news_analyzer
        self.llm = llm
        self.db = db

        # 工具注册表
        self._tools = {
            'get_macro_indicators': self._get_macro_indicators,
            'judge_economic_phase': self._judge_economic_phase,
            'get_asset_allocation': self._get_asset_allocation,
            'analyze_news_sentiment': self._analyze_news_sentiment,
            'get_market_overview': self._get_market_overview,
            'compare_historical_phases': self._compare_historical_phases,
        }

        # Agent系统提示词
        self._system_prompt = """你是宏观经济分析专家，擅长使用美林时钟框架分析经济周期并提供资产配置建议。

你的能力：
1. 获取和分析宏观经济数据
2. 判断经济周期阶段 (衰退/复苏/过热/滞胀)
3. 提供资产配置建议
4. 分析新闻情感对市场的影响

回答要求：
1. 推理过程要清晰可追溯
2. 给出置信度评估
3. 提供风险提示
4. 建议要符合金融逻辑

可用工具：
- get_macro_indicators: 获取指定国家的宏观经济指标数据
- judge_economic_phase: 判断当前经济周期阶段 (美林时钟)
- get_asset_allocation: 获取基于经济周期的资产配置建议
- analyze_news_sentiment: 分析财经新闻情感
- get_market_overview: 获取市场概览数据
- compare_historical_phases: 对比历史相似周期阶段
"""

    async def analyze(self, user_query: str, user_id: str = None) -> AgentResponse:
        """
        执行分析

        Args:
            user_query: 用户查询
            user_id: 用户ID

        Returns:
            AgentResponse: Agent响应
        """
        start_time = time.time()
        tools_used = []
        intermediate_steps = []
        tokens_used = 0

        logger.info(f"MacroAgent 收到查询: {user_query}")

        try:
            # 1. 意图识别
            intent = self._identify_intent(user_query)
            intermediate_steps.append({
                'step': 'intent_recognition',
                'result': intent
            })

            # 2. 工具选择和执行
            tool_calls = self._select_tools(intent)
            tool_results = {}

            for tool_name, tool_args in tool_calls:
                if tool_name in self._tools:
                    logger.info(f"执行工具: {tool_name}")
                    tools_used.append(tool_name)

                    try:
                        result = await self._tools[tool_name](**tool_args)
                        tool_results[tool_name] = result
                        intermediate_steps.append({
                            'step': 'tool_call',
                            'tool': tool_name,
                            'args': tool_args,
                            'result': result
                        })
                    except Exception as e:
                        logger.error(f"工具执行失败: {tool_name}, 错误: {e}")
                        intermediate_steps.append({
                            'step': 'tool_call',
                            'tool': tool_name,
                            'args': tool_args,
                            'error': str(e)
                        })

            # 3. 生成响应
            response = self._generate_response(user_query, intent, tool_results)
            intermediate_steps.append({
                'step': 'response_generation',
                'intent': intent
            })

            execution_time_ms = int((time.time() - start_time) * 1000)

            agent_response = AgentResponse(
                query=user_query,
                response=response,
                tools_used=tools_used,
                intermediate_steps=intermediate_steps,
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
                status='success'
            )

        except Exception as e:
            logger.error(f"Agent执行失败: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)

            agent_response = AgentResponse(
                query=user_query,
                response=f"分析过程中出现错误: {str(e)}",
                tools_used=tools_used,
                intermediate_steps=intermediate_steps,
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
                status='failed',
                error_message=str(e)
            )

        # 4. 保存执行日志
        self._save_execution_log(agent_response, user_id)

        return agent_response

    def _identify_intent(self, query: str) -> Dict[str, Any]:
        """识别用户意图"""
        query_lower = query.lower()

        # 意图关键词映射
        intent_patterns = {
            'phase_judgment': ['经济周期', '周期阶段', '美林时钟', '什么阶段', '复苏', '衰退', '过热', '滞胀'],
            'asset_allocation': ['资产配置', '投资建议', '配置建议', '买什么', '怎么配'],
            'news_analysis': ['新闻', '消息', '利好', '利空', '事件'],
            'market_overview': ['市场概览', '大盘', '指数', '行情'],
            'indicator_query': ['指标', 'GDP', 'CPI', 'PMI', '数据'],
        }

        detected_intents = []
        for intent, keywords in intent_patterns.items():
            if any(kw in query_lower for kw in keywords):
                detected_intents.append(intent)

        # 提取国家
        country = 'CN'  # 默认中国
        query_upper = query.upper()
        if '美国' in query or 'US' in query_upper:
            country = 'US'
        elif '欧盟' in query or '欧洲' in query:
            country = 'EU'

        # 提取风险偏好
        risk_preference = 'moderate'
        if '保守' in query:
            risk_preference = 'conservative'
        elif '激进' in query or '积极' in query:
            risk_preference = 'aggressive'

        return {
            'intents': detected_intents or ['general_inquiry'],
            'country': country,
            'risk_preference': risk_preference,
            'original_query': query
        }

    def _select_tools(self, intent: Dict[str, Any]) -> List[tuple]:
        """选择要执行的工具"""
        tools = []
        intents = intent['intents']
        country = intent['country']

        if 'phase_judgment' in intents:
            tools.append(('judge_economic_phase', {'country': country}))

        if 'asset_allocation' in intents:
            tools.append(('get_asset_allocation', {
                'country': country,
                'risk_preference': intent['risk_preference']
            }))

        if 'indicator_query' in intents:
            tools.append(('get_macro_indicators', {'country': country}))

        if 'news_analysis' in intents:
            tools.append(('analyze_news_sentiment', {'query': intent['original_query']}))

        if 'market_overview' in intents:
            tools.append(('get_market_overview', {'country': country}))

        # 默认：获取概览
        if not tools:
            tools.append(('get_market_overview', {'country': country}))

        return tools

    async def _get_macro_indicators(self, country: str) -> Dict[str, Any]:
        """获取宏观指标工具"""
        # 使用模拟数据
        if country == 'CN':
            indicators = {
                'GDP增长率': 5.2,
                'CPI': 0.25,
                'PMI': 50.5,
                '失业率': 5.2,
            }
        elif country == 'US':
            indicators = {
                'GDP增长率': 2.5,
                'CPI': 3.2,
                '失业率': 3.8,
                'PMI': 52.3,
            }
        else:
            indicators = {}

        return {
            'country': country,
            'indicators': indicators,
            'last_updated': datetime.utcnow().isoformat()
        }

    async def _judge_economic_phase(self, country: str) -> Dict[str, Any]:
        """判断经济周期工具"""
        # 获取模拟指标
        indicators = await self._get_macro_indicators(country)

        # 创建指标对象
        from .merrill_clock_engine import MacroIndicator
        now = datetime.utcnow()

        indicator_objs = {}
        if country == 'CN':
            indicator_objs['gdp_growth'] = MacroIndicator(
                indicator_id='gdp_growth', name='GDP增长率',
                current_value=5.2, previous_value=5.0,
                yoy_change=0.052, mom_change=0.02,
                trend='upward', last_updated=now,
                data_source='NBS', frequency='quarterly'
            )
            indicator_objs['cpi'] = MacroIndicator(
                indicator_id='cpi', name='CPI',
                current_value=102.5, previous_value=102.2,
                yoy_change=0.025, mom_change=0.003,
                trend='stable', last_updated=now,
                data_source='NBS', frequency='monthly'
            )
        else:
            indicator_objs['gdp_growth'] = MacroIndicator(
                indicator_id='gdp_growth', name='GDP增长率',
                current_value=2.5, previous_value=2.3,
                yoy_change=0.025, mom_change=0.01,
                trend='upward', last_updated=now,
                data_source='FRED', frequency='quarterly'
            )
            indicator_objs['cpi'] = MacroIndicator(
                indicator_id='cpi', name='CPI',
                current_value=308.0, previous_value=305.0,
                yoy_change=0.032, mom_change=0.01,
                trend='upward', last_updated=now,
                data_source='FRED', frequency='monthly'
            )

        # 判断周期
        judgment = self.merrill_engine.judge_phase(country, indicator_objs)

        return {
            'country': country,
            'phase': judgment.phase.value,
            'confidence': judgment.confidence,
            'growth_score': judgment.growth_score,
            'inflation_score': judgment.inflation_score,
            'reasoning': judgment.reasoning
        }

    async def _get_asset_allocation(
        self,
        country: str,
        risk_preference: str = 'moderate'
    ) -> Dict[str, Any]:
        """获取资产配置工具"""
        # 先判断周期
        phase_result = await self._judge_economic_phase(country)

        # 创建判断对象
        from .merrill_clock_engine import PhaseJudgment
        judgment = PhaseJudgment(
            judgment_id='temp',
            country=country,
            phase=EconomicPhase(phase_result['phase']),
            confidence=phase_result['confidence'],
            growth_score=phase_result['growth_score'],
            inflation_score=phase_result['inflation_score'],
            indicators_used=[],
            reasoning=phase_result['reasoning'],
            alternative_phases=[],
            judgment_time=datetime.utcnow(),
            valid_until=datetime.utcnow()
        )

        # 生成配置
        allocation = self.merrill_engine.generate_allocation(judgment, risk_preference)

        return {
            'phase': allocation.phase.value,
            'allocation': {
                'equities': allocation.equities_weight,
                'bonds': allocation.bonds_weight,
                'commodities': allocation.commodities_weight,
                'cash': allocation.cash_weight
            },
            'sectors': allocation.sector_recommendations,
            'rationale': allocation.rationale,
            'expected_return': allocation.expected_return,
            'risk_level': allocation.risk_level
        }

    async def _analyze_news_sentiment(self, query: str) -> Dict[str, Any]:
        """新闻情感分析工具"""
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'key_topics': ['市场动态'],
            'summary': '暂无相关新闻分析结果'
        }

    async def _get_market_overview(self, country: str) -> Dict[str, Any]:
        """获取市场概览工具"""
        if country == 'CN':
            return {
                'country': 'CN',
                'main_index': {
                    'name': '上证指数',
                    'value': 3250.50,
                    'change': 0.015
                },
                'market_breadth': {
                    'advancing': 2500,
                    'declining': 1800
                },
                'sentiment': 'neutral'
            }
        else:
            return {
                'country': country,
                'main_index': {
                    'name': 'S&P 500',
                    'value': 5200.00,
                    'change': 0.008
                },
                'market_breadth': {
                    'advancing': 280,
                    'declining': 220
                },
                'sentiment': 'positive'
            }

    async def _compare_historical_phases(self, country: str, current_phase: str) -> Dict[str, Any]:
        """对比历史周期工具"""
        # 模拟历史数据
        historical_similar = [
            {
                'period': '2019-Q1',
                'phase': current_phase,
                'similarity': 0.85,
                'outcome': '市场反弹10%'
            },
            {
                'period': '2016-Q2',
                'phase': current_phase,
                'similarity': 0.72,
                'outcome': '横盘震荡'
            }
        ]

        return {
            'current_phase': current_phase,
            'historical_similar': historical_similar
        }

    def _generate_response(
        self,
        query: str,
        intent: Dict[str, Any],
        tool_results: Dict[str, Any]
    ) -> str:
        """生成响应"""
        response_parts = []

        # 周期判断结果
        if 'judge_economic_phase' in tool_results:
            phase_data = tool_results['judge_economic_phase']
            response_parts.append(f"""
## 📊 经济周期判断

**当前阶段**: {phase_data['phase']}
**置信度**: {phase_data['confidence']:.1%}
**增长得分**: {phase_data['growth_score']:.3f}
**通胀得分**: {phase_data['inflation_score']:.3f}

{phase_data['reasoning']}
""")

        # 资产配置建议
        if 'get_asset_allocation' in tool_results:
            alloc_data = tool_results['get_asset_allocation']
            allocation = alloc_data['allocation']
            response_parts.append(f"""
## 💰 资产配置建议

| 资产类别 | 权重 |
|---------|------|
| 股票 | {allocation['equities']:.0%} |
| 债券 | {allocation['bonds']:.0%} |
| 商品 | {allocation['commodities']:.0%} |
| 现金 | {allocation['cash']:.0%} |

**预期收益**: {alloc_data['expected_return']:.1%}
**风险等级**: {alloc_data['risk_level']}

{alloc_data['rationale']}
""")

        # 市场概览
        if 'get_market_overview' in tool_results:
            overview = tool_results['get_market_overview']
            index = overview['main_index']
            response_parts.append(f"""
## 📈 市场概览

**主要指数**: {index['name']}
**当前点位**: {index['value']:,.2f}
**涨跌幅**: {index['change']:+.1%}

**市场宽度**: 上涨 {overview['market_breadth']['advancing']} / 下跌 {overview['market_breadth']['declining']}
**市场情绪**: {overview['sentiment']}
""")

        if not response_parts:
            return "您好，我是宏观分析助手。我可以帮您分析经济周期、提供资产配置建议。请问有什么可以帮助您的？"

        return "\n".join(response_parts)

    def _save_execution_log(self, response: AgentResponse, user_id: str = None) -> None:
        """保存执行日志"""
        if self.db:
            try:
                self.db.execute("""
                    INSERT INTO agent_execution_log
                    (log_id, agent_type, query, response, tools_used, intermediate_steps,
                     execution_time_ms, tokens_used, status, error_message, user_id, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"agent_log_{uuid.uuid4().hex[:12]}",
                    'macro_agent',
                    response.query,
                    response.response,
                    json.dumps(response.tools_used),
                    json.dumps(response.intermediate_steps),
                    response.execution_time_ms,
                    response.tokens_used,
                    response.status,
                    response.error_message,
                    user_id,
                    datetime.utcnow()
                ))
            except Exception as e:
                logger.error(f"保存Agent日志失败: {e}")


# 单例实例
_macro_agent: Optional[MacroAgent] = None


def get_macro_agent() -> MacroAgent:
    """获取宏观分析Agent实例"""
    global _macro_agent
    if _macro_agent is None:
        from .merrill_clock_engine import get_merrill_clock_engine
        merrill_engine = get_merrill_clock_engine()
        _macro_agent = MacroAgent(merrill_engine=merrill_engine)
    return _macro_agent
