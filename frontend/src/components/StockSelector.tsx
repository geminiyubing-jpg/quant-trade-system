/**
 * StockSelector - 股票选择器组件
 *
 * 功能：
 * - 搜索股票（代码/名称模糊匹配）
 * - 批量导入股票代码
 * - 板块选择（按行业批量添加）
 * - 已选股票管理（删除、清空）
 */

import React, { useState, useMemo } from 'react';
import {
  Input,
  Button,
  Tag,
  Space,
  Tabs,
  List,
  message,
  Typography,
  Card,
  Tooltip,
} from 'antd';
import {
  SearchOutlined,
  PlusOutlined,
  ClearOutlined,
  ImportOutlined,
  AppstoreOutlined,
  StockOutlined,
} from '@ant-design/icons';

const { Search } = Input;
const { TabPane } = Tabs;
const { Text } = Typography;

// ==============================================
// 类型定义
// ==============================================

export interface StockItem {
  code: string;       // 股票代码，如 000001.SZ
  name: string;       // 股票名称
  market: string;     // 市场：SH, SZ, BJ
  industry?: string;  // 所属行业
}

interface StockSelectorProps {
  value?: string[];
  onChange?: (symbols: string[]) => void;
  maxSelect?: number;
  placeholder?: string;
}

// ==============================================
// 模拟数据（实际项目中应从 API 获取）
// ==============================================

const MOCK_STOCKS: StockItem[] = [
  { code: '000001.SZ', name: '平安银行', market: 'SZ', industry: '银行' },
  { code: '000002.SZ', name: '万科A', market: 'SZ', industry: '房地产' },
  { code: '000063.SZ', name: '中兴通讯', market: 'SZ', industry: '通信' },
  { code: '000333.SZ', name: '美的集团', market: 'SZ', industry: '家电' },
  { code: '000651.SZ', name: '格力电器', market: 'SZ', industry: '家电' },
  { code: '000858.SZ', name: '五粮液', market: 'SZ', industry: '白酒' },
  { code: '600000.SH', name: '浦发银行', market: 'SH', industry: '银行' },
  { code: '600036.SH', name: '招商银行', market: 'SH', industry: '银行' },
  { code: '600519.SH', name: '贵州茅台', market: 'SH', industry: '白酒' },
  { code: '600887.SH', name: '伊利股份', market: 'SH', industry: '食品' },
  { code: '601318.SH', name: '中国平安', market: 'SH', industry: '保险' },
  { code: '601888.SH', name: '中国中免', market: 'SH', industry: '零售' },
  { code: '300001.SZ', name: '特锐德', market: 'SZ', industry: '电气设备' },
  { code: '300059.SZ', name: '东方财富', market: 'SZ', industry: '证券' },
  { code: '300750.SZ', name: '宁德时代', market: 'SZ', industry: '电池' },
];

// 行业板块
const INDUSTRY_SECTORS = [
  { name: '银行', stocks: ['000001.SZ', '600000.SH', '600036.SH'] },
  { name: '白酒', stocks: ['000858.SZ', '600519.SH'] },
  { name: '家电', stocks: ['000333.SZ', '000651.SZ'] },
  { name: '新能源', stocks: ['300750.SZ', '300001.SZ'] },
  { name: '证券', stocks: ['300059.SZ'] },
];

// 常用股票（模拟最近使用）
const RECENT_STOCKS = ['600519.SH', '000858.SZ', '300750.SZ', '600036.SH'];

// ==============================================
// 主组件
// ==============================================

const StockSelector: React.FC<StockSelectorProps> = ({
  value = [],
  onChange,
  maxSelect = 100,
  placeholder = '输入股票代码或名称搜索',
}) => {
  const [searchKeyword, setSearchKeyword] = useState('');
  const [activeTab, setActiveTab] = useState('search');
  const [batchInput, setBatchInput] = useState('');

  // 搜索结果
  const searchResults = useMemo(() => {
    if (!searchKeyword.trim()) return [];
    const keyword = searchKeyword.toLowerCase();
    return MOCK_STOCKS.filter(
      (stock) =>
        stock.code.toLowerCase().includes(keyword) ||
        stock.name.toLowerCase().includes(keyword)
    ).slice(0, 20);
  }, [searchKeyword]);

  // 已选股票详情
  const selectedStocks = useMemo(() => {
    return value.map((code) => {
      const stock = MOCK_STOCKS.find((s) => s.code === code);
      return stock || { code, name: code, market: 'Unknown' };
    });
  }, [value]);

  // 添加股票
  const handleAddStock = (code: string) => {
    if (value.includes(code)) {
      message.info('该股票已在列表中');
      return;
    }
    if (value.length >= maxSelect) {
      message.warning(`最多只能选择 ${maxSelect} 只股票`);
      return;
    }
    onChange?.([...value, code]);
  };

  // 移除股票
  const handleRemoveStock = (code: string) => {
    onChange?.(value.filter((c) => c !== code));
  };

  // 清空所有
  const handleClearAll = () => {
    onChange?.([]);
  };

  // 批量导入
  const handleBatchImport = () => {
    const lines = batchInput.split(/[\n,;，；\s]+/);
    const newCodes: string[] = [];

    for (const line of lines) {
      const trimmed = line.trim().toUpperCase();
      // 验证股票代码格式
      const match = trimmed.match(/^(\d{6})(\.(SZ|SH|BJ))?$/);
      if (match) {
        const code = match[1];
        const suffix = match[3] || inferMarket(code);
        const fullCode = `${code}.${suffix}`;
        if (!value.includes(fullCode) && !newCodes.includes(fullCode)) {
          newCodes.push(fullCode);
        }
      }
    }

    if (newCodes.length === 0) {
      message.warning('未识别到有效的股票代码');
      return;
    }

    const total = value.length + newCodes.length;
    if (total > maxSelect) {
      const allowed = maxSelect - value.length;
      message.warning(`超过最大限制，仅添加 ${allowed} 只股票`);
      onChange?.([...value, ...newCodes.slice(0, allowed)]);
    } else {
      onChange?.([...value, ...newCodes]);
      message.success(`成功添加 ${newCodes.length} 只股票`);
    }

    setBatchInput('');
  };

  // 板块批量添加
  const handleSectorSelect = (_sectorName: string, stocks: string[]) => {
    const newCodes = stocks.filter((s) => !value.includes(s));
    if (newCodes.length === 0) {
      message.info('该板块股票已全部在列表中');
      return;
    }
    onChange?.([...value, ...newCodes]);
    message.success(`添加 ${newCodes.length} 只股票`);
  };

  // 渲染已选股票
  const renderSelectedStocks = () => (
    <div className="selected-stocks-container">
      <div className="selected-header">
        <Space>
          <Text strong>已选股票</Text>
          <Tag color="blue">{value.length} / {maxSelect}</Tag>
        </Space>
        {value.length > 0 && (
          <Button
            type="text"
            size="small"
            icon={<ClearOutlined />}
            onClick={handleClearAll}
            danger
          >
            清空
          </Button>
        )}
      </div>
      <div className="selected-tags">
        {selectedStocks.map((stock) => (
          <Tag
            key={stock.code}
            closable
            onClose={() => handleRemoveStock(stock.code)}
            style={{ margin: '4px' }}
          >
            <Tooltip title={`${stock.code} - ${stock.industry || ''}`}>
              {stock.name} ({stock.code.split('.')[0]})
            </Tooltip>
          </Tag>
        ))}
        {value.length === 0 && (
          <Text type="secondary">暂未选择股票</Text>
        )}
      </div>
    </div>
  );

  return (
    <div className="stock-selector">
      {renderSelectedStocks()}

      <Tabs activeKey={activeTab} onChange={setActiveTab} size="small">
        {/* 搜索 */}
        <TabPane
          tab={<span><SearchOutlined /> 搜索</span>}
          key="search"
        >
          <Search
            placeholder={placeholder}
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            style={{ marginBottom: 12 }}
            allowClear
          />
          <List
            size="small"
            dataSource={searchResults}
            locale={{ emptyText: searchKeyword ? '未找到匹配的股票' : '请输入股票代码或名称' }}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button
                    key="add"
                    type="link"
                    size="small"
                    icon={<PlusOutlined />}
                    disabled={value.includes(item.code)}
                    onClick={() => handleAddStock(item.code)}
                  >
                    {value.includes(item.code) ? '已添加' : '添加'}
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  avatar={<StockOutlined style={{ color: '#1890ff' }} />}
                  title={`${item.name} (${item.code})`}
                  description={item.industry}
                />
              </List.Item>
            )}
            style={{ maxHeight: 200, overflow: 'auto' }}
          />
        </TabPane>

        {/* 批量导入 */}
        <TabPane
          tab={<span><ImportOutlined /> 批量导入</span>}
          key="import"
        >
          <Input.TextArea
            placeholder="输入股票代码，支持以下格式：&#10;000001.SZ&#10;000001&#10;600000.SH, 600036.SH"
            value={batchInput}
            onChange={(e) => setBatchInput(e.target.value)}
            rows={4}
            style={{ fontFamily: 'monospace' }}
          />
          <Button
            type="primary"
            icon={<ImportOutlined />}
            onClick={handleBatchImport}
            style={{ marginTop: 8 }}
            block
          >
            导入
          </Button>
        </TabPane>

        {/* 板块选择 */}
        <TabPane
          tab={<span><AppstoreOutlined /> 板块</span>}
          key="sector"
        >
          <div className="sector-grid">
            {INDUSTRY_SECTORS.map((sector) => (
              <Card
                key={sector.name}
                size="small"
                hoverable
                onClick={() => handleSectorSelect(sector.name, sector.stocks)}
                style={{ cursor: 'pointer' }}
              >
                <Space direction="vertical" size={0}>
                  <Text strong>{sector.name}</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {sector.stocks.length} 只股票
                  </Text>
                </Space>
              </Card>
            ))}
          </div>
        </TabPane>

        {/* 常用股票 */}
        <TabPane
          tab={<span><StockOutlined /> 常用</span>}
          key="recent"
        >
          <List
            size="small"
            dataSource={RECENT_STOCKS.map((code) =>
              MOCK_STOCKS.find((s) => s.code === code) || { code, name: code }
            )}
            renderItem={(item: any) => (
              <List.Item
                actions={[
                  <Button
                    key="add"
                    type="link"
                    size="small"
                    icon={<PlusOutlined />}
                    disabled={value.includes(item.code)}
                    onClick={() => handleAddStock(item.code)}
                  >
                    {value.includes(item.code) ? '已添加' : '添加'}
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  avatar={<StockOutlined />}
                  title={`${item.name} (${item.code})`}
                />
              </List.Item>
            )}
          />
        </TabPane>
      </Tabs>

      <style>{`
        .stock-selector {
          border: 1px solid #d9d9d9;
          border-radius: 6px;
          padding: 12px;
          background: #fafafa;
        }

        .selected-stocks-container {
          margin-bottom: 12px;
          padding: 8px;
          background: #fff;
          border-radius: 4px;
          border: 1px solid #e8e8e8;
        }

        .selected-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .selected-tags {
          min-height: 32px;
          display: flex;
          flex-wrap: wrap;
          align-items: center;
        }

        .sector-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
        }

        .ant-list-item {
          padding: 8px 0 !important;
        }

        .ant-card-small {
          text-align: center;
        }
      `}</style>
    </div>
  );
};

// ==============================================
// 辅助函数
// ==============================================

/** 根据代码推断市场 */
function inferMarket(code: string): string {
  if (code.startsWith('6')) return 'SH';
  if (code.startsWith('0') || code.startsWith('3')) return 'SZ';
  if (code.startsWith('4') || code.startsWith('8')) return 'BJ';
  return 'SZ';
}

export default StockSelector;
