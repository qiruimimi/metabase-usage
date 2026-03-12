# MBQL (Metabase Query Language) 构建规则详解

> 基于 Dashboard 312 实际案例总结的 MBQL 构建指南

---

## 一、MBQL 整体结构

```json
{
  "database": 4,                    // 数据库 ID
  "type": "query",                  // 固定值: query (表示 MBQL)
  "query": {
    // 核心查询配置 (以下部分都是可选的，根据需求组合)
    "source-table": "card__3953",   // 数据源: Model ID 或表名
    "joins": [...],                 // 表关联 (可选)
    "filter": [...],                // 筛选条件 (可选)
    "breakout": [...],              // 分组维度 (可选)
    "aggregation": [...],           // 聚合计算 (可选)
    "expressions": {...},           // 自定义字段 (可选)
    "order-by": [...],              // 排序 (可选)
    "limit": 100                    // 限制条数 (可选)
  }
}
```

**核心原则**: MBQL 采用 **"管道"模式**，数据流从上到下处理：
```
source-table → joins → filter → breakout → aggregation → expressions → order-by → limit
```

---

## 二、source-table (数据源)

### 2.1 引用 Model
```json
"source-table": "card__3953"   // Model ID 为 3953
```

### 2.2 引用原始表
```json
"source-table": 123   // 表的内部 ID
```

---

## 三、Field 引用规则 (核心基础)

几乎所有 MBQL 配置都基于 `field` 引用，格式统一为：

```json
["field", "字段名", {字段属性}]
```

### 3.1 基础字段引用
```json
// 基础字段
["field", "user_id", {"base-type": "type/BigInteger"}]
["field", "user_type", {"base-type": "type/Text"}]
["field", "amt_usd", {"base-type": "type/Float"}]
["field", "ds_time", {"base-type": "type/DateTime"}]
```

**base-type 类型对照**:
| 数据类型 | base-type |
|----------|-----------|
| 整数 | `type/BigInteger`, `type/Integer` |
| 浮点数 | `type/Float` |
| 字符串 | `type/Text` |
| 日期时间 | `type/DateTime` |
| 日期 | `type/Date` |
| 布尔 | `type/Boolean` |

### 3.2 时间字段特殊配置

时间字段可以用 `temporal-unit` 指定时间粒度：

```json
// 按天分组
["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "day"}]

// 按周分组
["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "week"}]

// 按月分组
["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "month"}]

// 按季度分组
["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "quarter"}]

// 按年分组
["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "year"}]
```

### 3.3 关联表字段引用

当使用 Join 后，引用关联表字段需要加 `join-alias`：

```json
["field", "country", {"base-type": "type/Text", "join-alias": "用户维度表"}]
```

---

## 四、Filter (筛选条件)

### 4.1 Filter 基本结构

Filter 是一个嵌套的数组结构，第一个元素是**操作符**，后面是**操作数**。

```json
["操作符", 操作数1, 操作数2, ...]
```

### 4.2 比较运算符

| 操作符 | 语法 | 示例 |
|--------|------|------|
| **等于** | `["=", field, value]` | `["=", ["field", "user_type", {...}], "新签"]` |
| **不等于** | `["!=", field, value]` | `["!=", ["field", "status", {...}], "deleted"]` |
| **大于** | `[">", field, value]` | `[">", ["field", "amt_usd", {...}], 100]` |
| **小于** | `["<", field, value]` | `["<", ["field", "amt_usd", {...}], 1000]` |
| **大于等于** | `[">=", field, value]` | `[">=", ["field", "ds_time", {...}], "2026-01-01"]` |
| **小于等于** | `["<=", field, value]` | `["<=", ["field", "ds_time", {...}], "2026-12-31"]` |
| **范围** | `["between", field, min, max]` | `["between", ["field", "ds_time", {...}], "2026-01-01", "2026-03-01"]` |

### 4.3 空值判断

```json
// 为空 (IS NULL)
["is-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]]

// 非空 (IS NOT NULL)
["not-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]]
```

**实际案例** (Card 3954):
```json
"filter": [
  "=",
  ["field", "user_type", {"base-type": "type/Text"}],
  "新签"
]
```

### 4.4 逻辑组合

```json
// AND 组合
["and",
  ["=", ["field", "user_type", {...}], "新签"],
  ["not-null", ["field", "pay_success_date", {...}]]
]

// OR 组合
["or",
  ["=", ["field", "user_type", {...}], "新签"],
  ["=", ["field", "user_type", {...}], "升级"]
]
```

### 4.5 字符串匹配

```json
// 包含 (contains)
["contains", ["field", "sku", {...}], "elite"]

// 以...开头 (starts-with)
["starts-with", ["field", "email", {...}], "admin"]

// 以...结尾 (ends-with)
["ends-with", ["field", "email", {...}], "@company.com"]
```

### 4.6 多值匹配

```json
// 等于多个值中的任意一个
["=",
  ["field", "country", {...}],
  ["美国", "日本", "新加坡"]
]
```

### 4.7 高级：复合条件 Join

当需要基于多个字段匹配关联表时，使用 `and` 组合：

**场景**：发票和订阅通过 `invoice_token` + `subscription_token` 双重确认匹配

```json
{
  "alias": "订阅明细表",
  "strategy": "left-join",
  "condition": [
    "and",
    ["=",
      ["field", "invoice_token", {"join-alias": "发票表"}],
      ["field", "invoice_token", {"join-alias": "订阅明细表"}]
    ],
    ["=",
      ["field", "subscription_token", {"join-alias": "发票表"}],
      ["field", "subscription_token", {"join-alias": "订阅明细表"}]
    ]
  ],
  "source-table": "card__728"
}
```

**实际案例**：日本 Affiliate 收入分析 (Question 4461)
- 第一层 Join：主表关联发票表 (invoice_id)
- 第二层 Join：发票表关联订阅宽表 (invoice_token + subscription_token 双重匹配)

### 4.8 高级：count-where 条件计数

统计满足特定条件的记录数（不是去重）：

```json
["aggregation-options",
  ["count-where", 
    ["not-null", ["field", "invoice_token", {...}]]
  ],
  {"name": "有发票记录数", "display-name": "有发票记录数"}
]
```

**与 distinct + if 的区别**：
- `distinct + if`：去重后计数（如支付成功人数）
- `count-where`：不去重，统计满足条件的行数

### 4.9 高级：相对时间筛选

```json
["time-interval", 
  ["field", "created", {"base-type": "type/DateTime"}], 
  -1,                    // 负数=过去，正数=未来
  "year",                // 单位：day/week/month/year
  {"include-current": true}  // 是否包含当前周期
]
```

**示例**：
- 最近30天：`["time-interval", field, -30, "day"]`
- 最近4周：`["time-interval", field, -4, "week"]`
- 本月：`["time-interval", field, "current", "month"]`
- 最近1年（含当前）：`["time-interval", field, -1, "year", {"include-current": true}]`

---

## 五、Breakout (分组维度)

### 5.1 单维度分组

```json
"breakout": [
  ["field", "user_type", {"base-type": "type/Text"}]
]
```

### 5.2 多维度分组

```json
"breakout": [
  ["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "day"}],
  ["field", "sku", {"base-type": "type/Text"}]
]
```

**实际案例** (Card 3957 - 分 SKU 柱状图):
```json
"breakout": [
  ["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "day"}],
  ["field", "sku", {"base-type": "type/Text"}]
]
```

### 5.3 带关联表的分组

```json
"breakout": [
  ["field", "country", {"base-type": "type/Text", "join-alias": "用户维度表"}]
]
```

**实际案例** (Card 3959):
```json
"breakout": [
  ["field", "用户有效国家（中文）- 优先取活跃国家，无则取注册国家",
    {"base-type": "type/Text", "join-alias": "Coohom用户维度宽表（旧） - user_id"}]
]
```

---

## 六、Aggregation (聚合计算)

### 6.1 基础聚合

| 聚合 | MBQL | 说明 |
|------|------|------|
| **计数** | `["count"]` | 统计行数 |
| **去重计数** | `["distinct", field]` | 去重后计数 |
| **求和** | `["sum", field]` | 数值求和 |
| **平均值** | `["avg", field]` | 数值平均 |
| **最小值** | `["min", field]` | 最小值 |
| **最大值** | `["max", field]` | 最大值 |
| **标准差** | `["stddev", field]` | 标准差 |

### 6.2 带自定义名称的聚合

使用 `aggregation-options` 包装，可以指定显示名称：

```json
["aggregation-options",
  ["count"],
  {"name": "订单数", "display-name": "订单数"}
]

["aggregation-options",
  ["distinct", ["field", "user_id", {...}]],
  {"name": "uv", "display-name": "去重用户数"}
]

["aggregation-options",
  ["sum", ["field", "amt_usd", {...}]],
  {"name": "gmv", "display-name": "GMV"}
]
```

### 6.3 条件聚合 (重要)

统计满足特定条件的记录，使用 `if` 嵌套：

```json
["aggregation-options",
  ["distinct",
    ["if",
      [[["not-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]],
        ["field", "user_id", {"base-type": "type/BigInteger"}]]]
    ]
  ],
  {"name": "支付成功人数", "display-name": "支付成功人数"}
]
```

**结构解析**:
```
aggregation-options
  └── distinct
        └── if
              └── [条件, 值]
                  └── 条件: [not-null, field]
```

**逻辑说明**:
- `if` 接收一个数组 `[条件, 值]`
- 条件满足时返回 `值`，否则返回 null
- `distinct` 统计非 null 的去重值

### 6.4 多聚合组合

```json
"aggregation": [
  ["aggregation-options", ["count"], {"name": "pv", "display-name": "PV"}],
  ["aggregation-options", ["distinct", ["field", "user_id", {...}]], {"name": "uv", "display-name": "UV"}],
  ["aggregation-options",
    ["distinct",
      ["if", [[["not-null", ["field", "pay_success_date", {...}]], ["field", "user_id", {...}]]]]
    ],
    {"name": "支付人数", "display-name": "支付人数"}
  ],
  ["sum", ["field", "amt_usd", {...}]]
]
```

---

## 七、Expressions (自定义字段)

Expressions 用于基于已有字段计算派生指标，如客单价、转化率等。

### 7.1 基本结构

```json
"expressions": {
  "字段名": [运算符, 操作数1, 操作数2, ...]
}
```

### 7.2 算术运算

```json
// 加法
["+", ["field", "a", {...}], ["field", "b", {...}]]

// 减法
["-", ["field", "a", {...}], ["field", "b", {...}]]

// 乘法
["*", ["field", "a", {...}], ["field", "b", {...}]]

// 除法 (注意除零保护)
["/",
  ["field", "sum", {"base-type": "type/Float"}],
  ["field", "count", {"base-type": "type/Integer"}]
]
```

### 7.3 实际案例

**客单价** (Card 3959/3966):
```json
"expressions": {
  "客单价": [
    "/",
    ["field", "sum", {"base-type": "type/Float"}],
    ["field", "支付成功人数", {"base-type": "type/Integer"}]
  ],
  "支付成功率": [
    "/",
    ["field", "支付成功人数", {"base-type": "type/Integer"}],
    ["field", "意向行为uv", {"base-type": "type/Integer"}]
  ]
}
```

### 7.4 引用表达式

在 `order-by` 中引用表达式：

```json
"order-by": [
  ["desc",
    ["expression", "支付成功率", {"base-type": "type/Float"}]
  ]
]
```

---

## 八、Order-by (排序)

### 8.1 基础排序

```json
// 升序
["asc", ["field", "ds_time", {"base-type": "type/DateTime"}]]

// 降序
["desc", ["field", "amt_usd", {"base-type": "type/Float"}]]
```

### 8.2 按聚合字段排序

```json
// 按第1个聚合字段降序
["desc", ["aggregation", 0]]

// 按第2个聚合字段升序
["asc", ["aggregation", 1]]
```

### 8.3 多字段排序

```json
"order-by": [
  ["asc", ["field", "ds_time", {"base-type": "type/DateTime"}]],
  ["desc", ["field", "amt_usd", {"base-type": "type/Float"}]]
]
```

### 8.4 实际案例 (Card 3959)

```json
"order-by": [
  ["desc", ["field", "意向行为pv", {"base-type": "type/Integer"}]],
  ["desc", ["expression", "支付成功率", {"base-type": "type/Float"}]]
]
```

---

## 九、Joins (表关联)

### 9.1 Join 基本结构

```json
"joins": [
  {
    "ident": "唯一标识符",           // 必填，唯一标识这个 join
    "strategy": "left-join",         // 关联策略: left-join/right-join/inner-join
    "alias": "表别名",               // 必填，引用关联表字段时使用
    "source-table": "card__597",     // 关联的表/Model
    "condition": [                   // 关联条件
      "=",
      ["field", "主表字段", {"base-type": "..."}],
      ["field", "关联表字段", {"base-type": "...", "join-alias": "表别名"}]
    ]
  }
]
```

### 9.2 实际案例 (Card 3959)

```json
"joins": [
  {
    "ident": "cMzBCBnGsCYXSYPaP_sQ8",
    "strategy": "left-join",
    "alias": "Coohom用户维度宽表（旧） - user_id",
    "source-table": "card__597",
    "condition": [
      "=",
      ["field", "user_id", {"base-type": "type/BigInteger"}],
      ["field", "酷家乐userid",
        {"base-type": "type/BigInteger", "join-alias": "Coohom用户维度宽表（旧） - user_id"}]
    ]
  }
]
```

---

## 十、Source-query (子查询)

当需要基于聚合结果再计算时，使用 `source-query` 嵌套。

### 10.1 结构

```json
{
  "source-query": {
    // 内层查询配置
    "source-table": "card__3953",
    "joins": [...],
    "filter": [...],
    "breakout": [...],
    "aggregation": [...]
  },
  "expressions": {...},    // 基于内层结果计算
  "order-by": [...]
}
```

### 10.2 实际案例 (Card 3959)

```json
{
  "source-query": {
    "joins": [...],
    "breakout": [...],
    "aggregation": [...],
    "source-table": "card__3953",
    "filter": ["=", ["field", "user_type", {...}], "新签"]
  },
  "expressions": {
    "客单价": ["/", ["field", "sum", {...}], ["field", "支付成功人数", {...}]],
    "支付成功率": ["/", ["field", "支付成功人数", {...}], ["field", "意向行为uv", {...}]]
  },
  "order-by": [
    ["desc", ["field", "意向行为pv", {...}]],
    ["desc", ["expression", "支付成功率", {...}]]
  ]
}
```

**执行顺序**:
```
内层: source-table → joins → filter → breakout → aggregation
外层: expressions (基于内层聚合结果计算) → order-by
```

---

## 十一、常见业务场景模式

### 场景 1: 每日核心指标统计
```json
{
  "source-table": "card__3953",
  "breakout": [
    ["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "day"}]
  ],
  "aggregation": [
    ["count"],
    ["distinct", ["field", "user_id", {"base-type": "type/BigInteger"}]],
    ["sum", ["field", "amt_usd", {"base-type": "type/Float"}]]
  ]
}
```

### 场景 2: 分类型 + 分国家统计
```json
{
  "source-table": "card__3953",
  "joins": [...],
  "filter": ["=", ["field", "user_type", {...}], "新签"],
  "breakout": [
    ["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "week"}],
    ["field", "country", {"base-type": "type/Text", "join-alias": "..."}]
  ],
  "aggregation": [
    ["distinct", ["field", "user_id", {...}]],
    ["sum", ["field", "amt_usd", {...}]]
  ]
}
```

### 场景 3: 转化率分析 (条件聚合 + 表达式)
```json
{
  "source-query": {
    "source-table": "card__3953",
    "breakout": [["field", "ds_time", {"temporal-unit": "day"}]],
    "aggregation": [
      ["aggregation-options", ["distinct", ["field", "user_id", {...}]], {"name": "uv"}],
      ["aggregation-options",
        ["distinct", ["if", [[["not-null", ["field", "pay_success_date", {...}]], ["field", "user_id", {...}]]]]],
        {"name": "支付人数"}
      ]
    ]
  },
  "expressions": {
    "支付成功率": ["/", ["field", "支付人数", {...}], ["field", "uv", {...}]]
  }
}
```

---

## 十二、完整 API 调用示例

```python
import requests

METABASE_URL = "https://kmb.qunhequnhe.com"
API_KEY = "mb_h5ddq58TgNTAZsV7e81myvAxMlMcqXWrx1y9TdqArl8="

def create_mbql_question(name, mbql_query, display="table", 
                         collection_id=396, visualization_settings=None):
    """
    创建 MBQL Question
    
    Args:
        name: Question 名称
        mbql_query: MBQL query 配置 (不含 database 和 type 外层)
        display: 可视化类型
        collection_id: 集合 ID
        visualization_settings: 可视化配置
    """
    url = f"{METABASE_URL}/api/card"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "type": "question",
        "dataset_query": {
            "type": "query",
            "database": 4,
            "query": mbql_query
        },
        "display": display,
        "collection_id": collection_id,
        "visualization_settings": visualization_settings or {}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


# 使用示例: 创建新签用户每日支付统计
mbql = {
    "source-table": "card__3953",
    "filter": ["=", ["field", "user_type", {"base-type": "type/Text"}], "新签"],
    "breakout": [
        ["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "day"}]
    ],
    "aggregation": [
        ["aggregation-options",
         ["distinct", ["if", [[["not-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]],
                               ["field", "user_id", {"base-type": "type/BigInteger"}]]]]],
         {"name": "支付成功人数", "display-name": "支付成功人数"}],
        ["sum", ["field", "amt_usd", {"base-type": "type/Float"}]]
    ]
}

question = create_mbql_question(
    name="新签用户每日支付统计",
    mbql_query=mbql,
    display="line",
    visualization_settings={
        "graph.dimensions": ["ds_time"],
        "graph.metrics": ["支付成功人数", "sum"],
        "graph.show_values": True
    }
)

print(f"Question ID: {question['id']}")
```

---

## 十三、Dashboard 操作

### 13.1 创建 Dashboard

```python
def create_dashboard(name, collection_id=396, description=""):
    """创建 Dashboard"""
    url = f"{METABASE_URL}/api/dashboard"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "collection_id": collection_id,
        "description": description
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# 示例
dashboard = create_dashboard(
    name="转化效率分析看板",
    collection_id=396,
    description="基于 Model 3953 的用户转化分析"
)
print(f"Dashboard ID: {dashboard['id']}")
```

### 13.2 添加 Question 到 Dashboard

**重要经验**: Dashboard 创建后为空，需要通过 PUT 请求添加卡片。

```python
def add_cards_to_dashboard(dashboard_id, cards):
    """
    添加 Question 到 Dashboard
    
    Args:
        dashboard_id: Dashboard ID
        cards: 卡片列表，每个卡片包含:
            - card_id: Question ID (注意是 card_id 不是 cardId)
            - row: 行位置 (从0开始)
            - col: 列位置 (从0开始，Dashboard 总宽度24格)
            - size_x: 宽度 (占几格)
            - size_y: 高度 (占几格)
    """
    url = f"{METABASE_URL}/api/dashboard/{dashboard_id}"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # 关键点: 使用临时负数 ID，后端会分配真实 ID
    dashcards = []
    for i, card in enumerate(cards):
        dashcards.append({
            "id": -(i + 1),  # 临时 ID: -1, -2, -3...
            "card_id": card["card_id"],  # 注意字段名是 card_id (不是 cardId)
            "row": card["row"],
            "col": card["col"],
            "size_x": card["size_x"],
            "size_y": card["size_y"],
            "parameter_mappings": []  # 参数映射，可选
        })
    
    payload = {
        "dashcards": dashcards
    }
    
    response = requests.put(url, headers=headers, json=payload)
    return response.json()

# 示例: 添加两个 Question 到 Dashboard
cards = [
    {
        "card_id": 4374,  # 转化效率分析
        "row": 0,
        "col": 0,
        "size_x": 16,  # 占16格 (左侧2/3)
        "size_y": 8
    },
    {
        "card_id": 4371,  # 对比分析
        "row": 0,
        "col": 16,  # 从第16格开始 (右侧1/3)
        "size_x": 8,
        "size_y": 8
    }
]

result = add_cards_to_dashboard(337, cards)
print(f"已添加 {len(result['dashcards'])} 个卡片")
```

### 13.3 Dashboard 网格系统

- **总宽度**: 24 格
- **坐标原点在左上角**: row=0, col=0
- **卡片可以重叠**: 需要手动规划位置

**常见布局**:
```
┌────────────────────────────────────────┐
│  卡片1 (12x6)   │   卡片2 (12x6)       │
│  col=0,row=0    │   col=12,row=0       │
├─────────────────┼──────────────────────┤
│  卡片3 (24x6)                          │
│  col=0,row=6                           │
└────────────────────────────────────────┘
```

### 13.4 完整流程示例

```python
def create_dashboard_with_questions():
    """创建 Dashboard 并添加 Questions 的完整流程"""
    
    # 1. 创建 Dashboard
    dashboard = create_dashboard(
        name="萝卜的转化分析看板",
        collection_id=396
    )
    dashboard_id = dashboard['id']
    
    # 2. 添加 Questions
    cards = [
        {"card_id": 4374, "row": 0, "col": 0, "size_x": 16, "size_y": 8},
        {"card_id": 4371, "row": 0, "col": 16, "size_x": 8, "size_y": 8}
    ]
    
    result = add_cards_to_dashboard(dashboard_id, cards)
    
    print(f"Dashboard 创建完成!")
    print(f"ID: {dashboard_id}")
    print(f"链接: https://kmb.qunhequnhe.com/dashboard/{dashboard_id}")
    print(f"包含 {len(result['dashcards'])} 个 Question")
    
    return dashboard_id

# 执行
dashboard_id = create_dashboard_with_questions()
```

### 13.5 关键经验总结

| 踩坑点 | 正确做法 |
|--------|----------|
| 字段名错误 | 使用 `card_id` (不是 `cardId`) |
| dashcards 缺少 id | 使用临时负数 ID (`-1`, `-2` 等) |
| 使用 POST 添加卡片 | 应该先用 POST 创建 Dashboard，再用 PUT 更新添加卡片 |
| 卡片重叠 | 手动计算 col + size_x 不要超过 24 |

---

## 参考文档

- [METABASE_API.md](./METABASE_API.md) - API 基础使用
- [METABASE_DASHBOARD_312_ANALYSIS.md](./METABASE_DASHBOARD_312_ANALYSIS.md) - Dashboard 案例分析
- [Metabase 官方文档](https://www.metabase.com/docs/latest/api/dashboard.html)

---

**文档状态**: 📝 基于 Dashboard 312 实际案例分析整理
