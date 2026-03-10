"""
策略进化 API 端点

提供遗传算法优化、贝叶斯优化和 AI 分析等策略进化功能。
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
import asyncio
from datetime import datetime

from src.services.strategy.evolution import (
    evolution_engine,
    GeneticOptimizer,
    BayesianOptimizer,
    EvolutionResult,
    BayesianOptimizationResult
)


router = APIRouter(prefix="/evolution", tags=["Strategy Evolution"])


# ========================================
# Pydantic 模型
# ========================================

class ParameterBounds(BaseModel):
    """参数边界"""
    min: float = Field(..., description="最小值")
    max: float = Field(..., description="最大值")


class GeneticOptimizationRequest(BaseModel):
    """遗传算法优化请求"""
    param_bounds: Dict[str, ParameterBounds] = Field(
        ...,
        description="参数边界 {name: {min, max}}"
    )
    population_size: int = Field(default=50, ge=10, le=200, description="种群大小")
    generations: int = Field(default=100, ge=10, le=500, description="迭代次数")
    elite_size: int = Field(default=5, ge=1, le=20, description="精英数量")
    mutation_rate: float = Field(default=0.1, ge=0.01, le=0.5, description="变异率")
    crossover_rate: float = Field(default=0.8, ge=0.1, le=1.0, description="交叉率")
    selection_method: str = Field(default="tournament", description="选择方法")
    strategy_id: Optional[str] = Field(default=None, description="策略ID（可选）")


class BayesianOptimizationRequest(BaseModel):
    """贝叶斯优化请求"""
    param_bounds: Dict[str, ParameterBounds] = Field(
        ...,
        description="参数边界 {name: {min, max}}"
    )
    n_iterations: int = Field(default=50, ge=10, le=200, description="迭代次数")
    n_initial: int = Field(default=5, ge=2, le=20, description="初始采样次数")
    mode: str = Field(default="maximize", description="优化模式 (maximize/minimize)")
    strategy_id: Optional[str] = Field(default=None, description="策略ID（可选）")


class AIOptimizationRequest(BaseModel):
    """AI 优化分析请求"""
    strategy_code: str = Field(..., description="策略代码")
    backtest_results: Dict[str, Any] = Field(..., description="回测结果")
    optimization_goal: str = Field(default="sharpe_ratio", description="优化目标")


# ========================================
# 模拟回测函数（用于演示）
# ========================================

def create_mock_backtest_function(
    param_bounds: Dict[str, Tuple[float, float]]
) -> callable:
    """
    创建模拟回测函数

    实际使用时应该替换为真实的回测函数。
    """
    def mock_backtest(params: Dict[str, float]) -> float:
        """
        模拟回测函数

        基于参数生成一个模拟的适应度值。
        实际使用时应该调用真实的回测引擎。
        """
        # 模拟：参数越接近某个"最优值"，适应度越高
        optimal_values = {
            "ma_short": 5.0,
            "ma_long": 20.0,
            "rsi_period": 14.0,
            "rsi_oversold": 30.0,
            "rsi_overbought": 70.0,
            "stop_loss": 0.05,
            "take_profit": 0.15,
        }

        total_distance = 0.0
        for name, value in params.items():
            if name in optimal_values:
                # 计算与最优值的归一化距离
                min_val, max_val = param_bounds.get(name, (0, 100))
                range_size = max_val - min_val
                if range_size > 0:
                    distance = abs(value - optimal_values[name]) / range_size
                    total_distance += distance

        # 转换为适应度（距离越小，适应度越高）
        avg_distance = total_distance / len(params) if params else 0.5
        fitness = 1.0 - avg_distance

        # 添加一些随机噪声
        import random
        noise = random.uniform(-0.1, 0.1)

        return max(0.0, min(1.0, fitness + noise))

    return mock_backtest


# ========================================
# 存储优化任务状态
# ========================================

optimization_tasks: Dict[str, Dict[str, Any]] = {}


# ========================================
# API 端点
# ========================================

@router.post("/genetic/start", summary="启动遗传算法优化")
async def start_genetic_optimization(
    request: GeneticOptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    启动遗传算法优化

    使用遗传算法优化策略参数。

    - **param_bounds**: 参数边界，格式：{"param_name": {"min": 0, "max": 100}}
    - **population_size**: 种群大小（10-200）
    - **generations**: 迭代次数（10-500）
    - **elite_size**: 精英数量
    - **mutation_rate**: 变异率
    - **crossover_rate**: 交叉率

    返回优化任务 ID，可通过 /evolution/status/{task_id} 查询进度。
    """
    import uuid
    task_id = str(uuid.uuid4())

    # 转换参数边界格式
    param_bounds = {
        name: (bounds.min, bounds.max)
        for name, bounds in request.param_bounds.items()
    }

    # 创建回测函数
    backtest_function = create_mock_backtest_function(param_bounds)

    # 初始化任务状态
    optimization_tasks[task_id] = {
        "type": "genetic",
        "status": "running",
        "progress": 0,
        "result": None,
        "started_at": datetime.utcnow(),
        "request": request.dict()
    }

    # 后台执行优化
    async def run_optimization():
        try:
            result = evolution_engine.optimize_with_genetic(
                backtest_function=backtest_function,
                param_bounds=param_bounds,
                population_size=request.population_size,
                generations=request.generations,
                elite_size=request.elite_size,
                mutation_rate=request.mutation_rate,
                crossover_rate=request.crossover_rate,
                selection_method=request.selection_method
            )

            optimization_tasks[task_id]["status"] = "completed"
            optimization_tasks[task_id]["progress"] = 100
            optimization_tasks[task_id]["result"] = {
                "best_params": result.best_params,
                "best_fitness": float(result.best_fitness),
                "generations": result.generations,
                "fitness_history": [float(f) for f in result.fitness_history[-20:]],  # 只保留最后20个
                "all_results": result.all_results[:5]  # 只保留前5个
            }
            optimization_tasks[task_id]["completed_at"] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Genetic optimization failed: {e}")
            optimization_tasks[task_id]["status"] = "failed"
            optimization_tasks[task_id]["error"] = str(e)

    background_tasks.add_task(run_optimization)

    return {
        "success": True,
        "task_id": task_id,
        "message": "Genetic optimization started",
        "estimated_time": f"{request.generations * 0.5:.0f} seconds"
    }


@router.post("/bayesian/start", summary="启动贝叶斯优化")
async def start_bayesian_optimization(
    request: BayesianOptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    启动贝叶斯优化

    使用贝叶斯方法优化策略参数，适合评估代价高的场景。

    - **param_bounds**: 参数边界
    - **n_iterations**: 迭代次数（10-200）
    - **n_initial**: 初始随机采样次数
    - **mode**: 优化模式（maximize/minimize）

    返回优化任务 ID。
    """
    import uuid
    task_id = str(uuid.uuid4())

    # 转换参数边界格式
    param_bounds = {
        name: (bounds.min, bounds.max)
        for name, bounds in request.param_bounds.items()
    }

    # 创建回测函数
    backtest_function = create_mock_backtest_function(param_bounds)

    # 初始化任务状态
    optimization_tasks[task_id] = {
        "type": "bayesian",
        "status": "running",
        "progress": 0,
        "result": None,
        "started_at": datetime.utcnow(),
        "request": request.dict()
    }

    # 后台执行优化
    async def run_optimization():
        try:
            result = evolution_engine.optimize_with_bayesian(
                backtest_function=backtest_function,
                param_bounds=param_bounds,
                n_iterations=request.n_iterations,
                mode=request.mode
            )

            optimization_tasks[task_id]["status"] = "completed"
            optimization_tasks[task_id]["progress"] = 100
            optimization_tasks[task_id]["result"] = {
                "best_params": result.best_params,
                "best_value": float(result.best_value),
                "iterations": result.iterations,
                "exploration_points": result.exploration_points[-10:]  # 保留最后10个
            }
            optimization_tasks[task_id]["completed_at"] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Bayesian optimization failed: {e}")
            optimization_tasks[task_id]["status"] = "failed"
            optimization_tasks[task_id]["error"] = str(e)

    background_tasks.add_task(run_optimization)

    return {
        "success": True,
        "task_id": task_id,
        "message": "Bayesian optimization started",
        "estimated_time": f"{request.n_iterations * 0.3:.0f} seconds"
    }


@router.post("/ai/analyze", summary="AI 分析回测结果")
async def ai_analyze_backtest(request: AIOptimizationRequest):
    """
    AI 分析回测结果

    使用 AI 分析策略的回测结果，并提供优化建议。

    - **strategy_code**: 策略代码
    - **backtest_results**: 回测结果（JSON 格式）
    - **optimization_goal**: 优化目标（如：sharpe_ratio, total_return）

    返回：
    - 策略弱点分析
    - 参数调整建议
    - 风控改进建议
    - 预期改进效果
    """
    try:
        result = await evolution_engine.optimize_with_ai(
            strategy_code=request.strategy_code,
            backtest_results=request.backtest_results,
            optimization_goal=request.optimization_goal
        )

        return {
            "success": result["success"],
            "data": result
        }

    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", summary="查询优化任务状态")
async def get_optimization_status(task_id: str):
    """
    查询优化任务状态

    - **task_id**: 任务 ID

    返回任务状态和结果（如果已完成）。
    """
    if task_id not in optimization_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = optimization_tasks[task_id]

    response = {
        "task_id": task_id,
        "type": task["type"],
        "status": task["status"],
        "progress": task["progress"],
        "started_at": task["started_at"].isoformat(),
    }

    if task["status"] == "completed":
        response["result"] = task["result"]
        response["completed_at"] = task["completed_at"].isoformat()

    elif task["status"] == "failed":
        response["error"] = task.get("error", "Unknown error")

    return response


@router.get("/history", summary="获取优化历史")
async def get_optimization_history():
    """
    获取优化历史

    返回所有已完成的优化任务列表。
    """
    completed_tasks = [
        {
            "task_id": task_id,
            "type": task["type"],
            "status": task["status"],
            "started_at": task["started_at"].isoformat(),
            "completed_at": task.get("completed_at", {}).isoformat() if task.get("completed_at") else None,
            "best_fitness": task.get("result", {}).get("best_fitness") or task.get("result", {}).get("best_value")
        }
        for task_id, task in optimization_tasks.items()
        if task["status"] in ["completed", "failed"]
    ]

    return {
        "success": True,
        "data": {
            "total_tasks": len(optimization_tasks),
            "completed_tasks": completed_tasks
        }
    }


@router.get("/summary", summary="获取进化引擎摘要")
async def get_evolution_summary():
    """
    获取进化引擎摘要

    返回遗传算法和贝叶斯优化的历史统计信息。
    """
    summary = evolution_engine.get_evolution_summary()

    return {
        "success": True,
        "data": summary
    }


@router.delete("/task/{task_id}", summary="删除优化任务")
async def delete_optimization_task(task_id: str):
    """
    删除优化任务

    - **task_id**: 任务 ID
    """
    if task_id not in optimization_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = optimization_tasks[task_id]

    if task["status"] == "running":
        raise HTTPException(status_code=400, detail="Cannot delete running task")

    del optimization_tasks[task_id]

    return {
        "success": True,
        "message": f"Task {task_id} deleted"
    }


@router.post("/quick-test", summary="快速测试优化")
async def quick_test_optimization():
    """
    快速测试优化功能

    使用预设参数快速测试遗传算法优化功能。
    """
    import uuid
    task_id = str(uuid.uuid4())

    # 预设参数边界
    param_bounds = {
        "ma_short": (5.0, 20.0),
        "ma_long": (20.0, 60.0),
        "rsi_period": (7.0, 21.0),
        "stop_loss": (0.02, 0.10),
        "take_profit": (0.05, 0.30),
    }

    # 创建回测函数
    backtest_function = create_mock_backtest_function(param_bounds)

    # 初始化任务状态
    optimization_tasks[task_id] = {
        "type": "genetic",
        "status": "running",
        "progress": 0,
        "result": None,
        "started_at": datetime.utcnow(),
        "request": {"test": True}
    }

    # 后台执行优化（使用较小的参数）
    async def run_quick_test():
        try:
            result = evolution_engine.optimize_with_genetic(
                backtest_function=backtest_function,
                param_bounds=param_bounds,
                population_size=20,
                generations=10
            )

            optimization_tasks[task_id]["status"] = "completed"
            optimization_tasks[task_id]["progress"] = 100
            optimization_tasks[task_id]["result"] = {
                "best_params": result.best_params,
                "best_fitness": float(result.best_fitness),
                "generations": result.generations,
                "fitness_history": [float(f) for f in result.fitness_history]
            }
            optimization_tasks[task_id]["completed_at"] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Quick test failed: {e}")
            optimization_tasks[task_id]["status"] = "failed"
            optimization_tasks[task_id]["error"] = str(e)

    # 同步执行快速测试（因为是测试，不需要后台任务）
    await run_quick_test()

    return {
        "success": True,
        "task_id": task_id,
        "result": optimization_tasks[task_id]["result"],
        "message": "Quick test completed"
    }
