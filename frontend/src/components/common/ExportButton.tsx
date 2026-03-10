/**
 * 导出按钮组件
 * 支持 CSV 和 Excel 格式导出
 */

import React from 'react';
import { Button, Dropdown, message } from 'antd';
import { DownloadOutlined, FileExcelOutlined, FileTextOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { exportToCSV, exportToExcel, exportMarketData } from '../../services/export';
import type { MarketDataExport, ExportOptions } from '../../services/export';

interface ExportButtonProps<T> {
  /** 要导出的数据 */
  data: T[];
  /** 选中的行（可选） */
  selectedKeys?: string[];
  /** 获取选中数据的键 */
  getRowKey?: (item: T) => string;
  /** 导出文件名 */
  filename?: string;
  /** 导出类型：通用数据还是行情数据 */
  type?: 'generic' | 'market';
  /** 是否禁用 */
  disabled?: boolean;
  /** 按钮样式 */
  style?: React.CSSProperties;
  /** 按钮类名 */
  className?: string;
  /** 导出完成回调 */
  onExportComplete?: (format: 'csv' | 'excel', count: number) => void;
}

/**
 * 导出按钮组件
 */
function ExportButton<T extends Record<string, unknown>>({
  data,
  selectedKeys = [],
  getRowKey,
  filename,
  type = 'generic',
  disabled = false,
  style,
  className,
  onExportComplete,
}: ExportButtonProps<T>): React.ReactElement {
  // 执行导出
  const doExport = (format: 'csv' | 'excel', selectedOnly: boolean = false) => {
    if (!data || data.length === 0) {
      message.warning('没有数据可导出');
      return;
    }

    const options: ExportOptions = {
      filename: filename || `export_${Date.now()}`,
    };

    let dataToExport: T[] | MarketDataExport[];
    let count: number;

    if (selectedOnly && selectedKeys.length > 0 && getRowKey) {
      dataToExport = data.filter((item) => selectedKeys.includes(getRowKey(item)));
      count = dataToExport.length;
    } else {
      dataToExport = data;
      count = data.length;
    }

    if (count === 0) {
      message.warning('没有选中的数据可导出');
      return;
    }

    if (type === 'market') {
      exportMarketData(dataToExport as unknown as MarketDataExport[], format, options);
    } else {
      if (format === 'csv') {
        exportToCSV(dataToExport, options);
      } else {
        exportToExcel(dataToExport, options);
      }
    }

    onExportComplete?.(format, count);
  };

  // 下拉菜单选项
  const menuItems: MenuProps['items'] = [
    {
      key: 'excel',
      label: (
        <span>
          <FileExcelOutlined style={{ color: '#52c41a', marginRight: 8 }} />
          导出全部为 Excel
        </span>
      ),
      onClick: () => doExport('excel', false),
    },
    {
      key: 'csv',
      label: (
        <span>
          <FileTextOutlined style={{ color: '#1890ff', marginRight: 8 }} />
          导出全部为 CSV
        </span>
      ),
      onClick: () => doExport('csv', false),
    },
  ];

  // 如果有选中项，添加导出选中项选项
  if (selectedKeys.length > 0) {
    menuItems.push({ type: 'divider' });
    menuItems.push({
      key: 'selected-excel',
      label: (
        <span>
          <FileExcelOutlined style={{ color: '#52c41a', marginRight: 8 }} />
          导出选中 ({selectedKeys.length} 项) 为 Excel
        </span>
      ),
      onClick: () => doExport('excel', true),
    });
    menuItems.push({
      key: 'selected-csv',
      label: (
        <span>
          <FileTextOutlined style={{ color: '#1890ff', marginRight: 8 }} />
          导出选中 ({selectedKeys.length} 项) 为 CSV
        </span>
      ),
      onClick: () => doExport('csv', true),
    });
  }

  const isDisabled = disabled || !data || data.length === 0;

  return (
    <Dropdown
      menu={{ items: menuItems }}
      placement="bottomRight"
      disabled={isDisabled}
    >
      <Button
        type="default"
        icon={<DownloadOutlined />}
        disabled={isDisabled}
        style={style}
        className={className}
      >
        导出
      </Button>
    </Dropdown>
  );
}

export default ExportButton;
