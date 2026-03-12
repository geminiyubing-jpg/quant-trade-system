/**
 * TopNav - 顶部导航组件
 * 包含搜索栏和分类标签
 */

import React, { useState, memo } from 'react';
import { motion } from 'framer-motion';
import {
  Search,
  Star,
  Building2,
  Coins,
  Globe,
  Globe2,
  Bitcoin,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { categoryTabs } from '../../data/marketPulseData';

interface TopNavProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  onSearch?: (query: string) => void;
}

// 图标映射
const iconMap: Record<string, React.ReactNode> = {
  Globe: <Globe size={16} />,
  Star: <Star size={16} />,
  Building2: <Building2 size={16} />,
  Coins: <Coins size={16} />,
  Globe2: <Globe2 size={16} />,
  Bitcoin: <Bitcoin size={16} />,
};

const TopNav: React.FC<TopNavProps> = memo(({ activeTab, onTabChange, onSearch }) => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    onSearch?.(query);
  };

  return (
    <div className="top-nav">
      {/* 搜索栏 */}
      <motion.div
        className={`search-bar ${isSearchFocused ? 'focused' : ''}`}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Search size={18} className="search-icon" />
        <input
          type="text"
          placeholder={t('marketPulse.searchPlaceholder')}
          value={searchQuery}
          onChange={handleSearchChange}
          onFocus={() => setIsSearchFocused(true)}
          onBlur={() => setIsSearchFocused(false)}
          className="search-input"
        />
      </motion.div>

      {/* 分类标签 */}
      <div className="category-tabs">
        <div className="tabs-scroll">
          {categoryTabs.map((tab, index) => (
            <motion.button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {iconMap[tab.icon]}
              <span>{t(`marketPulse.categories.${tab.id}`)}</span>
              {activeTab === tab.id && (
                <motion.div
                  className="tab-indicator"
                  layoutId="activeTab"
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  );
});

TopNav.displayName = 'TopNav';

export default TopNav;
