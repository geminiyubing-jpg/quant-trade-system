import { Card, Row, Col, Statistic } from 'antd';
import { useTranslation } from 'react-i18next';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('dashboard.title')}</h1>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title={t('dashboard.totalAssets')}
              value={1128000}
              precision={2}
              valueStyle={{ color: 'var(--bb-up)' }}
              suffix="¥"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={t('dashboard.dailyPnL')}
              value={9.3}
              precision={2}
              valueStyle={{ color: 'var(--bb-down)' }}
              suffix="%"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={t('dashboard.positionCount')}
              value={15}
              suffix="只"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={t('dashboard.runningStrategies')}
              value={3}
              suffix="个"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
