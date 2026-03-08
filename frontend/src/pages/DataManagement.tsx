import { Card } from 'antd';
import { useTranslation } from 'react-i18next';

const DataManagement: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('data.title')}</h1>
      <Card>
        <p>{t('data.developmentInProgress')}</p>
      </Card>
    </div>
  );
};

export default DataManagement;
