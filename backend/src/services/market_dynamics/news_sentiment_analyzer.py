"""
==============================================
QuantAI Ecosystem - 新闻情感分析器
==============================================

使用NLP技术分析财经新闻情感：
- 新闻采集
- 情感分析
- 主题提取
- 事件识别
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """情感分析结果"""
    sentiment_id: str
    title: str
    summary: str
    sentiment_score: float          # -1 到 1
    sentiment_label: str            # positive/negative/neutral
    confidence: float
    topics: List[str]
    entities: List[Dict[str, str]]
    events: List[Dict[str, Any]]
    impact_level: str               # high/medium/low
    affected_assets: List[str]
    analyzed_at: datetime


class NewsSentimentAnalyzer:
    """
    新闻情感分析器

    功能：
    - 新闻采集
    - NLP情感分析
    - 主题提取
    - 实体识别
    - 事件提取
    """

    # 情感关键词
    POSITIVE_KEYWORDS = [
        '增长', '上涨', '突破', '盈利', '利好', '反弹', '新高',
        '超额', '强劲', '乐观', '机遇', '扩张', '收购',
        '增长', '上升', '突破', 'profit', 'growth', 'surge', 'rally'
    ]

    NEGATIVE_KEYWORDS = [
        '下跌', '亏损', '下滑', '暴跌', '利空', '风险', '担忧',
        '衰退', '萎缩', '裁员', '违约', '债务', '危机',
        '下降', '暴跌', 'loss', 'decline', 'crash', 'risk', 'concern'
    ]

    # 高影响关键词
    HIGH_IMPACT_KEYWORDS = [
        '央行', '利率', '政策', '监管', '制裁', '贸易战',
        '疫情', '战争', '选举', '国会', 'Fed', 'ECB', 'PBOC'
    ]

    # 金融实体模式
    ENTITY_PATTERNS = {
        'stock': r'(?:SH\d{6}|SZ\d{6}|\d{6}\.(?:SH|SZ|HK)|[A-Z]{1,5}=F)',
        'index': r'(?:上证指数|深证成指|创业板指|沪深300|中证500|S&P\s*500|NASDAQ|Dow\s*Jones)',
        'currency': r'(?:美元|欧元|日元|人民币|CNY|USD|EUR|JPY)',
        'commodity': r'(?:原油|黄金|铜|铁矿石|CRUDE|GOLD|COPPER)',
        'company': r'(?:[\u4e00-\u9fa5]{2,10}(?:股份|集团|公司|科技|银行))'
    }

    def __init__(self, ai_client=None, db=None):
        self.ai_client = ai_client
        self.db = db

    async def analyze(self, title: str, content: str = "", source: str = "") -> SentimentResult:
        """
        分析新闻情感

        Args:
            title: 新闻标题
            content: 新闻内容
            source: 新闻来源

        Returns:
            SentimentResult: 分析结果
        """
        logger.info(f"分析新闻: {title[:50]}...")

        # 1. 基于规则的情感分析
        rule_sentiment = self._rule_based_sentiment(title, content)

        # 2. AI增强分析 (如果有AI客户端)
        if self.ai_client:
            ai_sentiment = await self._ai_enhanced_sentiment(title, content)
            sentiment_score = (rule_sentiment['score'] + ai_sentiment['score']) / 2
            confidence = max(rule_sentiment['confidence'], ai_sentiment['confidence'])
        else:
            sentiment_score = rule_sentiment['score']
            confidence = rule_sentiment['confidence']

        # 3. 确定情感标签
        sentiment_label = self._determine_sentiment_label(sentiment_score)

        # 4. 提取主题
        topics = self._extract_topics(title, content)

        # 5. 识别实体
        entities = self._extract_entities(title, content)

        # 6. 提取事件
        events = self._extract_events(title, content)

        # 7. 评估影响级别
        impact_level = self._assess_impact_level(title, content, sentiment_score)

        # 8. 识别受影响资产
        affected_assets = self._identify_affected_assets(entities, topics)

        # 9. 生成摘要
        summary = self._generate_summary(title, content, topics, sentiment_label)

        result = SentimentResult(
            sentiment_id=f"sent_{uuid.uuid4().hex[:12]}",
            title=title,
            summary=summary,
            sentiment_score=round(sentiment_score, 4),
            sentiment_label=sentiment_label,
            confidence=round(confidence, 4),
            topics=topics,
            entities=entities,
            events=events,
            impact_level=impact_level,
            affected_assets=affected_assets,
            analyzed_at=datetime.utcnow()
        )

        # 10. 保存结果
        self._save_result(result, content, source)

        return result

    def _rule_based_sentiment(self, title: str, content: str) -> Dict[str, float]:
        """基于规则的情感分析"""
        text = f"{title} {content}".lower()

        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw.lower() in text)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw.lower() in text)

        total = positive_count + negative_count
        if total == 0:
            return {'score': 0.0, 'confidence': 0.3}

        score = (positive_count - negative_count) / total
        confidence = min(0.8, 0.3 + total * 0.1)

        return {'score': score, 'confidence': confidence}

    async def _ai_enhanced_sentiment(self, title: str, content: str) -> Dict[str, float]:
        """AI增强情感分析"""
        if not self.ai_client:
            return {'score': 0.0, 'confidence': 0.0}

        try:
            prompt = f"""
            分析以下财经新闻的情感倾向，返回JSON格式：

            标题: {title}
            内容: {content[:500]}

            返回格式:
            {{
                "sentiment_score": -1到1之间的数值,
                "confidence": 0到1之间的置信度,
                "reasoning": "判断理由"
            }}
            """

            # 调用AI (实际实现)
            # response = await self.ai_client.generate(prompt)
            # result = json.loads(response)

            # 模拟返回
            result = {'sentiment_score': 0.0, 'confidence': 0.5}

            return {
                'score': result.get('sentiment_score', 0.0),
                'confidence': result.get('confidence', 0.5)
            }

        except Exception as e:
            logger.error(f"AI情感分析失败: {e}")
            return {'score': 0.0, 'confidence': 0.0}

    def _determine_sentiment_label(self, score: float) -> str:
        """确定情感标签"""
        if score > 0.2:
            return 'positive'
        elif score < -0.2:
            return 'negative'
        else:
            return 'neutral'

    def _extract_topics(self, title: str, content: str) -> List[str]:
        """提取主题"""
        topics = []
        text = f"{title} {content}"

        topic_keywords = {
            '货币政策': ['利率', '央行', '货币', '降息', '加息', 'Fed', 'PBOC'],
            '财政政策': ['财政', '税收', '预算', '支出', '政府'],
            '经济增长': ['GDP', '增长', '经济', '复苏', '衰退'],
            '通胀': ['通胀', 'CPI', 'PPI', '物价', '上涨'],
            '就业': ['就业', '失业', '工资', '劳动力'],
            '贸易': ['贸易', '出口', '进口', '关税', '顺差', '逆差'],
            '股市': ['股市', '股票', '指数', 'A股', '港股', '美股'],
            '债市': ['债券', '国债', '收益率', '信用'],
            '汇市': ['汇率', '外汇', '人民币', '美元'],
            '商品': ['商品', '原油', '黄金', '大宗'],
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)

        return topics[:5]  # 最多返回5个主题

    def _extract_entities(self, title: str, content: str) -> List[Dict[str, str]]:
        """识别实体"""
        entities = []
        text = f"{title} {content}"

        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                entities.append({
                    'type': entity_type,
                    'value': match,
                    'source': 'regex'
                })

        return entities[:10]  # 最多返回10个实体

    def _extract_events(self, title: str, content: str) -> List[Dict[str, Any]]:
        """提取事件"""
        events = []
        text = f"{title} {content}"

        event_patterns = [
            {'pattern': r'加息(\d+)个?基点', 'type': 'rate_hike', 'impact': 'negative'},
            {'pattern': r'降息(\d+)个?基点', 'type': 'rate_cut', 'impact': 'positive'},
            {'pattern': r'发布.*?报告', 'type': 'report_release', 'impact': 'neutral'},
            {'pattern': r'公布.*?数据', 'type': 'data_release', 'impact': 'neutral'},
            {'pattern': r'收购.*?公司', 'type': 'acquisition', 'impact': 'positive'},
            {'pattern': r'裁员', 'type': 'layoff', 'impact': 'negative'},
        ]

        for ep in event_patterns:
            matches = re.findall(ep['pattern'], text)
            if matches:
                events.append({
                    'type': ep['type'],
                    'impact': ep['impact'],
                    'count': len(matches)
                })

        return events

    def _assess_impact_level(self, title: str, content: str, sentiment_score: float) -> str:
        """评估影响级别"""
        text = f"{title} {content}"

        # 检查高影响关键词
        high_impact_count = sum(1 for kw in self.HIGH_IMPACT_KEYWORDS if kw in text)

        if high_impact_count >= 2 or abs(sentiment_score) > 0.7:
            return 'high'
        elif high_impact_count >= 1 or abs(sentiment_score) > 0.4:
            return 'medium'
        else:
            return 'low'

    def _identify_affected_assets(self, entities: List[Dict], topics: List[str]) -> List[str]:
        """识别受影响资产"""
        assets = []

        for entity in entities:
            if entity['type'] in ['stock', 'index', 'currency', 'commodity']:
                assets.append(entity['value'])

        # 基于主题推断
        topic_asset_map = {
            '股市': ['A股指数', '沪深300'],
            '债市': ['国债期货', '信用债'],
            '汇市': ['USDCNY', 'USDEUR'],
            '商品': ['原油', '黄金'],
        }

        for topic in topics:
            if topic in topic_asset_map:
                assets.extend(topic_asset_map[topic])

        return list(set(assets))[:5]

    def _generate_summary(self, title: str, content: str, topics: List[str], sentiment: str) -> str:
        """生成摘要"""
        sentiment_map = {
            'positive': '积极',
            'negative': '消极',
            'neutral': '中性'
        }

        topic_str = '、'.join(topics[:3]) if topics else '市场动态'

        return f"[{sentiment_map.get(sentiment, '中性')}] {title[:50]}... 涉及{topic_str}"

    def _save_result(self, result: SentimentResult, content: str, source: str) -> None:
        """保存分析结果"""
        if self.db:
            try:
                self.db.execute("""
                    INSERT INTO news_sentiment
                    (sentiment_id, source, title, content, summary, sentiment_score,
                     sentiment_label, confidence, topics, entities, events,
                     impact_level, affected_assets, analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.sentiment_id,
                    source,
                    result.title,
                    content,
                    result.summary,
                    result.sentiment_score,
                    result.sentiment_label,
                    result.confidence,
                    json.dumps(result.topics),
                    json.dumps(result.entities),
                    json.dumps(result.events),
                    result.impact_level,
                    json.dumps(result.affected_assets),
                    result.analyzed_at
                ))
            except Exception as e:
                logger.error(f"保存情感分析结果失败: {e}")

    async def analyze_batch(self, news_items: List[Dict[str, str]]) -> List[SentimentResult]:
        """批量分析新闻"""
        results = []
        for item in news_items:
            result = await self.analyze(
                title=item.get('title', ''),
                content=item.get('content', ''),
                source=item.get('source', '')
            )
            results.append(result)
        return results


# 单例实例
_news_sentiment_analyzer: Optional[NewsSentimentAnalyzer] = None


def get_news_sentiment_analyzer() -> NewsSentimentAnalyzer:
    """获取新闻情感分析器实例"""
    global _news_sentiment_analyzer
    if _news_sentiment_analyzer is None:
        _news_sentiment_analyzer = NewsSentimentAnalyzer()
    return _news_sentiment_analyzer
