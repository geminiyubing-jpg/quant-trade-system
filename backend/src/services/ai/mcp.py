"""
智谱 MCP (Model Context Protocol) 服务模块

支持 GLM-5 的工具调用功能，实现 AI 与量化系统的深度集成。
"""

from typing import Dict, List, Any, Optional
from loguru import logger
import json
from decimal import Decimal

from src.core.config import settings


class MCPTool:
    """MCP 工具基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        raise NotImplementedError


class GetStockPriceTool(MCPTool):
    """获取股票价格工具"""

    def __init__(self):
        super().__init__(
            name="get_stock_price",
            description="获取股票实时价格数据"
        )

    async def execute(
        self,
        symbol: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        获取股票价格

        Args:
            symbol: 股票代码
            fields: 需要的字段列表

        Returns:
            股票价格数据
        """
        # 这里应该连接到数据库或 API
        # 暂时返回模拟数据
        from src.models.stock import StockPrice
        from src.core.database import AsyncSessionLocal
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            # 获取最新价格
            stmt = select(StockPrice).where(
                StockPrice.symbol == symbol
            ).order_by(
                StockPrice.timestamp.desc()
            ).limit(1)

            result = await session.execute(stmt)
            price_data = result.fetchone()

            if not price_data:
                return {
                    "success": False,
                    "error": f"找不到股票 {symbol} 的价格数据"
                }

            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "price_close": float(price_data.price_close),
                    "timestamp": price_data.timestamp.isoformat(),
                }
            }


class ExecuteBacktestTool(MCPTool):
    """执行回测工具"""

    def __init__(self):
        super().__init__(
            name="execute_backtest",
            description="执行策略回测"
        )

    async def execute(
        self,
        strategy_name: str,
        start_date: str,
        end_date: str,
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        执行回测

        Args:
            strategy_name: 策略名称
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金

        Returns:
            回测结果
        """
        # 这里应该调用回测引擎
        # 暂时返回模拟结果
        return {
            "success": True,
            "data": {
                "strategy_name": strategy_name,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "final_capital": initial_capital * 1.15,  # 模拟 15% 收益
                "total_return": 0.15,
                "max_drawdown": 0.08,
                "sharpe_ratio": 1.2,
                "status": "completed"
            }
        }


class GetPortfolioInfoTool(MCPTool):
    """获取投资组合信息工具"""

    def __init__(self):
        super().__init__(
            name="get_portfolio_info",
            description="获取当前投资组合信息"
        )

    async def execute(self) -> Dict[str, Any]:
        """
        获取投资组合信息

        Returns:
            投资组合数据
        """
        # 这里应该连接到数据库
        # 暂时返回模拟数据
        return {
            "success": True,
            "data": {
                "total_value": 1000000.0,
                "total_pnl": 50000.0,
                "positions": [
                    {
                        "symbol": "000001.SZ",
                        "quantity": 1000,
                        "avg_price": 10.50,
                        "current_price": 11.25,
                        "market_value": 11250.0,
                        "unrealized_pnl": 750.0
                    }
                ]
            }
        }


class MCPService:
    """MCP 服务管理器"""

    def __init__(self):
        """初始化 MCP 服务"""
        # 注册所有工具
        self.tools = {
            "get_stock_price": GetStockPriceTool(),
            "execute_backtest": ExecuteBacktestTool(),
            "get_portfolio_info": GetPortfolioInfoTool(),
        }

    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """获取指定工具"""
        return self.tools.get(tool_name)

    def get_all_tools(self) -> Dict[str, MCPTool]:
        """获取所有工具"""
        return self.tools

    def format_tools_for_glm(self) -> List[Dict[str, Any]]:
        """
        格式化工具列表供 GLM-5 使用

        Returns:
            GLM-5 函数调用格式的工具列表
        """
        tools = []
        for tool_name, tool in self.tools.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "股票代码"
                            },
                            "fields": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "需要的字段"
                            }
                        },
                        "required": ["symbol"]
                    }
                }
            })

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行指定工具

        Args:
            tool_name: 工具名称
            parameters: 工具参数

        Returns:
            工具执行结果
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"工具 {tool_name} 不存在"
            }

        try:
            logger.info(f"Executing MCP tool: {tool_name} with params: {parameters}")
            result = await tool.execute(**parameters)
            return result

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


async def generate_strategy_with_tools(
    user_prompt: str,
    available_tools: List[str] = None
) -> Dict[str, Any]:
    """
    使用 MCP 工具生成策略（GLM-5 + 工具调用）

    Args:
        user_prompt: 用户提示
        available_tools: 可用工具列表

    Returns:
        生成的策略和工具调用结果
    """
    from .glm import glm5_service

    system_prompt = """你是一个专业的量化交易策略专家。用户会给你一个任务，你可以使用以下工具来完成任务：

可用工具：
1. get_stock_price - 获取股票实时价格
2. execute_backtest - 执行策略回测
3. get_portfolio_info - 获取投资组合信息

请根据用户需求：
1. 分析需求
2. 选择合适的工具
3. 调用工具获取数据
4. 基于数据生成策略
5. 确保策略符合 Quant Core Team 的精度和风控标准

请以 JSON 格式返回最终的策略和工具调用结果。
"""

    mcp_service = MCPService()

    # 构建工具列表
    tools = mcp_service.format_tools_for_glm()

    # 添加到消息中
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"{user_prompt}\n\n可用工具：{json.dumps(tools, ensure_ascii=False, indent=2)}"
        }
    ]

    # 调用 GLM-5（带工具调用）
    response = await glm5_service._call_api(
        messages=messages,
        temperature=0.7
    )

    return {
        "success": True,
        "data": {
            "user_prompt": user_prompt,
            "glm_response": response,
            "tools_used": tools
        }
    }


# 创建全局实例
mcp_service = MCPService()
