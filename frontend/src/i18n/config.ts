import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import zh_CN from './locales/zh_CN.json';
import en_US from './locales/en_US.json';

// 配置 i18next
i18n
  .use(initReactI18next)
  .init({
    resources: {
      zh_CN: { translation: zh_CN },
      en_US: { translation: en_US },
    },
    lng: 'zh_CN', // 默认语言
    fallbackLng: 'zh_CN', // 回退语言
    interpolation: {
      escapeValue: false, // React 已经做了 XSS 防护
    },
    react: {
      useSuspense: false, // 禁用 Suspense
    },
  });

export default i18n;
