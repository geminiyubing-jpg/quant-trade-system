"""
==============================================
QuantAI Ecosystem - 参数优化引擎
==============================================

支持多种参数优化方法：
- 网格搜索 (Grid Search)
- 随机搜索 (Random Search)
- 贝叶斯优化 (Bayesian Optimization)
- 遗传算法 (Genetic Algorithm)
"""

import logging
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import itertools
import random

logger = logging.getLogger(__name__)


class OptimizationMethod(str, Enum):
    """优化方法"""
    GRID = "grid"               # 网格搜索
    RANDOM = "random"           # 随机搜索
    BAYESIAN = "bayesian"       # 贝叶斯优化
    GENETIC = "genetic"         # 遗传算法


class OptimizationObjective(str, Enum):
    """优化目标"""
    SHARPE_RATIO = "sharpe_ratio"
    TOTAL_RETURN = "total_return"
    MAX_DRAWDOWN = "max_drawdown"
    CALMAR_RATIO = "calmar_ratio"
    SORTINO_RATIO = "sortino_ratio"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"


@dataclass
class ParameterRange:
    """参数范围定义"""
    name: str
    param_type: str  # int, float, categorical
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    values: Optional[List[Any]] = None  # 用于 categorical 类型

    def generate_values(self) -> List[Any]:
        """生成参数值列表"""
        if self.param_type == "categorical":
            return self.values or []

        values = []
        if self.param_type == "int":
            current = int(self.min_value)
            while current <= self.max_value:
                values.append(current)
                current += int(self.step or 1)
        elif self.param_type == "float":
            current = self.min_value
            while current <= self.max_value:
                values.append(round(current, 4))
                current += self.step or 0.1

        return values


@dataclass
class OptimizationResult:
    """优化结果"""
    best_parameters: Dict[str, Any]
    best_score: float
    objective: OptimizationObjective
    method: OptimizationMethod
    all_results: List[Dict[str, Any]] = field(default_factory=list)
    total_combinations: int = 0
    evaluated_combinations: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "best_parameters": self.best_parameters,
            "best_score": self.best_score,
            "objective": self.objective.value,
            "method": self.method.value,
            "total_combinations": self.total_combinations,
            "evaluated_combinations": self.evaluated_combinations,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class BaseOptimizer(ABC):
    """优化器基类"""

    def __init__(
        self,
        objective: OptimizationObjective = OptimizationObjective.SHARPE_RATIO,
        maximize: bool = True
    ):
        self.objective = objective
        self.maximize = maximize

    @abstractmethod
    def optimize(
        self,
        param_ranges: List[ParameterRange],
        evaluate_func: Callable[[Dict[str, Any]], float],
        max_iterations: Optional[int] = None
    ) -> OptimizationResult:
        """执行优化"""
        pass

    def _compare_scores(self, current: float, best: float) -> bool:
        """比较分数，返回 current 是否优于 best"""
        if self.maximize:
            return current > best
        return current < best


class GridSearchOptimizer(BaseOptimizer):
    """网格搜索优化器"""

    def optimize(
        self,
        param_ranges: List[ParameterRange],
        evaluate_func: Callable[[Dict[str, Any]], float],
        max_iterations: Optional[int] = None
    ) -> OptimizationResult:
        """网格搜索"""
        logger.info("开始网格搜索优化")

        # 生成所有参数组合
        all_values = [pr.generate_values() for pr in param_ranges]
        param_names = [pr.name for pr in param_ranges]
        combinations = list(itertools.product(*all_values))

        result = OptimizationResult(
            best_parameters={},
            best_score=float("-inf") if self.maximize else float("inf"),
            objective=self.objective,
            method=OptimizationMethod.GRID,
            total_combinations=len(combinations),
        )

        # 限制迭代次数
        if max_iterations:
            combinations = combinations[:max_iterations]

        # 评估每组参数
        for combo in combinations:
            params = dict(zip(param_names, combo))
            try:
                score = evaluate_func(params)
                result.all_results.append({
                    "parameters": params,
                    "score": score
                })

                if self._compare_scores(score, result.best_score):
                    result.best_score = score
                    result.best_parameters = params

            except Exception as e:
                logger.warning(f"参数评估失败: {params}, 错误: {e}")

            result.evaluated_combinations += 1

        result.finished_at = datetime.utcnow()
        logger.info(f"网格搜索完成，最佳分数: {result.best_score}")

        return result


class RandomSearchOptimizer(BaseOptimizer):
    """随机搜索优化器"""

    def optimize(
        self,
        param_ranges: List[ParameterRange],
        evaluate_func: Callable[[Dict[str, Any]], float],
        max_iterations: Optional[int] = None
    ) -> OptimizationResult:
        """随机搜索"""
        max_iterations = max_iterations or 100
        logger.info(f"开始随机搜索优化，迭代次数: {max_iterations}")

        result = OptimizationResult(
            best_parameters={},
            best_score=float("-inf") if self.maximize else float("inf"),
            objective=self.objective,
            method=OptimizationMethod.RANDOM,
            total_combinations=max_iterations,
        )

        for i in range(max_iterations):
            # 随机采样参数
            params = {}
            for pr in param_ranges:
                values = pr.generate_values()
                params[pr.name] = random.choice(values)

            try:
                score = evaluate_func(params)
                result.all_results.append({
                    "parameters": params,
                    "score": score,
                    "iteration": i
                })

                if self._compare_scores(score, result.best_score):
                    result.best_score = score
                    result.best_parameters = params

            except Exception as e:
                logger.warning(f"参数评估失败: {params}, 错误: {e}")

            result.evaluated_combinations += 1

        result.finished_at = datetime.utcnow()
        logger.info(f"随机搜索完成，最佳分数: {result.best_score}")

        return result


class BayesianOptimizer(BaseOptimizer):
    """贝叶斯优化器"""

    def optimize(
        self,
        param_ranges: List[ParameterRange],
        evaluate_func: Callable[[Dict[str, Any]], float],
        max_iterations: Optional[int] = None
    ) -> OptimizationResult:
        """贝叶斯优化"""
        max_iterations = max_iterations or 50
        logger.info(f"开始贝叶斯优化，迭代次数: {max_iterations}")

        result = OptimizationResult(
            best_parameters={},
            best_score=float("-inf") if self.maximize else float("inf"),
            objective=self.objective,
            method=OptimizationMethod.BAYESIAN,
            total_combinations=max_iterations,
        )

        # 初始随机采样
        n_initial = min(10, max_iterations // 2)
        param_names = [pr.name for pr in param_ranges]

        # 存储已评估的点
        X = []  # 参数空间
        y = []  # 目标值

        for i in range(max_iterations):
            if i < n_initial:
                # 初始随机采样
                params = {}
                for pr in param_ranges:
                    values = pr.generate_values()
                    params[pr.name] = random.choice(values)
            else:
                # 使用采集函数选择下一个点
                params = self._acquisition_function(
                    X, y, param_ranges, param_names
                )

            try:
                score = evaluate_func(params)

                # 记录结果
                x_vec = [params[name] for name in param_names]
                X.append(x_vec)
                y.append(score)

                result.all_results.append({
                    "parameters": params,
                    "score": score,
                    "iteration": i
                })

                if self._compare_scores(score, result.best_score):
                    result.best_score = score
                    result.best_parameters = params

            except Exception as e:
                logger.warning(f"参数评估失败: {params}, 错误: {e}")

            result.evaluated_combinations += 1

        result.finished_at = datetime.utcnow()
        logger.info(f"贝叶斯优化完成，最佳分数: {result.best_score}")

        return result

    def _acquisition_function(
        self,
        X: List,
        y: List,
        param_ranges: List[ParameterRange],
        param_names: List[str]
    ) -> Dict[str, Any]:
        """采集函数 - 选择下一个评估点"""
        # 简化实现：使用期望改进 (EI)
        # 实际应用中应使用高斯过程回归

        # 这里使用随机选择作为简化实现
        params = {}
        for pr in param_ranges:
            values = pr.generate_values()
            params[pr.name] = random.choice(values)

        return params


class GeneticOptimizer(BaseOptimizer):
    """遗传算法优化器"""

    def __init__(
        self,
        objective: OptimizationObjective = OptimizationObjective.SHARPE_RATIO,
        maximize: bool = True,
        population_size: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elite_size: int = 5
    ):
        super().__init__(objective, maximize)
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size

    def optimize(
        self,
        param_ranges: List[ParameterRange],
        evaluate_func: Callable[[Dict[str, Any]], float],
        max_iterations: Optional[int] = None
    ) -> OptimizationResult:
        """遗传算法优化"""
        max_iterations = max_iterations or 100
        logger.info(f"开始遗传算法优化，代数: {max_iterations}")

        result = OptimizationResult(
            best_parameters={},
            best_score=float("-inf") if self.maximize else float("inf"),
            objective=self.objective,
            method=OptimizationMethod.GENETIC,
            total_combinations=max_iterations * self.population_size,
        )

        param_names = [pr.name for pr in param_ranges]

        # 初始化种群
        population = self._init_population(param_ranges, param_names)

        for generation in range(max_iterations):
            # 评估适应度
            fitness_scores = []
            for individual in population:
                try:
                    score = evaluate_func(individual)
                    fitness_scores.append((individual, score))

                    result.all_results.append({
                        "parameters": individual,
                        "score": score,
                        "generation": generation
                    })

                    if self._compare_scores(score, result.best_score):
                        result.best_score = score
                        result.best_parameters = individual.copy()

                except Exception as e:
                    fitness_scores.append((individual, float("-inf") if self.maximize else float("inf")))

            result.evaluated_combinations += len(population)

            # 选择
            selected = self._selection(fitness_scores)

            # 交叉
            offspring = self._crossover(selected, param_ranges)

            # 变异
            population = self._mutation(offspring, param_ranges)

            # 保留精英
            sorted_fitness = sorted(
                fitness_scores,
                key=lambda x: x[1],
                reverse=self.maximize
            )
            for i in range(min(self.elite_size, len(sorted_fitness))):
                population[i] = sorted_fitness[i][0]

        result.finished_at = datetime.utcnow()
        logger.info(f"遗传算法完成，最佳分数: {result.best_score}")

        return result

    def _init_population(
        self,
        param_ranges: List[ParameterRange],
        param_names: List[str]
    ) -> List[Dict[str, Any]]:
        """初始化种群"""
        population = []
        for _ in range(self.population_size):
            individual = {}
            for pr in param_ranges:
                values = pr.generate_values()
                individual[pr.name] = random.choice(values)
            population.append(individual)
        return population

    def _selection(
        self,
        fitness_scores: List[Tuple[Dict, float]]
    ) -> List[Dict[str, Any]]:
        """选择操作 - 锦标赛选择"""
        selected = []
        sorted_fitness = sorted(
            fitness_scores,
            key=lambda x: x[1],
            reverse=self.maximize
        )

        for _ in range(self.population_size - self.elite_size):
            # 锦标赛选择
            tournament = random.sample(fitness_scores, min(3, len(fitness_scores)))
            winner = max(tournament, key=lambda x: x[1]) if self.maximize else min(tournament, key=lambda x: x[1])
            selected.append(winner[0].copy())

        return selected

    def _crossover(
        self,
        population: List[Dict[str, Any]],
        param_ranges: List[ParameterRange]
    ) -> List[Dict[str, Any]]:
        """交叉操作"""
        offspring = []

        for i in range(0, len(population) - 1, 2):
            parent1 = population[i]
            parent2 = population[i + 1]

            if random.random() < self.crossover_rate:
                # 单点交叉
                child1, child2 = {}, {}
                crossover_point = random.randint(1, len(param_ranges) - 1)

                for j, pr in enumerate(param_ranges):
                    if j < crossover_point:
                        child1[pr.name] = parent1[pr.name]
                        child2[pr.name] = parent2[pr.name]
                    else:
                        child1[pr.name] = parent2[pr.name]
                        child2[pr.name] = parent1[pr.name]

                offspring.extend([child1, child2])
            else:
                offspring.extend([parent1.copy(), parent2.copy()])

        return offspring

    def _mutation(
        self,
        population: List[Dict[str, Any]],
        param_ranges: List[ParameterRange]
    ) -> List[Dict[str, Any]]:
        """变异操作"""
        for individual in population:
            for pr in param_ranges:
                if random.random() < self.mutation_rate:
                    values = pr.generate_values()
                    individual[pr.name] = random.choice(values)

        return population


class ParameterOptimizer:
    """
    参数优化器

    统一接口，支持多种优化方法
    """

    def __init__(
        self,
        method: OptimizationMethod = OptimizationMethod.GRID,
        objective: OptimizationObjective = OptimizationObjective.SHARPE_RATIO,
        maximize: bool = True
    ):
        self.method = method
        self.objective = objective
        self.maximize = maximize

        # 创建优化器
        self._optimizer = self._create_optimizer()

    def _create_optimizer(self) -> BaseOptimizer:
        """创建优化器实例"""
        optimizers = {
            OptimizationMethod.GRID: GridSearchOptimizer,
            OptimizationMethod.RANDOM: RandomSearchOptimizer,
            OptimizationMethod.BAYESIAN: BayesianOptimizer,
            OptimizationMethod.GENETIC: GeneticOptimizer,
        }

        optimizer_class = optimizers.get(self.method, GridSearchOptimizer)
        return optimizer_class(self.objective, self.maximize)

    def optimize(
        self,
        param_ranges: List[ParameterRange],
        evaluate_func: Callable[[Dict[str, Any]], float],
        max_iterations: Optional[int] = None
    ) -> OptimizationResult:
        """
        执行参数优化

        Args:
            param_ranges: 参数范围定义
            evaluate_func: 评估函数，接收参数字典，返回目标值
            max_iterations: 最大迭代次数

        Returns:
            OptimizationResult: 优化结果
        """
        logger.info(f"开始参数优化，方法: {self.method.value}, 目标: {self.objective.value}")

        return self._optimizer.optimize(
            param_ranges=param_ranges,
            evaluate_func=evaluate_func,
            max_iterations=max_iterations
        )

    @staticmethod
    def create_param_range(
        name: str,
        param_type: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: Optional[float] = None,
        values: Optional[List[Any]] = None
    ) -> ParameterRange:
        """创建参数范围的便捷方法"""
        return ParameterRange(
            name=name,
            param_type=param_type,
            min_value=min_value,
            max_value=max_value,
            step=step,
            values=values
        )
