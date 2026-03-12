/**
 * SectionHeader - 分组标题组件
 */

import React, { memo } from 'react';
import { motion } from 'framer-motion';
import { ChevronRight, Settings } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface SectionHeaderProps {
  title: string;
  onMoreClick?: () => void;
  onManageClick?: () => void;
  showManage?: boolean;
}

const SectionHeader: React.FC<SectionHeaderProps> = memo(({
  title,
  onMoreClick,
  onManageClick,
  showManage = false,
}) => {
  const { t } = useTranslation();

  return (
    <motion.div
      className="section-header"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <h3 className="section-title">{title}</h3>
      <div className="section-actions">
        {showManage && (
          <button
            className="action-button manage"
            onClick={onManageClick}
            title={t('marketPulse.section.manage')}
          >
            <Settings size={14} />
            <span>{t('marketPulse.section.manage')}</span>
          </button>
        )}
        <button
          className="action-button more"
          onClick={onMoreClick}
          title={t('marketPulse.section.more')}
        >
          <span>{t('marketPulse.section.more')}</span>
          <ChevronRight size={14} />
        </button>
      </div>
    </motion.div>
  );
});

SectionHeader.displayName = 'SectionHeader';

export default SectionHeader;
