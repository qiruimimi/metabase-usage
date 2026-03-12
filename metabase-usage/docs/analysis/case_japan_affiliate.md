# 案例分析：日本 Affiliate 收入分析 (Question 4461)

## 业务背景

**场景**: 日本市场 Affiliate 收入数据追踪  
**目的**: 分析日本用户的支付发票趋势，监控 Affiliate 渠道收入  
**Collection**: japan-affiliate-data (455)

---

## 数据模型 (三层 Join)

```
主订单表 (Model 2206)
    ↓ Left Join
发票表 (Model 2205) - 关联条件: invoice_id = id
    ↓ Left Join
订阅宽表 (Model 728) - 关联条件: invoice_token + subscription_token (双重确认)
```

### Join 1: 基础关联
```json
{
  "strategy": "left-join",
  "alias": "ods_payment_invoice_s_d",
  "condition": [
    "=",
    ["field", "invoice_id", {"base-type": "type/BigInteger"}],
    ["field", "id", {"base-type": "type/BigInteger", "join-alias": "ods_payment_invoice_s_d"}]
  ],
  "source-table": "card__2205"
}
```

### Join 2: 复合条件关联 (重点)
```json
{
  "alias": "dws_coohom_trd_daily_toc_invoice_s_d - invoice_token",
  "strategy": "left-join",
  "condition": [
    "and",
    ["=",
      ["field", "invoice_token", {"join-alias": "ods_payment_invoice_s_d"}],
      ["field", "invoice_token", {"join-alias": "dws_coohom_trd_daily_toc_invoice_s_d - invoice_token"}]
    ],
    ["=",
      ["field", "subscription_token", {"join-alias": "ods_payment_invoice_s_d"}],
      ["field", "subscription_token", {"join-alias": "dws_coohom_trd_daily_toc_invoice_s_d - invoice_token"}]
    ]
  ],
  "source-table": "card__728"
}
```

**关键点**: 使用 `and` 组合两个字段的匹配，确保数据唯一性

---

## 筛选条件

### 三层 Filter 组合
```json
["and",
  // 1. 必须有发票ID
  ["not-null", ["field", "invoice_id", {"base-type": "type/BigInteger"}]],
  
  // 2. 最近1年数据（含当前）
  ["time-interval", 
    ["field", "created", {"base-type": "type/DateTime"}], 
    -1, "year", 
    {"include-current": true}
  ],
  
  // 3. 仅日本用户
  ["=", 
    ["field", "country_chs", {"join-alias": "..."}], 
    "日本"
  ]
]
```

---

## 聚合分析

| 指标 | MBQL | 业务含义 |
|------|------|----------|
| 总记录 | `["count"]` | 所有支付记录数 |
| 有发票记录 | `["aggregation-options", ["count-where", ["not-null", ...]], ...]` | 成功开票的记录数 |
| 总收入 | `["sum", ["field", "amt_usd", ...]]` | Affiliate 收入金额(USD) |

### count-where vs distinct+if

| 方式 | 用途 | 示例 |
|------|------|------|
| `count-where` | 统计满足条件的行数 | 有发票的记录数 |
| `distinct + if` | 去重后统计 | 支付成功的用户数 |

---

## 分组维度

按**支付成功日期**按周分组：
```json
["field", "pay_success_date", {
  "base-type": "type/DateTime",
  "join-alias": "dws_coohom_trd_daily_toc_invoice_s_d - invoice_token",
  "temporal-unit": "week"
}]
```

---

## Dashboard 设计

### 筛选项配置

| 参数 | 类型 | 默认值 | 用途 |
|------|------|--------|------|
| 日期范围 | `date/all-options` | past30days | 过滤时间范围 |
| 时间粒度 | `temporal-unit` | week | 切换日/周/月视图 |

### 参数映射
```json
{
  "parameter_id": "date_param_1",
  "card_id": 4461,
  "target": ["dimension", ["field", "pay_success_date", {"base-type": "type/DateTime"}]]
}
```

---

## 学习要点

### 1. 多层 Join 的最佳实践
```
主表
  → 维度表1 (单字段关联)
    → 维度表2 (复合字段关联，用 and)
```

### 2. 筛选条件的组合策略
- 基础筛选: 非空、时间范围
- 业务筛选: 国家/地区
- 时间筛选: time-interval 相对时间

### 3. 聚合指标的选择
- 行数统计 → `count`
- 条件行数 → `count-where`
- 去重计数 → `distinct + if`
- 数值汇总 → `sum/avg`

---

## 访问链接

- **Question**: https://kmb.qunhequnhe.com/question/4461
- **Dashboard**: https://kmb.qunhequnhe.com/dashboard/346
- **Collection**: https://kmb.qunhequnhe.com/collection/455

---

## 相关文档

- [MBQL 构建指南](../../docs/api/MBQL_BUILD_GUIDE.md)
- [复合 Join 条件](../../docs/api/MBQL_BUILD_GUIDE.md#48-高级复合条件-join)
- [count-where 用法](../../docs/api/MBQL_BUILD_GUIDE.md#49-高级count-where-条件计数)
