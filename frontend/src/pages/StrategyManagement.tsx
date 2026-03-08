import { Card } from 'antd';
import { useTranslation } from 'react-i18next';

const StrategyManagement: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('strategy.title')}</h1>
      <Card>
        <p>{t('strategy.developmentInProgress')}</p>
      </Card>
    </div>
  );
};

export default StrategyManagement;
