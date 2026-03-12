# Metabase 任务质量保证检查清单 (QA Checklist)

> 萝卜的自我要求：每次完成任务前必须逐项检查

---

## 🎯 创建 Question 前检查

### 1. 筛选条件设计
- [ ] **是否硬编码了时间筛选？**
  - ❌ 不要在 Question 里写死 `time-interval`
  - ✅ 如果要用 Dashboard 参数控制，Question 里只留必要的业务筛选（如 country = "日本"）
  - ✅ 时间范围完全交给 Dashboard Filter

### 2. 字段别名设置
- [ ] **所有聚合字段都有中文 display-name 吗？**
  ```json
  // ✅ 正确
  ["aggregation-options", ["count"], {"name": "记录数", "display-name": "记录数"}]
  
  // ❌ 错误 - 会显示英文
  ["count"]
  ```

### 3. Join 别名简化
- [ ] **Join 别名是否过长/难理解？**
  - ❌ `dws_coohom_trd_daily_toc_invoice_s_d - invoice_token`
  - ✅ `detail_table` 或 `订阅明细表`

---

## 🎯 创建 Dashboard 前检查

### 4. 参数映射验证
- [ ] **参数目标的字段引用完整吗？**
  ```json
  // ✅ 必须包含 join-alias
  ["field", "pay_success_date", {
      "base-type": "type/DateTime",
      "join-alias": "detail_table"  // 不能省略！
  }]
  ```

### 5. Question 与 Dashboard 参数兼容性
- [ ] **Question 没有硬编码和 Dashboard 参数冲突的筛选**
- [ ] **Dashboard 参数能正确覆盖 Question 的默认筛选范围**

---

## 🎯 测试验证流程

### 6. 基础功能测试
- [ ] **Question 基础查询能返回数据吗？**
  ```bash
  curl -X POST /api/card/{id}/query
  # 期望: 200 或 202，有数据行
  ```

### 7. 带参数测试
- [ ] **带 Dashboard 参数能正常运行吗？**
  ```bash
  curl -X POST /api/card/{id}/query \
    -d '{"parameters": [{"type": "date/all-options", "value": "past30days"}]}'
  ```

### 8. 可视化检查
- [ ] **图表中显示的是中文别名吗？**
- [ ] **不同单位的指标没有混在同一个轴上吗？**
  - 人数 (人) 和 金额 ($) 要分开或转换为比率

---

## 🎯 常见错误 & 解决方案

| 错误现象 | 原因 | 解决方案 |
|---------|------|----------|
| Dashboard 参数不生效 | Question 硬编码了冲突的筛选 | 移除 Question 里的 time-interval，交给 Dashboard 控制 |
| 图表显示英文 | 缺少 aggregation-options 的 display-name | 给所有聚合加 `"display-name": "中文名"` |
| 参数映射失败 | 缺少 join-alias | 参数目标字段必须包含完整的 join-alias |
| 500 错误 | 复合条件语法错误 | 检查 `and`/`or` 的嵌套结构 |

---

## 🎯 标准工作流程

```
1. 设计 Question
   ↓
2. 检查是否硬编码时间筛选 → 移除，交给 Dashboard
   ↓
3. 设置所有字段的中文别名
   ↓
4. 简化 Join 别名
   ↓
5. 测试 Question 基础查询
   ↓
6. 创建 Dashboard
   ↓
7. 添加参数并正确映射（含 join-alias）
   ↓
8. 测试 Dashboard 带参数运行
   ↓
9. 检查可视化效果（中文、单位）
   ↓
10. 完成
```

---

## 🎯 修改 vs 新建原则

### 优先直接修改现有 Question
- [ ] **Question 已经有下游引用（Dashboard）？** → **必须直接修改，不要新建！**
  ```
  正确流程：
  GET /api/card/{id} → 修改配置 → PUT /api/card/{id}
  
  错误做法：
  DELETE 旧 Question → 新建 Question → 更新所有 Dashboard 引用
  ```

- [ ] **新建 Question 的场景（仅限）：**
  - 全新的分析需求
  - 旧 Question 完全不可用，没有下游引用
  - 明确需要保留旧版本做对比

### 删除旧数据的规范
- [ ] **删除前确认：**
  - 该 Question 没有被任何 Dashboard 引用
  - 该 Question 没有历史报告依赖
  - 已通知相关人员

---

## 🎯 Dashboard 参数绑定完整检查清单

### 创建/修改 Dashboard 时必查
- [ ] **Question 有参数定义吗？**
  ```json
  // Question 里必须有
  "parameters": [
    {"id": "date_param_1", "name": "日期范围", "type": "date/all-options", ...}
  ]
  ```
  
- [ ] **Dashboard 参数和 Question 参数 ID 一致吗？**
  - Dashboard: `"id": "date_param_1"`
  - Question: `"id": "date_param_1"` ✓ 必须相同！
  
- [ ] **参数映射的 target 字段完整吗？**
  ```json
  // 必须包含 join-alias！
  "target": ["dimension", ["field", "pay_success_date", {
    "base-type": "type/DateTime",
    "join-alias": "detail_table"  // ← 不能省略
  }]]
  ```

### 常见参数绑定错误

| 现象 | 原因 | 解决 |
|------|------|------|
| 筛选项显示"无效参数" | Question 没有 parameters 定义 | 给 Question 添加 parameters 数组 |
| 参数不生效 | 参数 ID 不匹配 | 确保 Dashboard 和 Question 的 id 完全一致 |
| 500 错误 | 缺少 join-alias | 参数映射的 target 必须包含完整字段引用 |

### 正确的参数配置流程

```
1. Question 配置
   "parameters": [
     {"id": "param_1", "name": "日期", "type": "date/all-options"}
   ]
   
2. Dashboard 配置
   "parameters": [
     {"id": "param_1", ...}  // id 必须和 Question 一致
   ]
   
3. Dashcard 参数映射
   "parameter_mappings": [
     {
       "parameter_id": "param_1",  // Dashboard 参数 ID
       "card_id": 123,
       "target": ["dimension", ["field", "date", {"join-alias": "table"}]]
     }
   ]
```

---

## 🎯 Dashboard 布局最佳实践

### 宽度模式选择

| 模式 | 配置 | 适用场景 |
|------|------|----------|
| **Full** | `"width": "full"` | 数据看板、大屏幕展示 |
| **Default** | `"width": "fixed"` 或省略 | 标准报表、嵌入页面 |

**对比**：
- Full 模式：卡片可以占满整个屏幕宽度，适合复杂数据展示
- Fixed 模式：居中显示，宽度固定，适合简洁报表

### 卡片尺寸建议

| 用途 | 尺寸 | 位置 |
|------|------|------|
| 主图表 | 16x8 或 18x8 | 左侧/上方 |
| 辅助图表 | 8x8 或 6x8 | 右侧/下方 |
| 明细表格 | 24x8 | 单独一行 |
| KPI 指标 | 6x4 | 顶部一排 |

### 常见布局

```
Full Width 模式示例:
┌────────────────────────────────────────────────────────┐
│ [KPI 1] [KPI 2] [KPI 3] [KPI 4]       6x4 each       │
├──────────────────────────────┬─────────────────────────┤
│                              │                         │
│   主趋势图 (16x8)            │   辅助图表 (8x8)       │
│                              │                         │
├──────────────────────────────┴─────────────────────────┤
│                                                        │
│   明细数据表格 (24x8)                                  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 🎯 团队协作注意事项

### 修改 Dashboard 前
- [ ] 检查当前布局配置（width, cards 位置）
- [ ] 记录现有卡片引用关系
- [ ] 确认修改影响范围

### API vs 界面操作
- 界面修改：实时生效，适合调整布局
- API 修改：适合批量操作，但注意同步问题

---

## 📝 本次任务复盘 (2026-03-12 日本 Affiliate Dashboard)

### 犯的错误
1. ❌ Question 硬编码了 `time-interval`，和 Dashboard 参数冲突
2. ❌ 聚合字段缺少中文 display-name
3. ❌ 参数映射缺少 `join-alias`
4. ❌ 创建明细 Question 时忘记加 `visualization_settings: {}`

### 修复措施
1. ✅ 创建修复版 Question 4463/4464，移除硬编码时间筛选
2. ✅ 添加中文别名："记录数"、"invoice数"、"总收入(USD)"
3. ✅ 确保参数映射包含完整的字段引用

### 本次任务犯的错误（完整列表）

1. **Question 参数定义缺失** ❌
   - 错误：创建 Question 时没有添加 `parameters` 数组
   - 后果：Dashboard 筛选项显示"无效参数"
   - 解决：Question 必须包含和 Dashboard 匹配的参数定义

2. **参数 ID 不匹配** ❌
   - 错误：Dashboard 绑定了 `date_param_1`，但 Question 里没有这个 ID
   - 后果：参数无法传递
   - 解决：确保两边 ID 完全一致

3. **删除 Question 后未更新 Dashboard** ❌
   - 错误：删除 4463 后 Dashboard 还引用它
   - 后果：Dashboard 显示错误
   - 解决：删除 Question 前先检查 Dashboard 引用，或同时更新 Dashboard

4. **MBQL Question 参数传递方式混淆** ❌
   - 错误：以为 MBQL 和 Native SQL 参数配置方式相同
   - 后果：template-tags 配置无效
   - 解决：MBQL 用 `parameters` 数组，Native SQL 用 `template-tags`

5. **缺少完整的测试验证** ❌
   - 错误：创建后没有检查参数绑定是否生效
   - 后果：用户发现后才能修复
   - 解决：创建后必须测试带参数的查询

### 正确的完整流程（以后必须遵守）

```
创建 Question
  ↓
添加 parameters 定义（和 Dashboard 计划的一致）
  ↓
测试 Question 基础查询
  ↓
创建 Dashboard
  ↓
添加参数（id 和 Question 一致）
  ↓
添加卡片 + 参数映射（含 join-alias）
  ↓
测试带参数的 Dashboard 查询
  ↓
检查可视化效果
  ↓
完成
```

---
萝卜 🥕
2026-03-12
