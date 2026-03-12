# Question 分析 - 日本用户发票分析

## 查询来源
URL: `https://kmb.qunhequnhe.com/question#eyJkYX...`

## 核心结构

### 数据源 (3层 Join)

```
主表: Model 2206
    ↓ Left Join
Model 2205: ods_payment_invoice_s_d
    (关联: invoice_id = id)
    ↓ Left Join  
Model 728: dws_coohom_trd_daily_toc_invoice_s_d
    (关联: invoice_token + subscription_token 双重匹配)
```

### Join 配置详解

**第一层 Join** (Model 2205):
```json
{
  "strategy": "left-join",
  "alias": "ods_payment_invoice_s_d",
  "condition": ["=", 
    ["field", "invoice_id", {"base-type": "type/BigInteger"}],
    ["field", "id", {"base-type": "type/BigInteger", "join-alias": "ods_payment_invoice_s_d"}]
  ],
  "source-table": "card__2205"
}
```

**第二层 Join** (Model 728) - **复合条件**:
```json
{
  "strategy": "left-join",
  "alias": "dws_coohom_trd_daily_toc_invoice_s_d - invoice_token",
  "condition": ["and",
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

### 聚合分析

| 聚合 | MBQL | 业务含义 |
|------|------|----------|
| count | `["count"]` | 总记录数 |
| invoice统计 | `["aggregation-options", ["count-where", ["not-null", ...]], ...]` | 有invoice_token的记录数 |
| sum | `["sum", ["field", "amt_usd", ...]]` | 总金额(USD) |

### 筛选条件

```json
["and",
  ["not-null", ["field", "invoice_id", {"base-type": "type/BigInteger"}]],
  ["time-interval", 
    ["field", "created", {"base-type": "type/DateTime"}], 
    -1, "year", 
    {"include-current": true}
  ],
  ["=", 
    ["field", "country_chs", {"join-alias": "dws_coohom_trd_daily_toc_invoice_s_d - invoice_token"}], 
    "日本"
  ]
]
```

**筛选解析**:
1. invoice_id 非空
2. 最近 1 年数据 (包含当前)
3. **日本用户** (`country_chs = "日本"`)

### 分组维度

```json
["field", "pay_success_date", {
  "base-type": "type/DateTime",
  "join-alias": "dws_coohom_trd_daily_toc_invoice_s_d - invoice_token",
  "temporal-unit": "week"
}]
```

按**周**查看支付成功日期分布

## 可视化

- **类型**: line (折线图)
- **X轴**: pay_success_date (按周)
- **Y轴**: count, invoice统计, sum (3个指标)

## 业务场景

这是一个**日本市场发票分析**看板：
- 追踪日本用户的支付发票数据
- 关联发票详情和订阅信息
- 按周查看发票数量和金额趋势
- 过滤最近一年的数据

## 学习要点

### 1. 复合 Join 条件
```json
["and",
  ["=", ["field", "invoice_token", ...], ["field", "invoice_token", ...]],
  ["=", ["field", "subscription_token", ...], ["field", "subscription_token", ...]]
]
```
用 `and` 组合多个字段匹配

### 2. count-where 聚合
```json
["aggregation-options",
  ["count-where", ["not-null", ["field", "invoice_token", ...]]],
  {"name": "invoice统计", "display-name": "invoice统计"}
]
```
统计满足特定条件的记录数

### 3. time-interval 相对时间
```json
["time-interval", ["field", "created", ...], -1, "year", {"include-current": true}]
```
- `-1`: 过去
- `"year"`: 单位
- `include-current: true`: 包含当前

---
记录时间: 2026-03-12
分析者: 萝卜 🥕
