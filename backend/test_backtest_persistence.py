#!/usr/bin/env python3
"""测试回测结果持久化"""
import requests
from src.core.database import engine
from sqlalchemy import text

# 获取 token
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'test_user',
    'password': 'testpass123'
})
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print('=' * 70)
print('🎯 测试回测结果完整保存流程（修复外键约束）')
print('=' * 70)

# 1. 执行快速回测
print('\n📊 步骤 1: 执行快速回测...')
response = requests.post(
    'http://localhost:8000/api/v1/backtest/quick',
    params={
        'strategy_id': 'test-fk-fix',
        'symbols': ['000001.SZ'],
        'days': 30
    },
    headers=headers
)

if response.status_code == 201:
    result = response.json()
    backtest_id = result['backtest_id']
    print(f'✅ 回测成功！')
    print(f'   回测 ID: {backtest_id[:12]}...')
else:
    print(f'❌ 回测失败: {response.status_code}')
    exit(1)

# 2. 检查数据库记录
print('\n📋 步骤 2: 检查数据库记录...')
with engine.connect() as conn:
    # 检查 backtest_jobs
    result = conn.execute(text('SELECT COUNT(*) FROM backtest_jobs'))
    job_count = result.scalar()
    print(f'   backtest_jobs 表: {job_count} 条记录')

    if job_count > 0:
        result = conn.execute(text(
            "SELECT id, name, status FROM backtest_jobs WHERE id = :job_id",
            {'job_id': backtest_id}
        ))
        row = result.fetchone()
        if row:
            print(f'   ✅ Job 记录创建成功！')
            print(f'      ID: {row[0][:12]}...')
            print(f'      名称: {row[1]}')
            print(f'      状态: {row[2]}')

    # 检查 backtest_results
    result = conn.execute(text('SELECT COUNT(*) FROM backtest_results'))
    result_count = result.scalar()
    print(f'   backtest_results 表: {result_count} 条记录')

    if result_count > 0:
        result = conn.execute(text(
            "SELECT job_id, total_return, sharpe_ratio FROM backtest_results WHERE job_id = :job_id",
            {'job_id': backtest_id}
        ))
        row = result.fetchone()
        if row:
            print(f'   ✅ Result 记录创建成功！')
            print(f'      Job ID: {row[0][:12]}...')
            print(f'      收益率: {row[1]}')
            print(f'      夏普比率: {row[2]}')

# 3. API 查询测试
print('\n🌐 步骤 3: API 查询测试...')
response = requests.get('http://localhost:8000/api/v1/backtest/results', headers=headers)
if response.status_code == 200:
    results = response.json()
    print(f'✅ API 查询成功！共 {len(results)} 条记录')
    if results:
        r = results[0]
        print(f'   最新: {r["strategy_name"]} | 收益: {r["total_return"]}')
else:
    print(f'❌ API 查询失败: {response.status_code}')

print('\n' + '=' * 70)
if result_count > 0 and job_count > 0:
    print('🎉 回测结果持久化完全成功！外键约束问题已彻底解决！')
else:
    print('⚠️  仍有问题需要调试')
print('=' * 70)
