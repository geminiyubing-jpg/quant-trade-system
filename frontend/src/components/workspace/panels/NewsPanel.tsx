/**
 * 新闻面板
 * News Panel
 */
import React, { useState, useEffect } from 'react';
import { List, Tag, Spin, Empty, Button } from 'antd';
import { ClockCircleOutlined, LinkOutlined } from '@ant-design/icons';
import { NewsPanelConfig } from '../../../types/workspace';

interface NewsPanelProps {
  config?: NewsPanelConfig;
}

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  time: string;
  tags: string[];
  url: string;
}

const NewsPanel: React.FC<NewsPanelProps> = ({ config: _config }) => {
  const [loading, setLoading] = useState(true);
  const [news, setNews] = useState<NewsItem[]>([]);

  // 加载新闻
  useEffect(() => {
    const loadNews = async () => {
      setLoading(true);
      // 模拟数据
      setTimeout(() => {
        const mockData: NewsItem[] = [
          {
            id: '1',
            title: '央行：稳健的货币政策要灵活精准、合理适度',
            summary: '中国人民银行发布2026年第一季度货币政策执行报告，强调将继续实施稳健的货币政策...',
            source: '证券时报',
            time: '10分钟前',
            tags: ['宏观', '政策'],
            url: '#',
          },
          {
            id: '2',
            title: '贵州茅台发布2025年年报：净利润同比增长15.2%',
            summary: '贵州茅台披露年报，2025年实现营业收入1275.5亿元，同比增长16.8%；净利润655.2亿元...',
            source: '财联社',
            time: '25分钟前',
            tags: ['白酒', '年报'],
            url: '#',
          },
          {
            id: '3',
            title: '北向资金今日净买入52.3亿元',
            summary: '数据显示，北向资金全天净买入52.3亿元，其中沪股通净买入28.6亿元，深股通净买入23.7亿元...',
            source: '东方财富',
            time: '1小时前',
            tags: ['资金', '外资'],
            url: '#',
          },
          {
            id: '4',
            title: '新能源板块持续走强，多股涨停',
            summary: '受政策利好影响，新能源板块今日表现强势，宁德时代、比亚迪等龙头股纷纷大涨...',
            source: '同花顺',
            time: '2小时前',
            tags: ['新能源', '行情'],
            url: '#',
          },
          {
            id: '5',
            title: '券商看好2026年A股市场表现',
            summary: '多家券商发布2026年投资策略报告，普遍看好A股市场，建议关注科技、消费、医药等板块...',
            source: '中国证券报',
            time: '3小时前',
            tags: ['策略', '机构'],
            url: '#',
          },
        ];
        setNews(mockData);
        setLoading(false);
      }, 300);
    };

    loadNews();
  }, []);

  // 获取标签颜色
  const getTagColor = (tag: string): string => {
    const colors: Record<string, string> = {
      '宏观': '#FF6B00',
      '政策': '#1890FF',
      '白酒': '#FFD700',
      '年报': '#52C41A',
      '资金': '#722ED1',
      '外资': '#13C2C2',
      '新能源': '#FA8C16',
      '行情': '#EB2F96',
      '策略': '#2F54EB',
      '机构': '#FAAD14',
    };
    return colors[tag] || '#8B949E';
  };

  return (
    <div className="news-panel">
      <div className="panel-toolbar">
        <span className="toolbar-title">资讯快讯</span>
      </div>
      <div className="news-container">
        {loading ? (
          <div className="loading-center"><Spin /></div>
        ) : news.length === 0 ? (
          <Empty description="暂无新闻" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <List
            dataSource={news}
            renderItem={item => (
              <List.Item className="news-item">
                <div className="news-header">
                  <div className="news-tags">
                    {item.tags.map(tag => (
                      <Tag key={tag} color={getTagColor(tag)}>{tag}</Tag>
                    ))}
                  </div>
                  <span className="news-time">
                    <ClockCircleOutlined /> {item.time}
                  </span>
                </div>
                <h4 className="news-title">{item.title}</h4>
                <p className="news-summary">{item.summary}</p>
                <div className="news-footer">
                  <span className="news-source">{item.source}</span>
                  <Button type="link" size="small" icon={<LinkOutlined />} href={item.url}>
                    查看详情
                  </Button>
                </div>
              </List.Item>
            )}
          />
        )}
      </div>
    </div>
  );
};

export default NewsPanel;
