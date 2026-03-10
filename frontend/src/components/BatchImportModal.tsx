/**
 * ==============================================
 * 批量导入股票代码弹窗组件
 * ==============================================
 */

import React, { useState } from 'react';
import { Modal, Input, Button, Space, message, Typography, Divider, Alert } from 'antd';
import { ImportOutlined, ClearOutlined, FileTextOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

interface BatchImportModalProps {
  visible: boolean;
  existingSymbols: string[];
  onImport: (symbols: string[]) => void;
  onClose: () => void;
  maxSymbols?: number;
}

const BatchImportModal: React.FC<BatchImportModalProps> = ({
  visible,
  existingSymbols,
  onImport,
  onClose,
  maxSymbols = 100,
}) => {
  const { t } = useTranslation();
  const [inputValue, setInputValue] = useState('');
  const [importing, setImporting] = useState(false);

  // 解析输入的股票代码
  const parseSymbols = (input: string): string[] => {
    const lines = input.split(/[\n,;，；\s]+/);
    const symbols: string[] = [];

    for (const line of lines) {
      const trimmed = line.trim().toUpperCase();
      // 验证股票代码格式（6位数字 + 可选后缀）
      const match = trimmed.match(/^(\d{6})(\.(SZ|SH|BJ))?$/);
      if (match) {
        const code = match[1];
        const suffix = match[3] || inferMarket(code);
        symbols.push(`${code}.${suffix}`);
      }
    }

    return [...new Set(symbols)]; // 去重
  };

  // 根据代码推断市场
  const inferMarket = (code: string): string => {
    if (code.startsWith('6')) return 'SH';
    if (code.startsWith('0') || code.startsWith('3')) return 'SZ';
    if (code.startsWith('4') || code.startsWith('8')) return 'BJ';
    return 'SZ'; // 默认深交所
  };

  // 执行导入
  const handleImport = () => {
    setImporting(true);

    try {
      const parsedSymbols = parseSymbols(inputValue);

      if (parsedSymbols.length === 0) {
        message.warning(t('realtime.subscribeWarning'));
        setImporting(false);
        return;
      }

      // 过滤已存在的代码
      const newSymbols = parsedSymbols.filter((s) => !existingSymbols.includes(s));
      const duplicateCount = parsedSymbols.length - newSymbols.length;

      // 检查是否超过限制
      const availableSlots = maxSymbols - existingSymbols.length;
      if (newSymbols.length > availableSlots) {
        message.warning(t('realtime.subscribeLimit'));
        setImporting(false);
        return;
      }

      if (newSymbols.length > 0) {
        onImport(newSymbols);
        message.success(t('realtime.batchImportSuccess').replace('{count}', String(newSymbols.length)));
      }

      if (duplicateCount > 0) {
        message.warning(t('realtime.batchImportWarning').replace('{count}', String(duplicateCount)));
      }

      // 清空输入并关闭
      setInputValue('');
      onClose();
    } catch (error) {
      console.error('批量导入失败:', error);
      message.error('导入失败');
    } finally {
      setImporting(false);
    }
  };

  // 清空输入
  const handleClear = () => {
    setInputValue('');
  };

  // 示例代码
  const exampleSymbols = `000001.SZ
000002.SZ
600000.SH
600036.SH
300001.SZ`;

  return (
    <Modal
      title={
        <Space>
          <ImportOutlined style={{ color: '#00d4ff' }} />
          <span>{t('realtime.batchImportTitle')}</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={600}
      centered
      className="batch-import-modal"
      styles={{
        body: { padding: '24px' },
      }}
    >
      <Alert
        message={`${t('realtime.subscribeLimit')} | ${t('realtime.stats.total')}: ${existingSymbols.length}/${maxSymbols}`}
        type="info"
        showIcon
        style={{ marginBottom: '16px' }}
      />

      <TextArea
        placeholder={t('realtime.batchImportPlaceholder')}
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        rows={10}
        style={{
          fontFamily: '"JetBrains Mono", "Fira Code", monospace',
          fontSize: '13px',
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(0, 212, 255, 0.3)',
          color: '#e0e0e0',
        }}
      />

      <Divider />

      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <Text type="secondary" style={{ fontSize: '12px' }}>
          支持格式: 000001.SZ, 000001, 或每行一个代码
        </Text>
        <Space>
          <Button
            icon={<ClearOutlined />}
            onClick={handleClear}
            style={{ color: '#a0a0a0' }}
          >
            {t('realtime.clearAll')}
          </Button>
          <Button
            type="primary"
            icon={<ImportOutlined />}
            loading={importing}
            onClick={handleImport}
            style={{
              background: 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)',
              border: 'none',
            }}
          >
            {t('realtime.batchImport')}
          </Button>
        </Space>
      </Space>

      <Divider />

      <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: '12px', borderRadius: '8px' }}>
        <Text type="secondary" style={{ fontSize: '12px', marginBottom: '8px', display: 'block' }}>
          <FileTextOutlined /> 示例格式:
        </Text>
        <Paragraph
          copyable
          style={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: '12px',
            color: '#a0a0a0',
            marginBottom: 0,
            whiteSpace: 'pre-line',
          }}
        >
          {exampleSymbols}
        </Paragraph>
      </div>

      <style>{`
        .batch-import-modal .ant-modal-content {
          background: rgba(13, 20, 24, 0.98) !important;
          border: 1px solid rgba(0, 212, 255, 0.2);
          border-radius: 12px;
        }

        .batch-import-modal .ant-modal-header {
          background: transparent !important;
          border-bottom: 1px solid rgba(0, 212, 255, 0.1);
        }

        .batch-import-modal .ant-modal-title {
          color: #f5c842 !important;
        }

        .batch-import-modal .ant-modal-close {
          color: #a0a0a0;
        }

        .batch-import-modal .ant-modal-close:hover {
          color: #00d4ff;
        }

        .batch-import-modal .ant-input::placeholder {
          color: rgba(160, 160, 160, 0.5);
        }

        .batch-import-modal .ant-input:focus {
          border-color: #00d4ff !important;
          box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
        }
      `}</style>
    </Modal>
  );
};

export default BatchImportModal;
