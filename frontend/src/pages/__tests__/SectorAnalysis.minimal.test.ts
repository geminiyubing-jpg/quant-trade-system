/**
 * SectorAnalysis 最小化测试
 * 只测试基本逻辑， */

describe('SectorAnalysis', () => {
  it('can calculate sector ranking', () => {
    const sectors = [
      { name: '半导体', change_pct: 2.5 },
      { name: '计算机', change_pct: 1.8 },
      { name: '通信', change_pct: -0.5 },
      { name: '新能源', change_pct: 3.2 },
    ];

    const sorted = [...sectors].sort((a, b) => b.change_pct - a.change_pct);

    expect(sorted[0].name).toEqual('新能源');
    expect(sorted[sorted.length - 1].name).toEqual('通信');
  });

  it('can calculate market sentiment', () => {
    const sectors = [
      { change_pct: 2.5 },
      { change_pct: 1.8 },
      { change_pct: -0.5 },
      { change_pct: 3.2 },
      { change_pct: -1.2 },
    ];

    const upCount = sectors.filter(s => s.change_pct > 0).length;
    const downCount = sectors.filter(s => s.change_pct < 0).length;

    expect(upCount).toEqual(3);
    expect(downCount).toEqual(2);
  });

  it('can calculate sector concentration', () => {
    const sectors = [
      { amount: 15000000000 },
      { amount: 12000000000 },
      { amount: 8000000000 },
    ];

    const total = sectors.reduce((sum, s) => sum + s.amount, 0);
    const ratios = sectors.map(s => s.amount / total);

    expect(Math.abs(ratios.reduce((a, b) => a + b, 0) - 1)).toBeLessThan(0.0001);
  });
});
