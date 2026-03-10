"""
GLM-5 AI 服务模块

集成智谱 GLM-5 大模型，用于量化交易 AI 功能。
"""

from typing import Dict, List, Optional, Any
import httpx
from loguru import logger
from decimal import Decimal

from src.core.config import settings


class GLM5Service:
    """GLM-5 AI 服务类"""

    def __init__(self):
        """初始化 GLM-5 服务"""
        self.api_key = settings.glm_api_key
        self.api_url = settings.glm_api_url
        self.model = settings.glm_model

        if not self.api_key:
            logger.warning("GLM_API_KEY not configured, AI features will be disabled")

    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        """
        调用 GLM-5 API

        Args:
            messages: 消息列表
            temperature: 温度参数（0-1）
            max_tokens: 最大生成 token 数
            top_p: 核采样参数（0-1）

        Returns:
            API 响应结果
        """
        if not self.api_key:
            raise ValueError("GLM_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                logger.info(f"Calling GLM-5 API: {self.api_url}")
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"GLM-5 API error: {e}")
                raise
            except Exception as e:
                logger.error(f"GLM-5 service error: {e}")
                raise

    async def generate_strategy(
        self,
        strategy_type: str,
        market_condition: str,
        risk_tolerance: str = "medium",
    ) -> Dict[str, Any]:
        """
        AI 生成交易策略

        Args:
            strategy_type: 策略类型（如：动量、反转、套利）
            market_condition: 市场状况描述
            risk_tolerance: 风险承受能力

        Returns:
            生成的策略内容
        """
        system_prompt = """你是一个专业的量化交易策略专家。请根据用户的需求生成具体的交易策略。

策略必须包含：
1. 策略名称
2. 策略原理
3. 入场条件（具体、可执行）
4. 出场条件（具体、可执行）
5. 风控规则（止损、止盈、仓位管理）
6. 适用市场环境

请以 JSON 格式返回结果。"""

        user_prompt = f"""请生成一个{strategy_type}策略。

市场状况：{market_condition}
风险承受能力：{risk_tolerance}

要求：
- 策略逻辑清晰，可回测
- 参数明确，可量化
- 风控严格，符合 Quant Core Team 标准
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"Generating strategy: {strategy_type}")
        response = await self._call_api(messages, temperature=0.7)

        return {
            "success": True,
            "data": {
                "strategy_type": strategy_type,
                "generated_content": response.get("choices", [{}])[0].get("message", {}),
                "raw_response": response
            }
        }

    async def analyze_market(
        self,
        symbols: List[str],
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        AI 市场分析

        Args:
            symbols: 股票代码列表
            analysis_type: 分析类型（comprehensive, technical, fundamental）

        Returns:
            市场分析结果
        """
        system_prompt = f"""你是一个专业的股票市场分析师。请对以下股票进行{analysis_type}分析。

股票代码：{', '.join(symbols)}

分析必须包括：
1. 整体市场趋势判断
2. 个股技术分析（如适用）
3. 风险评估
4. 投资建议（买入/卖出/持有）
5. 置信度评分

请以 JSON 格式返回结果。"""

        user_prompt = f"""请分析以下股票：
{', '.join(symbols)}

分析类型：{analysis_type}

要求：
- 数据驱动分析
- 提供量化指标
- 明确的投资建议
- 符合 Quant Core Team 精度标准"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"Analyzing market: {symbols}")
        response = await self._call_api(messages, temperature=0.5)

        return {
            "success": True,
            "data": {
                "symbols": symbols,
                "analysis_type": analysis_type,
                "analysis_result": response.get("choices", [{}])[0].get("message", {}),
                "raw_response": response
            }
        }

    async def smart_stock_picking(
        self,
        criteria: Dict[str, Any],
        universe: str = "A股全市场",
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        AI 智能选股

        Args:
            criteria: 选股标准
            universe: 股票池范围
            top_n: 返回前 N 只股票

        Returns:
            选股结果
        """
        system_prompt = f"""你是一个专业的股票选股专家。请根据给定的标准进行智能选股。

股票池：{universe}
选股数量：{top_n} 只

选股标准：
{criteria}

要求：
- 基于量化指标
- 考虑风险收益比
- 提供选股理由
- 按优先级排序

请以 JSON 格式返回结果，包含股票代码、名称、评分和理由。"""

        user_prompt = f"""请从 {universe} 中选出 {top_n} 只最佳股票。

选股标准：
{criteria}

请返回：
1. 股票代码
2. 股票名称
3. 综合评分（0-100）
4. 选股理由
5. 风险提示

必须符合 Quant Core Team 的精度和风险控制标准。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"Smart stock picking: {universe}, top {top_n}")
        response = await self._call_api(messages, temperature=0.3)

        return {
            "success": True,
            "data": {
                "universe": universe,
                "top_n": top_n,
                "criteria": criteria,
                "picking_result": response.get("choices", [{}])[0].get("message", {}),
                "raw_response": response
            }
        }

    async def optimize_strategy(
        self,
        current_strategy: str,
        backtest_results: Dict[str, Any],
        optimization_goal: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """
        AI 优化策略

        Args:
            current_strategy: 当前策略描述
            backtest_results: 当前回测结果
            optimization_goal: 优化目标（sharpe_ratio, returns, max_drawdown）

        Returns:
            优化建议
        """
        system_prompt = f"""你是一个专业的量化策略优化专家。请分析当前策略并提供优化建议。

当前策略：
{current_strategy}

回测结果：
{backtest_results}

优化目标：{optimization_goal}

请提供：
1. 策略弱点分析
2. 参数调整建议（具体数值）
3. 风控改进建议
4. 预期改进效果

所有数值必须符合 Quant Core Team 的精度标准（使用 NUMERIC）。
请以 JSON 格式返回。"""

        user_prompt = f"""请优化这个策略，目标是提升 {optimization_goal}。

当前策略描述：
{current_strategy}

回测结果：
- 总收益率：{backtest_results.get('total_return', 'N/A')}
- 最大回撤：{backtest_results.get('max_drawdown', 'N/A')}
- 夏普比率：{backtest_results.get('sharpe_ratio', 'N/A')}

请提供具体的优化建议。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"Optimizing strategy for: {optimization_goal}")
        response = await self._call_api(messages, temperature=0.6)

        return {
            "success": True,
            "data": {
                "current_strategy": current_strategy,
                "optimization_goal": optimization_goal,
                "optimization_suggestions": response.get("choices", [{}])[0].get("message", {}),
                "raw_response": response
            }
        }

    def is_available(self) -> bool:
        """检查 GLM-5 服务是否可用"""
        return bool(self.api_key)


# 创建全局实例
glm5_service = GLM5Service()
