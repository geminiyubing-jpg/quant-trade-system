import React from 'react';
import { Select } from 'antd';
import { useTranslation } from 'react-i18next';
import { GlobalOutlined } from '@ant-design/icons';
import './LanguageSwitcher.css';

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();

  const handleChange = (value: string) => {
    i18n.changeLanguage(value);
    // 保存到 localStorage
    localStorage.setItem('language', value);
  };

  const languages = [
    { value: 'zh_CN', label: '简体中文', icon: '🇨🇳' },
    { value: 'en_US', label: 'English', icon: '🇺🇸' },
  ];

  return (
    <Select
      className="language-switcher"
      value={i18n.language}
      onChange={handleChange}
      style={{ width: 120 }}
      suffixIcon={<GlobalOutlined />}
    >
      {languages.map((lang) => (
        <Select.Option key={lang.value} value={lang.value}>
          <span className="language-option">
            <span className="language-icon">{lang.icon}</span>
            <span className="language-label">{lang.label}</span>
          </span>
        </Select.Option>
      ))}
    </Select>
  );
};

export default LanguageSwitcher;
