/**
 * 数据表格面板
 * Data Table Panel
 *
 * 集成真实股票列表数据
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Table, Input, Select } from 'antd';
import { SearchOutlined, RiseOutlined, FallOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { TablePanelConfig } from '../../../types/workspace';
import { getStockList, StockInfo, StockListParams, formatNumber, formatChangePercent } from '../../../services/marketData';

interface DataTablePanelProps {
  config?: TablePanelConfig;
}

interface TableStockData extends StockInfo {
  key: string;
  quote?: {
    price: number;
    change: number;
    change_percent: number;
    volume: number;
    amount: number;
    pe_ttm?: number;
    pb?: number;
    total_mv?: number;
  };
}

// 模拟股票数据（API 不可用时使用）
const generateMockStockData = (): TableStockData[] => {
  return [
    { key: '600519.SH', symbol: '600519.SH', name: '贵州茅台', industry: '白酒', market: 'SH', quote: { price: 1688.00, change: 28.50, change_percent: 1.72, volume: 3256842, amount: 5498520000, pe_ttm: 28.5, pb: 8.2, total_mv: 2118400000000 } },
    { key: '600036.SH', symbol: '600036.SH', name: '招商银行', industry: '银行', market: 'SH', quote: { price: 32.45, change: -0.35, change_percent: -1.07, volume: 85632145, amount: 2778250000, pe_ttm: 5.2, pb: 0.8, total_mv: 818500000000 } },
    { key: '000001.SZ', symbol: '000001.SZ', name: '平安银行', industry: '银行', market: 'SZ', quote: { price: 11.28, change: 0.15, change_percent: 1.35, volume: 125632845, amount: 1417140000, pe_ttm: 4.8, pb: 0.6, total_mv: 218800000000 } },
    { key: '000858.SZ', symbol: '000858.SZ', name: '五粮液', industry: '白酒', market: 'SZ', quote: { price: 158.50, change: -2.30, change_percent: -1.43, volume: 15632845, amount: 2477820000, pe_ttm: 22.5, pb: 5.6, total_mv: 615600000000 } },
    { key: '601318.SH', symbol: '601318.SH', name: '中国平安', industry: '保险', market: 'SH', quote: { price: 42.35, change: 0.85, change_percent: 2.05, volume: 45632145, amount: 1932480000, pe_ttm: 8.5, pb: 0.9, total_mv: 772200000000 } },
    { key: '600900.SH', symbol: '600900.SH', name: '长江电力', industry: '电力', market: 'SH', quote: { price: 28.65, change: 0.42, change_percent: 1.49, volume: 35628452, amount: 1020760000, pe_ttm: 18.2, pb: 2.1, total_mv: 658200000000 } },
    { key: '000333.SZ', symbol: '000333.SZ', name: '美的集团', industry: '家电', market: 'SZ', quote: { price: 58.92, change: -0.78, change_percent: -1.31, volume: 28654123, amount: 1688250000, pe_ttm: 12.5, pb: 3.2, total_mv: 412500000000 } },
    { key: '002594.SZ', symbol: '002594.SZ', name: '比亚迪', industry: '汽车', market: 'SZ', quote: { price: 235.80, change: 8.50, change_percent: 3.74, volume: 18563214, amount: 4378520000, pe_ttm: 35.2, pb: 6.8, total_mv: 684200000000 } },
  ];
};

const DataTablePanel: React.FC<DataTablePanelProps> = ({ config }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<TableStockData[]>([]);
  const [searchText, setSearchText] = useState('');
  const [dataType, setDataType] = useState(config?.dataType || 'stocks');
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });

  // 加载股票数据
  const loadStockData = useCallback(async () => {
    setLoading(true);
    try {
      const params: StockListParams = {
        page: pagination.current,
        page_size: pagination.pageSize,
      };

      const response = await getStockList(params);

      if (response && response.items) {
        const tableData: TableStockData[] = response.items.map((item) => ({
          ...item,
          key: item.symbol,
        }));
        setData(tableData);
        setPagination((prev) => ({ ...prev, total: response.total }));
      } else {
        // API 返回空数据，使用模拟数据
        setData(generateMockStockData());
        setPagination((prev) => ({ ...prev, total: 8 }));
      }
    } catch (error) {
      console.error('Failed to load stock data:', error);
      // 如果 API 不可用，使用模拟数据
      setData(generateMockStockData());
      setPagination((prev) => ({ ...prev, total: 8 }));
    } finally {
      setLoading(false);
    }
  }, [pagination.current, pagination.pageSize, dataType]);

  // 加载数据
  useEffect(() => {
    loadStockData();
  }, [loadStockData]);

  // 处理表格分页变化
  const handleTableChange = (newPagination: any) => {
    setPagination({
      current: newPagination.current,
      pageSize: newPagination.pageSize,
      total: pagination.total,
    });
  };

  // 表格列定义
  const columns: ColumnsType<TableStockData> = [
    {
      title: '代码',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 90,
      fixed: 'left',
      render: (text: string) => <span className="stock-code">{text}</span>,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 80,
      fixed: 'left',
    },
    {
      title: '行业',
      dataIndex: 'industry',
      key: 'industry',
      width: 70,
    },
    {
      title: '现价',
      dataIndex: ['quote', 'price'],
      key: 'price',
      width: 80,
      align: 'right',
      render: (price: number, record) => {
        if (!price) return '--';
        const change = record.quote?.change || 0;
        return (
          <span className={change >= 0 ? 'price-up' : 'price-down'}>
            {price.toFixed(2)}
          </span>
        );
      },
    },
    {
      title: '涨跌',
      dataIndex: ['quote', 'change_percent'],
      key: 'changePercent',
      width: 80,
      align: 'right',
      sorter: (a, b) => (a.quote?.change_percent || 0) - (b.quote?.change_percent || 0),
      render: (percent: number) => {
        if (percent === undefined) return '--';
        return (
          <span className={percent >= 0 ? 'price-up' : 'price-down'}>
            {percent >= 0 ? <RiseOutlined /> : <FallOutlined />}
            {formatChangePercent(percent)}
          </span>
        );
      },
    },
    {
      title: '成交量',
      dataIndex: ['quote', 'volume'],
      key: 'volume',
      width: 90,
      align: 'right',
      render: (vol: number) => vol ? formatNumber(vol, 0) : '--',
    },
    {
      title: '成交额',
      dataIndex: ['quote', 'amount'],
      key: 'amount',
      width: 90,
      align: 'right',
      render: (amount: number) => amount ? formatNumber(amount, 0) : '--',
    },
    {
      title: '市盈率',
      dataIndex: ['quote', 'pe_ttm'],
      key: 'pe',
      width: 70,
      align: 'right',
      render: (pe: number) => pe ? pe.toFixed(1) : '--',
    },
    {
      title: '市净率',
      dataIndex: ['quote', 'pb'],
      key: 'pb',
      width: 70,
      align: 'right',
      render: (pb: number) => pb ? pb.toFixed(1) : '--',
    },
    {
      title: '市值',
      dataIndex: ['quote', 'total_mv'],
      key: 'marketCap',
      width: 90,
      align: 'right',
      render: (mv: number) => mv ? formatNumber(mv, 0) : '--',
    },
  ];

  // 过滤数据
  const filteredData = data.filter(
    (item) =>
      item.symbol?.toLowerCase().includes(searchText.toLowerCase()) ||
      item.name?.includes(searchText)
  );

  return (
    <div className="datatable-panel">
      <div className="panel-toolbar">
        <Input
          placeholder="搜索股票代码/名称"
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          size="small"
          style={{ width: 150 }}
          allowClear
        />
        <Select
          value={dataType}
          onChange={setDataType}
          size="small"
          style={{ width: 80 }}
          options={[
            { value: 'stocks', label: 'A股' },
            { value: 'funds', label: '基金' },
            { value: 'etf', label: 'ETF' },
          ]}
        />
        <ReloadOutlined
          className="reload-icon"
          onClick={() => loadStockData()}
          spin={loading}
          style={{ cursor: 'pointer', color: '#8B949E' }}
        />
      </div>
      <div className="table-container">
        <Table
          columns={columns}
          dataSource={filteredData}
          loading={loading}
          size="small"
          pagination={{
            ...pagination,
            showSizeChanger: false,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 'max-content', y: 280 }}
          rowClassName={(record) =>
            record.quote?.change && record.quote.change >= 0 ? 'row-up' : 'row-down'
          }
        />
      </div>
    </div>
  );
};

export default DataTablePanel;
