import { Card } from 'antd';
import { useTranslation } from 'react-i18next';

const Backtest: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('backtest.title')}</h1>
      <Card>
        <p>{t('backtest.developmentInProgress')}</p>
      </Card>
    </div>
  );
};

export default Backtest;
