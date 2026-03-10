"""
==============================================
QuantAI Ecosystem - AI 美林时钟引擎
==============================================

基于美林投资时钟框架，自动判断宏观经济周期阶段
并提供资产配置建议。

美林时钟四阶段：
- 衰退期 (Recession): 经济下行 + 通胀下行 → 债券最优
- 复苏期 (Recovery): 经济上行 + 通胀下行 → 股票最优
- 过热期 (Overheat): 经济上行 + 通胀上行 → 商品最优
- 滞胀期 (Stagflation): 经济下行 + 通胀上行 → 现金最优
"""

import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class EconomicPhase(str, Enum):
    """经济周期四阶段"""
    RECESSION = "recession"      # 衰退期 (冬) - 债券最优
    RECOVERY = "recovery"        # 复苏期 (春) - 股票最优
    OVERHEAT = "overheat"        # 过热期 (夏) - 商品最优
    STAGFLATION = "stagflation"  # 滞胀期 (秋) - 现金最优


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MacroIndicator:
    """宏观指标"""
    indicator_id: str
    name: str
    current_value: float
    previous_value: float
    yoy_change: float              # 同比变化
    mom_change: float              # 环比变化
    trend: str                     # upward, downward, stable
    last_updated: datetime
    data_source: str
    frequency: str                 # daily, weekly, monthly, quarterly

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


@dataclass
class PhaseJudgment:
    """周期判断结果"""
    judgment_id: str
    country: str
    phase: EconomicPhase
    confidence: float             # 置信度 0-1
    growth_score: float           # 增长得分 -1到1
    inflation_score: float        # 通胀得分 -1到1
    indicators_used: List[str]
    reasoning: str                # AI推理过程
    alternative_phases: List[Tuple[EconomicPhase, float]]  # 备选阶段及概率
    judgment_time: datetime
    valid_until: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            'judgment_id': self.judgment_id,
            'country': self.country,
            'phase': self.phase.value,
            'confidence': self.confidence,
            'growth_score': self.growth_score,
            'inflation_score': self.inflation_score,
            'indicators_used': self.indicators_used,
            'reasoning': self.reasoning,
            'alternative_phases': [(p.value, prob) for p, prob in self.alternative_phases],
            'judgment_time': self.judgment_time.isoformat(),
            'valid_until': self.valid_until.isoformat()
        }


@dataclass
class AssetAllocation:
    """资产配置推荐"""
    allocation_id: str
    phase: EconomicPhase
    country: str
    equities_weight: float        # 股票权重
    bonds_weight: float           # 债券权重
    commodities_weight: float     # 商品权重
    cash_weight: float            # 现金权重
    sector_recommendations: List[Dict[str, Any]]
    risk_level: str
    expected_return: float
    expected_volatility: float
    rebalance_frequency: str
    rationale: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            'allocation_id': self.allocation_id,
            'phase': self.phase.value,
            'country': self.country,
            'equities_weight': self.equities_weight,
            'bonds_weight': self.bonds_weight,
            'commodities_weight': self.commodities_weight,
            'cash_weight': self.cash_weight,
            'sector_recommendations': self.sector_recommendations,
            'risk_level': self.risk_level,
            'expected_return': self.expected_return,
            'expected_volatility': self.expected_volatility,
            'rebalance_frequency': self.rebalance_frequency,
            'rationale': self.rationale,
            'created_at': self.created_at.isoformat()
        }


class MerrillClockEngine:
    """
    美林时钟引擎

    功能：
    - 宏观指标分析
    - 经济周期判断
    - 资产配置推荐
    - AI 增强推理
    """

    # 美林时钟判断阈值 (可根据历史数据优化)
    GROWTH_THRESHOLD = 0.02       # GDP增速阈值 2%
    INFLATION_THRESHOLD = 0.025   # CPI阈值 2.5%

    # 各阶段资产配置基准 (达里奥全天候理念)
    PHASE_ALLOCATIONS = {
        EconomicPhase.RECESSION: {
            'equities': 0.15, 'bonds': 0.55, 'commodities': 0.10, 'cash': 0.20,
            'description': '衰退期：经济下行、通胀下行，债券表现最优',
            'risk_level': RiskLevel.MEDIUM
        },
        EconomicPhase.RECOVERY: {
            'equities': 0.55, 'bonds': 0.25, 'commodities': 0.10, 'cash': 0.10,
            'description': '复苏期：经济上行、通胀下行，股票表现最优',
            'risk_level': RiskLevel.MEDIUM
        },
        EconomicPhase.OVERHEAT: {
            'equities': 0.30, 'bonds': 0.10, 'commodities': 0.50, 'cash': 0.10,
            'description': '过热期：经济上行、通胀上行，商品表现最优',
            'risk_level': RiskLevel.HIGH
        },
        EconomicPhase.STAGFLATION: {
            'equities': 0.10, 'bonds': 0.15, 'commodities': 0.35, 'cash': 0.40,
            'description': '滞胀期：经济下行、通胀上行，现金表现最优',
            'risk_level': RiskLevel.HIGH
        }
    }

    # 指标权重配置
    GROWTH_INDICATOR_WEIGHTS = {
        'gdp_growth': 0.40,
        'unemployment_rate': -0.25,    # 负相关
        'pmi': 0.20,
        'industrial_production': 0.15
    }

    INFLATION_INDICATOR_WEIGHTS = {
        'cpi': 0.45,
        'ppi': 0.25,
        'core_pce': 0.20,
        'wage_growth': 0.10
    }

    # 行业推荐配置
    SECTOR_RECOMMENDATIONS = {
        EconomicPhase.RECESSION: [
            {'sector': '公用事业', 'weight': 0.25, 'rationale': '防御性行业，需求稳定'},
            {'sector': '医疗保健', 'weight': 0.20, 'rationale': '刚需行业，抗周期性强'},
            {'sector': '必需消费', 'weight': 0.20, 'rationale': '消费必需品，业绩稳定'},
            {'sector': '债券', 'weight': 0.20, 'rationale': '利率下行受益'},
            {'sector': '黄金', 'weight': 0.15, 'rationale': '避险资产'}
        ],
        EconomicPhase.RECOVERY: [
            {'sector': '科技', 'weight': 0.25, 'rationale': '增长弹性大，估值修复'},
            {'sector': '金融', 'weight': 0.20, 'rationale': '利率上行受益'},
            {'sector': '工业', 'weight': 0.20, 'rationale': '经济复苏直接受益'},
            {'sector': '可选消费', 'weight': 0.15, 'rationale': '消费信心恢复'},
            {'sector': '材料', 'weight': 0.20, 'rationale': '需求回升'}
        ],
        EconomicPhase.OVERHEAT: [
            {'sector': '能源', 'weight': 0.25, 'rationale': '通胀直接受益'},
            {'sector': '材料', 'weight': 0.20, 'rationale': '商品涨价受益'},
            {'sector': '工业', 'weight': 0.15, 'rationale': '需求旺盛'},
            {'sector': '商品', 'weight': 0.25, 'rationale': '通胀对冲'},
            {'sector': '新兴市场', 'weight': 0.15, 'rationale': '风险偏好上升'}
        ],
        EconomicPhase.STAGFLATION: [
            {'sector': '能源', 'weight': 0.20, 'rationale': '通胀对冲'},
            {'sector': '必需消费', 'weight': 0.15, 'rationale': '防御性'},
            {'sector': '黄金', 'weight': 0.20, 'rationale': '避险保值'},
            {'sector': '现金等价物', 'weight': 0.25, 'rationale': '现金为王'},
            {'sector': '医疗保健', 'weight': 0.20, 'rationale': '刚需防御'}
        ]
    }

    def __init__(self, db_session=None, ai_client=None, cache_service=None):
        self.db = db_session
        self.ai_client = ai_client
        self.cache = cache_service
        self._indicator_cache: Dict[str, MacroIndicator] = {}

    def judge_phase(
        self,
        country: str,
        indicators: Dict[str, MacroIndicator],
        use_ai: bool = True
    ) -> PhaseJudgment:
        """
        判断经济周期阶段

        Args:
            country: 国家代码 (US/CN/EU)
            indicators: 宏观指标字典
            use_ai: 是否使用AI增强判断

        Returns:
            PhaseJudgment: 周期判断结果
        """
        logger.info(f"开始判断 {country} 经济周期阶段")

        # 1. 计算增长得分 (GDP、失业率、PMI等)
        growth_score = self._calculate_growth_score(indicators)

        # 2. 计算通胀得分 (CPI、PPI、PCE等)
        inflation_score = self._calculate_inflation_score(indicators)

        # 3. 基于美林时钟框架判断阶段
        base_phase = self._determine_phase(growth_score, inflation_score)

        # 4. AI增强判断 (考虑多因素和非线性关系)
        if use_ai and self.ai_client:
            ai_phase, confidence, reasoning = self._ai_enhance_judgment(
                country, indicators, growth_score, inflation_score, base_phase
            )
        else:
            ai_phase = base_phase
            confidence = self._calculate_base_confidence(growth_score, inflation_score)
            reasoning = self._generate_rule_based_reasoning(
                growth_score, inflation_score, base_phase
            )

        # 5. 计算备选阶段概率
        alternative_phases = self._calculate_alternative_probabilities(
            growth_score, inflation_score, ai_phase
        )

        judgment = PhaseJudgment(
            judgment_id=f"mc_{uuid.uuid4().hex[:12]}",
            country=country,
            phase=ai_phase,
            confidence=confidence,
            growth_score=growth_score,
            inflation_score=inflation_score,
            indicators_used=list(indicators.keys()),
            reasoning=reasoning,
            alternative_phases=alternative_phases,
            judgment_time=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=7)
        )

        # 6. 保存判断结果
        self._save_judgment(judgment)

        logger.info(f"经济周期判断完成: {country} -> {ai_phase.value}, 置信度: {confidence:.1%}")
        return judgment

    def generate_allocation(
        self,
        judgment: PhaseJudgment,
        risk_preference: str = 'moderate'
    ) -> AssetAllocation:
        """
        生成资产配置推荐

        Args:
            judgment: 周期判断结果
            risk_preference: 风险偏好 (conservative/moderate/aggressive)

        Returns:
            AssetAllocation: 资产配置推荐
        """
        logger.info(f"生成资产配置推荐: 阶段={judgment.phase.value}, 风险偏好={risk_preference}")

        # 1. 获取基准配置
        base_allocation = self.PHASE_ALLOCATIONS[judgment.phase]

        # 2. 根据风险偏好调整
        adjusted_allocation = self._adjust_for_risk_preference(
            base_allocation, risk_preference
        )

        # 3. 获取行业推荐
        sector_recommendations = self.SECTOR_RECOMMENDATIONS.get(judgment.phase, [])

        # 4. 生成配置理由
        rationale = self._generate_allocation_rationale(
            judgment, adjusted_allocation, sector_recommendations
        )

        # 5. 估算预期收益和波动率
        expected_return = self._estimate_expected_return(adjusted_allocation)
        expected_volatility = self._estimate_volatility(adjusted_allocation)

        allocation = AssetAllocation(
            allocation_id=f"alloc_{uuid.uuid4().hex[:12]}",
            phase=judgment.phase,
            country=judgment.country,
            equities_weight=adjusted_allocation['equities'],
            bonds_weight=adjusted_allocation['bonds'],
            commodities_weight=adjusted_allocation['commodities'],
            cash_weight=adjusted_allocation['cash'],
            sector_recommendations=sector_recommendations,
            risk_level=base_allocation['risk_level'].value,
            expected_return=expected_return,
            expected_volatility=expected_volatility,
            rebalance_frequency='monthly',
            rationale=rationale,
            created_at=datetime.utcnow()
        )

        # 6. 保存配置
        self._save_allocation(allocation, judgment.judgment_id)

        return allocation

    def _calculate_growth_score(self, indicators: Dict[str, MacroIndicator]) -> float:
        """计算增长得分 (-1 到 1)"""
        score = 0.0
        total_weight = 0.0

        for indicator_id, weight in self.GROWTH_INDICATOR_WEIGHTS.items():
            if indicator_id in indicators:
                ind = indicators[indicator_id]
                # 标准化处理
                normalized = self._normalize_indicator(ind, indicator_id)
                score += abs(weight) * normalized * (1 if weight > 0 else -1)
                total_weight += abs(weight)

        if total_weight > 0:
            score = score / total_weight

        return float(np.clip(score, -1, 1))

    def _calculate_inflation_score(self, indicators: Dict[str, MacroIndicator]) -> float:
        """计算通胀得分 (-1 到 1)"""
        score = 0.0
        total_weight = 0.0

        for indicator_id, weight in self.INFLATION_INDICATOR_WEIGHTS.items():
            if indicator_id in indicators:
                ind = indicators[indicator_id]
                normalized = self._normalize_indicator(ind, indicator_id)
                score += abs(weight) * normalized
                total_weight += abs(weight)

        if total_weight > 0:
            score = score / total_weight

        return float(np.clip(score, -1, 1))

    def _normalize_indicator(self, indicator: MacroIndicator, indicator_id: str) -> float:
        """指标标准化 (-1 到 1)"""
        # 基于同比变化进行标准化
        # 正值表示上升，负值表示下降
        change = indicator.yoy_change

        # 根据指标类型调整阈值
        if indicator_id == 'gdp_growth':
            # GDP: 0-3% 正常, >3% 高增长, <0% 负增长
            return np.clip(change / 0.05, -1, 1)
        elif indicator_id == 'unemployment_rate':
            # 失业率: 反向指标
            return np.clip(-change / 0.05, -1, 1)
        elif indicator_id in ['cpi', 'ppi', 'core_pce']:
            # 通胀指标: 0-3% 正常, >3% 高通胀
            return np.clip((change - 0.02) / 0.05, -1, 1)
        elif indicator_id == 'pmi':
            # PMI: 50是荣枯线
            pmi_value = indicator.current_value
            return np.clip((pmi_value - 50) / 10, -1, 1)
        else:
            return np.clip(change / 0.1, -1, 1)

    def _determine_phase(self, growth_score: float, inflation_score: float) -> EconomicPhase:
        """基于美林时钟框架判断阶段"""
        # 增长维度：growth_score > 0 表示经济上行
        # 通胀维度：inflation_score > 0 表示通胀上行

        if growth_score > 0 and inflation_score < 0:
            return EconomicPhase.RECOVERY    # 复苏期 (春)
        elif growth_score > 0 and inflation_score > 0:
            return EconomicPhase.OVERHEAT    # 过热期 (夏)
        elif growth_score < 0 and inflation_score > 0:
            return EconomicPhase.STAGFLATION # 滞胀期 (秋)
        else:
            return EconomicPhase.RECESSION   # 衰退期 (冬)

    def _ai_enhance_judgment(
        self,
        country: str,
        indicators: Dict[str, MacroIndicator],
        growth_score: float,
        inflation_score: float,
        base_phase: EconomicPhase
    ) -> Tuple[EconomicPhase, float, str]:
        """AI增强判断"""
        # 如果没有AI客户端，返回规则判断结果
        if not self.ai_client:
            confidence = self._calculate_base_confidence(growth_score, inflation_score)
            reasoning = self._generate_rule_based_reasoning(growth_score, inflation_score, base_phase)
            return base_phase, confidence, reasoning

        try:
            # 构建提示词
            prompt = self._build_judgment_prompt(country, indicators, growth_score, inflation_score, base_phase)

            # 调用AI (这里应该调用GLM-4.5或其他LLM)
            # response = await self.ai_client.generate(prompt, response_format="json")
            # result = json.loads(response)

            # 模拟AI响应 (实际实现时替换)
            result = {
                'phase': base_phase.value,
                'confidence': min(0.95, self._calculate_base_confidence(growth_score, inflation_score) + 0.1),
                'reasoning': self._generate_rule_based_reasoning(growth_score, inflation_score, base_phase)
            }

            phase = EconomicPhase(result.get('phase', base_phase.value))
            confidence = result.get('confidence', 0.7)
            reasoning = result.get('reasoning', '')

            return phase, confidence, reasoning

        except Exception as e:
            logger.error(f"AI增强判断失败: {e}")
            # Fallback到规则判断
            confidence = self._calculate_base_confidence(growth_score, inflation_score)
            reasoning = self._generate_rule_based_reasoning(growth_score, inflation_score, base_phase)
            return base_phase, confidence, reasoning

    def _build_judgment_prompt(
        self,
        country: str,
        indicators: Dict[str, MacroIndicator],
        growth_score: float,
        inflation_score: float,
        base_phase: EconomicPhase
    ) -> str:
        """构建AI判断提示词"""
        indicator_lines = []
        for ind_id, ind in indicators.items():
            indicator_lines.append(
                f"- {ind.name}: 当前值 {ind.current_value:.2f}, 同比变化 {ind.yoy_change:.2%}, 趋势 {ind.trend}"
            )

        return f"""
请作为宏观经济专家，分析以下经济数据并判断经济周期阶段：

国家：{country}
增长得分：{growth_score:.3f} (-1到1，正值表示经济上行)
通胀得分：{inflation_score:.3f} (-1到1，正值表示通胀上行)

关键指标：
{chr(10).join(indicator_lines)}

基础美林时钟判断：{base_phase.value}

请考虑以下因素进行综合判断：
1. 指标的趋势和动量
2. 各指标之间的一致性
3. 当前全球宏观环境
4. 政策影响

返回JSON格式：
{{
    "phase": "recession/recovery/overheat/stagflation",
    "confidence": 0.0-1.0,
    "reasoning": "详细推理过程"
}}
"""

    def _calculate_base_confidence(self, growth_score: float, inflation_score: float) -> float:
        """计算基础置信度"""
        # 基于得分到决策边界的距离计算置信度
        # 距离越远，置信度越高
        growth_abs = abs(growth_score)
        inflation_abs = abs(inflation_score)

        # 归一化到0.5-0.9范围
        confidence = 0.5 + (growth_abs + inflation_abs) / 4
        return min(0.9, confidence)

    def _generate_rule_based_reasoning(
        self,
        growth_score: float,
        inflation_score: float,
        phase: EconomicPhase
    ) -> str:
        """生成规则推理说明"""
        growth_status = "经济上行" if growth_score > 0 else "经济下行"
        inflation_status = "通胀上行" if inflation_score > 0 else "通胀下行"

        phase_descriptions = {
            EconomicPhase.RECESSION: "衰退期特征明显，建议防御性配置",
            EconomicPhase.RECOVERY: "复苏期特征明显，可适当增加风险资产",
            EconomicPhase.OVERHEAT: "过热期特征明显，需警惕政策收紧",
            EconomicPhase.STAGFLATION: "滞胀期特征明显，建议持有现金和抗通胀资产"
        }

        return f"""
基于美林时钟框架分析：
1. 增长维度：{growth_status} (得分: {growth_score:.3f})
2. 通胀维度：{inflation_status} (得分: {inflation_score:.3f})
3. 综合判断：{phase_descriptions.get(phase, '')}
4. 置信度评估：基于指标一致性计算
        """.strip()

    def _calculate_alternative_probabilities(
        self,
        growth_score: float,
        inflation_score: float,
        primary_phase: EconomicPhase
    ) -> List[Tuple[EconomicPhase, float]]:
        """计算备选阶段概率"""
        alternatives = []

        # 计算每个阶段的概率
        for phase in EconomicPhase:
            if phase != primary_phase:
                # 基于与该阶段边界的距离计算概率
                prob = self._calculate_phase_probability(growth_score, inflation_score, phase)
                alternatives.append((phase, prob))

        # 归一化
        total = sum(p for _, p in alternatives) + 0.6  # 主阶段权重0.6
        alternatives = [(p, prob / total) for p, prob in alternatives]

        # 按概率排序
        alternatives.sort(key=lambda x: -x[1])

        return alternatives[:3]  # 返回前3个备选

    def _calculate_phase_probability(
        self,
        growth: float,
        inflation: float,
        phase: EconomicPhase
    ) -> float:
        """计算属于某阶段的概率"""
        # 根据阶段定义计算得分匹配度
        if phase == EconomicPhase.RECOVERY:
            target = (1, -1)  # 增长正，通胀负
        elif phase == EconomicPhase.OVERHEAT:
            target = (1, 1)   # 增长正，通胀正
        elif phase == EconomicPhase.STAGFLATION:
            target = (-1, 1)  # 增长负，通胀正
        else:  # RECESSION
            target = (-1, -1) # 增长负，通胀负

        # 计算欧氏距离
        distance = np.sqrt((growth - target[0])**2 + (inflation - target[1])**2)
        # 转换为概率 (距离越近概率越高)
        prob = max(0, 1 - distance / 3)
        return prob

    def _adjust_for_risk_preference(
        self,
        allocation: Dict,
        risk_preference: str
    ) -> Dict[str, float]:
        """根据风险偏好调整配置"""
        adjustments = {
            'conservative': {'equities': -0.10, 'bonds': 0.05, 'cash': 0.05},
            'moderate': {'equities': 0, 'bonds': 0, 'cash': 0},
            'aggressive': {'equities': 0.10, 'bonds': -0.05, 'cash': -0.05}
        }

        adjusted = {
            'equities': allocation['equities'],
            'bonds': allocation['bonds'],
            'commodities': allocation['commodities'],
            'cash': allocation['cash']
        }

        adj = adjustments.get(risk_preference, adjustments['moderate'])

        for asset_class, delta in adj.items():
            if asset_class in adjusted:
                adjusted[asset_class] = np.clip(
                    adjusted[asset_class] + delta, 0.05, 0.70
                )

        # 重新归一化
        total = sum(adjusted.values())
        return {k: v / total for k, v in adjusted.items()}

    def _generate_allocation_rationale(
        self,
        phase: PhaseJudgment,
        allocation: Dict[str, float],
        sectors: List[Dict]
    ) -> str:
        """生成配置理由"""
        phase_desc = self.PHASE_ALLOCATIONS[phase.phase]['description']
        sector_names = [s['sector'] for s in sectors[:3]]

        return f"""
基于{phase.country}当前处于{phase.phase.value}阶段的判断 (置信度: {phase.confidence:.1%})：

【核心逻辑】
1. 增长得分：{phase.growth_score:.3f} → {'经济扩张' if phase.growth_score > 0 else '经济收缩'}
2. 通胀得分：{phase.inflation_score:.3f} → {'通胀上升' if phase.inflation_score > 0 else '通胀下降'}
3. {phase_desc}

【配置建议】
- 股票：{allocation['equities']:.0%} ({'超配' if allocation['equities'] > 0.3 else '低配'})
- 债券：{allocation['bonds']:.0%}
- 商品：{allocation['commodities']:.0%}
- 现金：{allocation['cash']:.0%}

【重点行业】{', '.join(sector_names)}

【风险提示】需密切关注指标变化，建议月度再平衡
        """.strip()

    def _estimate_expected_return(self, allocation: Dict[str, float]) -> float:
        """估算预期收益"""
        # 基于历史数据估算各资产类别的预期收益
        returns = {
            'equities': 0.08,      # 股票 8%
            'bonds': 0.03,         # 债券 3%
            'commodities': 0.05,   # 商品 5%
            'cash': 0.02           # 现金 2%
        }
        return sum(allocation.get(k, 0) * v for k, v in returns.items())

    def _estimate_volatility(self, allocation: Dict[str, float]) -> float:
        """估算波动率"""
        # 基于历史数据估算各资产类别的波动率
        volatilities = {
            'equities': 0.15,
            'bonds': 0.05,
            'commodities': 0.20,
            'cash': 0.01
        }
        # 简化计算 (实际应该考虑协方差矩阵)
        return np.sqrt(sum(
            (allocation.get(k, 0) * v)**2
            for k, v in volatilities.items()
        ))

    def _save_judgment(self, judgment: PhaseJudgment) -> None:
        """保存判断结果"""
        if self.db:
            try:
                self.db.execute("""
                    INSERT INTO merrill_clock_judgments
                    (judgment_id, country, phase, confidence, growth_score, inflation_score,
                     indicators_used, reasoning, alternative_phases, judgment_time, valid_until)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    judgment.judgment_id,
                    judgment.country,
                    judgment.phase.value,
                    judgment.confidence,
                    judgment.growth_score,
                    judgment.inflation_score,
                    json.dumps(judgment.indicators_used),
                    judgment.reasoning,
                    json.dumps([(p.value, prob) for p, prob in judgment.alternative_phases]),
                    judgment.judgment_time,
                    judgment.valid_until
                ))
                logger.debug(f"保存判断结果: {judgment.judgment_id}")
            except Exception as e:
                logger.error(f"保存判断结果失败: {e}")

    def _save_allocation(self, allocation: AssetAllocation, judgment_id: str) -> None:
        """保存资产配置"""
        if self.db:
            try:
                self.db.execute("""
                    INSERT INTO asset_allocations
                    (allocation_id, judgment_id, phase, country, equities_weight, bonds_weight,
                     commodities_weight, cash_weight, sector_recommendations, risk_level,
                     expected_return, expected_volatility, rebalance_frequency, rationale, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    allocation.allocation_id,
                    judgment_id,
                    allocation.phase.value,
                    allocation.country,
                    allocation.equities_weight,
                    allocation.bonds_weight,
                    allocation.commodities_weight,
                    allocation.cash_weight,
                    json.dumps(allocation.sector_recommendations),
                    allocation.risk_level,
                    allocation.expected_return,
                    allocation.expected_volatility,
                    allocation.rebalance_frequency,
                    allocation.rationale,
                    allocation.created_at
                ))
                logger.debug(f"保存资产配置: {allocation.allocation_id}")
            except Exception as e:
                logger.error(f"保存资产配置失败: {e}")

    def get_latest_judgment(self, country: str) -> Optional[PhaseJudgment]:
        """获取最新判断结果"""
        if self.db:
            try:
                result = self.db.execute("""
                    SELECT * FROM merrill_clock_judgments
                    WHERE country = ? AND valid_until > NOW()
                    ORDER BY judgment_time DESC LIMIT 1
                """, (country,)).fetchone()

                if result:
                    return self._parse_judgment_from_db(result)
            except Exception as e:
                logger.error(f"获取判断结果失败: {e}")
        return None

    def _parse_judgment_from_db(self, row) -> PhaseJudgment:
        """从数据库解析判断结果"""
        return PhaseJudgment(
            judgment_id=row['judgment_id'],
            country=row['country'],
            phase=EconomicPhase(row['phase']),
            confidence=row['confidence'],
            growth_score=row['growth_score'],
            inflation_score=row['inflation_score'],
            indicators_used=json.loads(row['indicators_used']),
            reasoning=row['reasoning'],
            alternative_phases=[
                (EconomicPhase(p), prob)
                for p, prob in json.loads(row['alternative_phases'])
            ],
            judgment_time=row['judgment_time'],
            valid_until=row['valid_until']
        )


# 单例实例
_merrill_clock_engine: Optional[MerrillClockEngine] = None


def get_merrill_clock_engine() -> MerrillClockEngine:
    """获取美林时钟引擎实例"""
    global _merrill_clock_engine
    if _merrill_clock_engine is None:
        _merrill_clock_engine = MerrillClockEngine()
    return _merrill_clock_engine
