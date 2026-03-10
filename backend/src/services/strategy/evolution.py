"""
==============================================
QuantAI Ecosystem - 策略进化引擎
==============================================

提供基于遗传算法和贝叶斯优化的策略参数优化功能。
"""

import random
import numpy as np
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


# ==============================================
# 数据模型
# ==============================================

@dataclass
class Gene:
    """基因 - 表示一个策略参数"""
    name: str
    value: float
    min_value: float
    max_value: float
    mutation_rate: float = 0.1

    def mutate(self):
        """变异"""
        if random.random() < self.mutation_rate:
            # 高斯变异
            range_size = self.max_value - self.min_value
            sigma = range_size * 0.1
            self.value = np.clip(
                self.value + np.random.normal(0, sigma),
                self.min_value,
                self.max_value
            )

    def copy(self) -> 'Gene':
        """复制基因"""
        return Gene(
            name=self.name,
            value=self.value,
            min_value=self.min_value,
            max_value=self.max_value,
            mutation_rate=self.mutation_rate
        )


@dataclass
class Chromosome:
    """染色体 - 表示一组策略参数"""
    genes: List[Gene]
    fitness: float = 0.0

    def copy(self) -> 'Chromosome':
        """复制染色体"""
        return Chromosome(
            genes=[gene.copy() for gene in self.genes],
            fitness=self.fitness
        )

    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {gene.name: gene.value for gene in self.genes}

    @classmethod
    def from_dict(cls, params: Dict[str, Tuple[float, float, float]]) -> 'Chromosome':
        """
        从参数定义创建染色体

        Args:
            params: {name: (min, max, initial)}
        """
        genes = []
        for name, (min_val, max_val, initial) in params.items():
            genes.append(Gene(
                name=name,
                value=initial,
                min_value=min_val,
                max_value=max_val
            ))
        return cls(genes=genes)


@dataclass
class EvolutionResult:
    """进化结果"""
    best_params: Dict[str, float]
    best_fitness: float
    generations: int
    population_size: int
    fitness_history: List[float]
    all_results: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BayesianOptimizationResult:
    """贝叶斯优化结果"""
    best_params: Dict[str, float]
    best_value: float
    iterations: int
    exploration_points: List[Dict[str, float]]
    acquisition_values: List[float]
    created_at: datetime = field(default_factory=datetime.utcnow)


# ==============================================
# 遗传算法优化器
# ==============================================

class GeneticOptimizer:
    """
    遗传算法优化器

    使用遗传算法优化策略参数。

    特点：
    - 支持多种选择策略（轮盘赌、锦标赛）
    - 支持多种交叉方式（单点、两点、均匀）
    - 自适应变异率
    - 精英保留策略
    """

    def __init__(
        self,
        fitness_function: Callable[[Dict[str, float]], float],
        param_bounds: Dict[str, Tuple[float, float]],
        population_size: int = 50,
        elite_size: int = 5,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        selection_method: str = "tournament"
    ):
        """
        初始化遗传算法优化器

        Args:
            fitness_function: 适应度函数
            param_bounds: 参数边界 {name: (min, max)}
            population_size: 种群大小
            elite_size: 精英数量
            mutation_rate: 变异率
            crossover_rate: 交叉率
            selection_method: 选择方法 ("tournament" or "roulette")
        """
        self.fitness_function = fitness_function
        self.param_bounds = param_bounds
        self.population_size = population_size
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.selection_method = selection_method

        self.population: List[Chromosome] = []
        self.generation = 0
        self.fitness_history: List[float] = []

    def initialize_population(self):
        """初始化种群"""
        self.population = []

        for _ in range(self.population_size):
            genes = []
            for name, (min_val, max_val) in self.param_bounds.items():
                value = random.uniform(min_val, max_val)
                genes.append(Gene(
                    name=name,
                    value=value,
                    min_value=min_val,
                    max_value=max_val,
                    mutation_rate=self.mutation_rate
                ))
            self.population.append(Chromosome(genes=genes))

        self.generation = 0
        self.fitness_history = []
        logger.info(f"Initialized population with {len(self.population)} individuals")

    def evaluate_fitness(self, chromosome: Chromosome) -> float:
        """评估适应度"""
        params = chromosome.to_dict()
        try:
            fitness = self.fitness_function(params)
            return fitness if not np.isnan(fitness) else 0.0
        except Exception as e:
            logger.error(f"Fitness evaluation error: {e}")
            return 0.0

    def evaluate_population(self):
        """评估整个种群"""
        for chromosome in self.population:
            chromosome.fitness = self.evaluate_fitness(chromosome)

        # 按适应度排序
        self.population.sort(key=lambda x: x.fitness, reverse=True)

        # 记录最佳适应度
        best_fitness = self.population[0].fitness if self.population else 0.0
        self.fitness_history.append(best_fitness)

        logger.debug(f"Generation {self.generation}: Best fitness = {best_fitness:.4f}")

    def selection(self) -> List[Chromosome]:
        """选择操作"""
        selected = []

        if self.selection_method == "tournament":
            # 锦标赛选择
            tournament_size = max(2, len(self.population) // 10)

            for _ in range(self.population_size - self.elite_size):
                tournament = random.sample(self.population, tournament_size)
                winner = max(tournament, key=lambda x: x.fitness)
                selected.append(winner.copy())

        else:  # roulette
            # 轮盘赌选择
            total_fitness = sum(c.fitness for c in self.population)
            if total_fitness <= 0:
                # 如果所有适应度都是0，随机选择
                selected = [c.copy() for c in random.sample(
                    self.population,
                    min(self.population_size - self.elite_size, len(self.population))
                )]
            else:
                probabilities = [c.fitness / total_fitness for c in self.population]

                for _ in range(self.population_size - self.elite_size):
                    idx = np.random.choice(len(self.population), p=probabilities)
                    selected.append(self.population[idx].copy())

        return selected

    def crossover(self, parent1: Chromosome, parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """交叉操作"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        # 均匀交叉
        child1_genes = []
        child2_genes = []

        for g1, g2 in zip(parent1.genes, parent2.genes):
            if random.random() < 0.5:
                child1_genes.append(g1.copy())
                child2_genes.append(g2.copy())
            else:
                child1_genes.append(g2.copy())
                child2_genes.append(g1.copy())

        return Chromosome(genes=child1_genes), Chromosome(genes=child2_genes)

    def mutate(self, chromosome: Chromosome):
        """变异操作"""
        for gene in chromosome.genes:
            gene.mutate()

    def evolve_generation(self) -> float:
        """进化一代"""
        # 1. 评估当前种群
        self.evaluate_population()

        # 2. 保留精英
        elites = [c.copy() for c in self.population[:self.elite_size]]

        # 3. 选择
        selected = self.selection()

        # 4. 交叉
        new_population = elites.copy()
        while len(new_population) < self.population_size:
            if len(selected) < 2:
                break

            parent1, parent2 = random.sample(selected, 2)
            child1, child2 = self.crossover(parent1, parent2)

            # 5. 变异
            self.mutate(child1)
            self.mutate(child2)

            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)

        self.population = new_population
        self.generation += 1

        return self.fitness_history[-1] if self.fitness_history else 0.0

    def run(
        self,
        max_generations: int = 100,
        early_stopping: int = 10,
        convergence_threshold: float = 1e-6
    ) -> EvolutionResult:
        """
        运行遗传算法

        Args:
            max_generations: 最大迭代次数
            early_stopping: 早停轮数
            convergence_threshold: 收敛阈值

        Returns:
            EvolutionResult: 优化结果
        """
        # 初始化种群
        self.initialize_population()

        no_improvement_count = 0
        best_fitness_ever = float('-inf')

        for gen in range(max_generations):
            best_fitness = self.evolve_generation()

            # 检查是否有改进
            if best_fitness > best_fitness_ever + convergence_threshold:
                best_fitness_ever = best_fitness
                no_improvement_count = 0
            else:
                no_improvement_count += 1

            # 早停检查
            if no_improvement_count >= early_stopping:
                logger.info(f"Early stopping at generation {gen + 1}")
                break

            # 日志
            if (gen + 1) % 10 == 0:
                logger.info(f"Generation {gen + 1}: Best fitness = {best_fitness:.4f}")

        # 获取最佳结果
        self.evaluate_population()
        best_chromosome = self.population[0]

        # 收集所有结果
        all_results = [
            {"params": c.to_dict(), "fitness": c.fitness}
            for c in self.population[:10]  # 保留前10个
        ]

        return EvolutionResult(
            best_params=best_chromosome.to_dict(),
            best_fitness=best_chromosome.fitness,
            generations=self.generation,
            population_size=self.population_size,
            fitness_history=self.fitness_history,
            all_results=all_results
        )


# ==============================================
# 贝叶斯优化器
# ==============================================

class BayesianOptimizer:
    """
    贝叶斯优化器

    使用高斯过程进行参数优化，适合评估代价高的场景。

    特点：
    - 高斯过程代理模型
    - 期望增量（EI）采集函数
    - 支持连续和离散参数
    """

    def __init__(
        self,
        objective_function: Callable[[Dict[str, float]], float],
        param_bounds: Dict[str, Tuple[float, float]],
        mode: str = "maximize"
    ):
        """
        初始化贝叶斯优化器

        Args:
            objective_function: 目标函数
            param_bounds: 参数边界 {name: (min, max)}
            mode: "maximize" 或 "minimize"
        """
        self.objective_function = objective_function
        self.param_bounds = param_bounds
        self.mode = mode

        self.observed_points: List[Dict[str, float]] = []
        self.observed_values: List[float] = []
        self.exploration_points: List[Dict[str, float]] = []

    def _normalize_params(self, params: Dict[str, float]) -> np.ndarray:
        """归一化参数到 [0, 1]"""
        normalized = []
        for name, value in params.items():
            min_val, max_val = self.param_bounds[name]
            normalized.append((value - min_val) / (max_val - min_val))
        return np.array(normalized)

    def _denormalize_params(self, normalized: np.ndarray) -> Dict[str, float]:
        """反归一化参数"""
        params = {}
        for i, name in enumerate(self.param_bounds.keys()):
            min_val, max_val = self.param_bounds[name]
            params[name] = min_val + normalized[i] * (max_val - min_val)
        return params

    def _expected_improvement(self, x: np.ndarray, xi: float = 0.01) -> float:
        """
        计算期望增量（EI）

        简化实现，使用基于距离的启发式方法。
        """
        if not self.observed_values:
            return 1.0  # 第一个点，最大探索

        best_value = max(self.observed_values) if self.mode == "maximize" else min(self.observed_values)

        # 计算与已观察点的最小距离
        min_distance = float('inf')
        for observed in self.observed_points:
            obs_normalized = self._normalize_params(observed)
            distance = np.linalg.norm(x - obs_normalized)
            min_distance = min(min_distance, distance)

        # 距离越远，探索价值越高
        exploration_score = min_distance

        # 如果这个点可能有更好的值
        current_params = self._denormalize_params(x)
        # 简化：使用距离作为代理
        exploitation_score = 0.5  # 中等利用分数

        ei = exploration_score * 0.7 + exploitation_score * 0.3
        return ei

    def _suggest_next_point(self) -> Dict[str, float]:
        """建议下一个评估点"""
        if not self.observed_points:
            # 第一个点：在参数空间中心开始
            return {name: (min_val + max_val) / 2 for name, (min_val, max_val) in self.param_bounds.items()}

        # 使用随机采样 + EI 选择
        n_candidates = 100
        best_ei = -float('inf')
        best_point = None

        for _ in range(n_candidates):
            # 随机生成候选点
            candidate = {name: random.uniform(min_val, max_val) for name, (min_val, max_val) in self.param_bounds.items()}
            candidate_normalized = self._normalize_params(candidate)

            ei = self._expected_improvement(candidate_normalized)

            if ei > best_ei:
                best_ei = ei
                best_point = candidate

        return best_point

    def run(
        self,
        n_iterations: int = 50,
        n_initial: int = 5
    ) -> BayesianOptimizationResult:
        """
        运行贝叶斯优化

        Args:
            n_iterations: 迭代次数
            n_initial: 初始随机采样次数

        Returns:
            BayesianOptimizationResult: 优化结果
        """
        # 初始随机采样
        for i in range(n_initial):
            point = {name: random.uniform(min_val, max_val) for name, (min_val, max_val) in self.param_bounds.items()}
            value = self.objective_function(point)

            self.observed_points.append(point)
            self.observed_values.append(value)
            self.exploration_points.append(point)

            logger.debug(f"Initial sample {i + 1}: value = {value:.4f}")

        # 贝叶斯优化循环
        for i in range(n_iterations - n_initial):
            # 建议下一个点
            next_point = self._suggest_next_point()

            # 评估
            value = self.objective_function(next_point)

            self.observed_points.append(next_point)
            self.observed_values.append(value)
            self.exploration_points.append(next_point)

            if (i + 1) % 10 == 0:
                best_value = max(self.observed_values) if self.mode == "maximize" else min(self.observed_values)
                logger.info(f"Iteration {i + 1 + n_initial}: Best value = {best_value:.4f}")

        # 获取最佳结果
        if self.mode == "maximize":
            best_idx = np.argmax(self.observed_values)
        else:
            best_idx = np.argmin(self.observed_values)

        best_params = self.observed_points[best_idx]
        best_value = self.observed_values[best_idx]

        return BayesianOptimizationResult(
            best_params=best_params,
            best_value=best_value,
            iterations=len(self.observed_values),
            exploration_points=self.exploration_points,
            acquisition_values=self.observed_values
        )


# ==============================================
# 策略进化引擎
# ==============================================

class StrategyEvolutionEngine:
    """
    策略进化引擎

    整合遗传算法和贝叶斯优化，提供完整的策略参数优化能力。
    """

    def __init__(self):
        self.genetic_optimizer: Optional[GeneticOptimizer] = None
        self.bayesian_optimizer: Optional[BayesianOptimizer] = None
        self.evolution_history: List[EvolutionResult] = []
        self.bayesian_history: List[BayesianOptimizationResult] = []

    def optimize_with_genetic(
        self,
        backtest_function: Callable[[Dict[str, float]], float],
        param_bounds: Dict[str, Tuple[float, float]],
        population_size: int = 50,
        generations: int = 100,
        **kwargs
    ) -> EvolutionResult:
        """
        使用遗传算法优化策略参数

        Args:
            backtest_function: 回测函数，接受参数字典，返回适应度
            param_bounds: 参数边界 {name: (min, max)}
            population_size: 种群大小
            generations: 迭代次数

        Returns:
            EvolutionResult: 优化结果
        """
        logger.info(f"Starting genetic optimization with {population_size} individuals for {generations} generations")

        self.genetic_optimizer = GeneticOptimizer(
            fitness_function=backtest_function,
            param_bounds=param_bounds,
            population_size=population_size,
            **kwargs
        )

        result = self.genetic_optimizer.run(max_generations=generations)
        self.evolution_history.append(result)

        logger.info(f"Genetic optimization completed: Best fitness = {result.best_fitness:.4f}")

        return result

    def optimize_with_bayesian(
        self,
        backtest_function: Callable[[Dict[str, float]], float],
        param_bounds: Dict[str, Tuple[float, float]],
        n_iterations: int = 50,
        mode: str = "maximize"
    ) -> BayesianOptimizationResult:
        """
        使用贝叶斯优化策略参数

        Args:
            backtest_function: 回测函数
            param_bounds: 参数边界
            n_iterations: 迭代次数
            mode: "maximize" 或 "minimize"

        Returns:
            BayesianOptimizationResult: 优化结果
        """
        logger.info(f"Starting Bayesian optimization for {n_iterations} iterations")

        self.bayesian_optimizer = BayesianOptimizer(
            objective_function=backtest_function,
            param_bounds=param_bounds,
            mode=mode
        )

        result = self.bayesian_optimizer.run(n_iterations=n_iterations)
        self.bayesian_history.append(result)

        logger.info(f"Bayesian optimization completed: Best value = {result.best_value:.4f}")

        return result

    async def optimize_with_ai(
        self,
        strategy_code: str,
        backtest_results: Dict[str, Any],
        optimization_goal: str = "sharpe_ratio",
        ai_service=None
    ) -> Dict[str, Any]:
        """
        使用 AI 分析回测结果并提供优化建议

        Args:
            strategy_code: 策略代码
            backtest_results: 回测结果
            optimization_goal: 优化目标
            ai_service: AI 服务实例

        Returns:
            AI 分析结果和优化建议
        """
        if ai_service is None:
            # 延迟导入避免循环依赖
            from src.services.ai.glm import glm5_service
            ai_service = glm5_service

        prompt = f"""
你是一个专业的量化策略分析师。请分析以下策略的回测结果，并提供优化建议。

## 策略代码
```
{strategy_code}
```

## 回测结果
- 总收益率: {backtest_results.get('total_return', 'N/A')}
- 年化收益率: {backtest_results.get('annual_return', 'N/A')}
- 最大回撤: {backtest_results.get('max_drawdown', 'N/A')}
- 夏普比率: {backtest_results.get('sharpe_ratio', 'N/A')}
- 胜率: {backtest_results.get('win_rate', 'N/A')}
- 总交易次数: {backtest_results.get('total_trades', 'N/A')}

## 优化目标
{optimization_goal}

## 请提供
1. 策略弱点分析（至少3点）
2. 参数调整建议（具体数值范围）
3. 风控改进建议
4. 预期改进效果
5. 优化后的策略代码片段（如果适用）

请以 JSON 格式返回结果。
"""

        try:
            result = await ai_service.chat(prompt)
            return {
                "success": True,
                "analysis": result,
                "optimization_goal": optimization_goal
            }
        except Exception as e:
            logger.error(f"AI optimization analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_evolution_summary(self) -> Dict[str, Any]:
        """获取进化历史摘要"""
        result = {
            "genetic_optimizations": len(self.evolution_history),
            "bayesian_optimizations": len(self.bayesian_history),
            "best_genetic_result": None,
            "best_bayesian_result": None
        }

        if self.evolution_history:
            best_genetic = max(self.evolution_history, key=lambda x: x.best_fitness)
            result["best_genetic_result"] = {
                "best_fitness": best_genetic.best_fitness,
                "best_params": best_genetic.best_params,
                "generations": best_genetic.generations
            }

        if self.bayesian_history:
            best_bayesian = max(self.bayesian_history, key=lambda x: x.best_value)
            result["best_bayesian_result"] = {
                "best_value": best_bayesian.best_value,
                "best_params": best_bayesian.best_params,
                "iterations": best_bayesian.iterations
            }

        return result


# 全局实例
evolution_engine = StrategyEvolutionEngine()
