# 彭博主题设计规范使用指南

> **版本**: v1.0.0
> **项目**: quant-trade-system
> **适用范围**: 系统所有前端页面
> **生效日期**: 2026-03-08

---

## 🎯 核心原则

### 1. 统一性原则
✅ **所有前端页面必须使用彭博主题样式**
✅ **禁止**使用白色或浅色背景
✅ **禁止**自定义颜色（必须使用 CSS 变量）

### 2. 数据优先原则
✅ 数据展示使用等宽数字字体
✅ 价格变化使用闪烁动画
✅ 涨跌使用标准颜色（绿涨红跌）

### 3. 专业性原则
✅ 黑色背景传递专业感
✅ 紧凑的间距提高信息密度
✅ 避免过度装饰

---

## 📨 色彩系统

### 涨跌颜色（金融标准）
```css
/* 上涨 - 绿色 */
color: var(--bb-up);

/* 下跌 - 红色 */
color: var(--bb-down);

/* 持平 - 黄色 */
color: var(--bb-neutral);
```

### 背景层次
```css
/* 主要内容区 - 纯黑 */
background: var(--bb-bg-primary);

/* 次要内容区 - 深灰 */
background: var(--bb-bg-secondary);

/* 卡片/面板 - 悬浮层 */
background: var(--bb-bg-elevated);
```

---

## 📝 字体使用

### 数据显示
```html
<!-- 价格显示 -->
<span class="price price-up">125.50</span>

<!-- 百分比 -->
<span class="percentage">2.5</span>

<!-- 数量 -->
<span class="numeric">1,000,000</span>
```

### 文本层级
```css
/* 主标题 */
font-size: var(--text-3xl);  /* 20px */

/* 正文 */
font-size: var(--text-base);  /* 13px */

/* 辅助信息 */
font-size: var(--text-sm);    /* 12px */
```

---

## 🎯 组件使用示例

### 数据表格
```html
<table class="bb-table">
  <thead>
    <tr>
      <th>代码</th>
      <th class="numeric">价格</th>
      <th class="numeric">涨跌幅</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>AAPL</td>
      <td class="numeric price-up">125.50</td>
      <td class="numeric text-up">+2.5</td>
    </tr>
  </tbody>
</table>
```

### 按钮
```html
<!-- 主要按钮 -->
<button class="bb-button bb-button-primary">
  执行交易
</button>

<!-- 买入按钮 -->
<button class="bb-button bb-button-up">
  买入
</button>

<!-- 卖出按钮 -->
<button class="bb-button bb-button-down">
  卖出
</button>
```

### 价格闪烁效果
```javascript
// 价格更新时添加闪烁动画
function updatePrice(element, newPrice, isUp) {
  element.textContent = newPrice;
  element.className = `price ${isUp ? 'price-up flash-up' : 'price-down flash-down'}`;

  // 动画结束后移除闪烁类
  setTimeout(() => {
    element.classList.remove('flash-up', 'flash-down');
  }, 500);
}
```

---

## ⚡ 性能优化

### 1. 价格更新优化
```javascript
// 使用 requestAnimationFrame 优化性能
function updatePrices(data) {
  requestAnimationFrame(() => {
    data.forEach(item => {
      const el = document.getElementById(`price-${item.symbol}`);
      if (el) updatePrice(el, item.price, item.isUp);
    });
  });
}
```

### 2. 批量 DOM 更新
```javascript
// 使用 DocumentFragment 减少重排
function updateTable(rows) {
  const fragment = document.createDocumentFragment();
  rows.forEach(row => {
    const tr = createTableRow(row);
    fragment.appendChild(tr);
  });
  tbody.appendChild(fragment);
}
```

---

## 🚫 禁止事项

### ❌ 绝对禁止
1. **禁止** 使用白色或浅色背景
2. **禁止** 使用非等宽数字字体显示数据
3. **禁止** 使用 float 计算金额（前端也要用 Decimal）
4. **禁止** 自定义颜色（必须使用 CSS 变量）
5. **禁止** 使用过度动画效果

### ⚠️ 谨慎使用
1. 慎用渐变色（彭博风格不常用）
2. 慎用圆角（保持方正专业感）
3. 慎用阴影（黑色背景阴影效果不明显）

---

## ✅ 开发检查清单

页面开发完成后，必须检查：

- [ ] 所有页面使用彭博主题样式
- [ ] 涨跌颜色使用正确（绿涨红跌）
- [ ] 数据使用等宽数字字体
- [ ] 文字对比度 ≥ 4.5:1
- [ ] 价格变化有闪烁动画
- [ ] 所有输入框有聚焦效果
- [ ] 响应式适配正常
- [ ] 性能测试通过（60fps）

---

## 📞 团队联系

**主题维护**: 角色 C（全栈开发工程师）
**设计审核**: 角色 B（金融系统架构师）

---

**版本**: v1.0.0
**最后更新**: 2026-03-08
