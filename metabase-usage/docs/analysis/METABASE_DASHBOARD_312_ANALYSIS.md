# Metabase Dashboard 312 - Coohom 折扣体系分析报告

> 本文档分析 Dashboard 312 (coohom-new) 的结构、数据模型、业务含义及 API 使用方法

---

## 一、Dashboard 概览

| 属性 | 值 |
|------|-----|
| **Dashboard ID** | 312 |
| **名称** | coohom折扣体系 new |
| **所属集合** | COOHOM折扣体系 (ID: 396) |
| **创建者** | shuhang@qunhemail.com |
| **最后更新** | 2026-03-12 |
| **查看次数** | 56 |

### 1.1 Dashboard Tabs

| Tab ID | 名称 | 位置 | 内容概述 |
|--------|------|------|----------|
| 325 | 总数据 | 0 | 按日聚合的核心指标趋势 |
| 326 | weekly | 1 | 按周聚合的指标趋势 |
| 324 | 分场景 | 2 | 按用户类型(新签/升级/召回)细分的详细数据 |

---

## 二、核心数据模型 (Model)

### 2.1 Model 3953 - 意向用户付费model

这是整个 Dashboard 的底层数据模型，是一个 **Metabase Model** (数据集类型)。

#### 模型基本信息
| 属性 | 值 |
|------|-----|
| **Model ID** | 3953 |
| **名称** | 意向用户付费model |
| **类型** | Model (可复用数据集) |
| **创建方式** | **SQL (Native)** |
| **数据库** | ID 4 (StarRocks) |
| **集合** | COOHOM折扣体系 (ID: 396) |

#### 数据源 SQL

```sql
select * from hive_prod.kdw_dw.dwd_coohom_trd_toc_payment_intention_i_d
```

**表名解析**:
- `dwd_` = DWD 层 (Data Warehouse Detail) - **数据仓库明细层**
- `coohom_trd_toc_payment_intention` = Coohom 交易-付费意向数据
- `_i_d` = 增量日表 (Incremental Daily)

#### 模型层设计模式

**Model 层特点**:
1. **明细层**: 保留最细粒度的原始数据（一行一个付费意向行为）
2. **宽表设计**: 包含丰富的维度字段，方便上层灵活分析
3. **预清洗**: 在数仓层已完成数据清洗和标准化

#### 核心字段说明

| 字段名 | 类型 | 业务含义 |
|--------|------|----------|
| `intention_date` | Text | 意向日期(字符串格式) |
| `ds_time` | DateTime | 数据时间戳 |
| `user_id` | BigInteger | 用户ID |
| `user_type` | Text | **用户付费模式**: 新签/升级/召回 |
| `sku` | Text | **SKU编码**: 如 elite_year_cyclical |
| `amt_usd` | Float | **支付金额(USD)** |
| `pay_success_date` | DateTime | **支付成功日期** (null表示未支付) |
| `is_payment_success` | Boolean | 是否支付成功 |

#### 关联维度表

**Join: Coohom用户维度宽表 (Card 597)**
- **关联字段**: user_id = 酷家乐userid
- **关联方式**: Left Join
- **补充字段**: 用户有效国家（中文）- 优先取活跃国家，无则取注册国家

### 2.2 数据模型设计模式

**Model 3953 设计特点**:
1. **SQL 创建**: 使用原生 SQL 直接查询数仓明细层宽表
2. **明细层**: DWD 层保留最细粒度数据，一行代表一次付费意向行为
3. **宽表设计**: 包含丰富的维度字段，支持上层灵活分析
4. **星型模型**: 作为事实表，关联维度表 (Card 597) 补充用户信息

```
数仓 DWD 层 (hive_prod.kdw_dw.dwd_coohom_trd_toc_payment_intention_i_d)
                    ↓ SQL 直连
            Metabase Model 3953 (意向用户付费model)
                    ↓ 配置式 Question
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
  明细表          趋势图         维度分析
(按时间聚合)    (折线图)       (饼图/柱状图)
```

**设计要点**:
1. **Model 层职责**: 对接数仓明细层，提供统一、清洗后的数据入口
2. **Question 层职责**: 基于 Model 做聚合分析，避免直接操作原始表
3. **左连接保留**: 即使用户维度缺失，核心付费数据仍然保留
4. **支付状态标记**: 通过 `pay_success_date` 是否为 null 判断支付状态

---

## 三、Question (查询卡片) 配置详解

### 3.1 Question 类型分类

Dashboard 312 包含 3 大类 Question:

| 类型 | 说明 | 示例 |
|------|------|------|
| **明细表** | 展示原始聚合数据 | 意向用户付费model - 按时间daily聚合表 |
| **趋势图** | 时间序列可视化 | 支付成功指标趋势、收入和客单价趋势 |
| **维度分析** | 按分类维度聚合 | 分国家、分SKU、分用户类型的饼图/柱状图 |

### 3.2 配置式 Question 构建方法

#### 类型 A: 基于 Model 的简单查询

以 **Card 3954 - 新签daily** 为例:

**配置结构**:
```json
{
  "database": 4,
  "type": "query",
  "query": {
    "source-table": "card__3953",  // 基于 Model 3953
    "filter": ["=", ["field", "user_type", ...], "新签"],  // 筛选条件
    "breakout": [["field", "ds_time", {"temporal-unit": "day"}]],  // 按天分组
    "aggregation": [
      ["count"],  // 计数
      ["distinct", ["field", "user_id", ...]],  // 去重用户数
      ["aggregation-options", 
        ["distinct", ["if", [[["not-null", ["field", "pay_success_date", ...]], 
          ["field", "user_id", ...]]]]],
        {"name": "支付成功人数", "display-name": "支付成功人数"}
      ],
      ["sum", ["field", "amt_usd", ...]]  // 金额求和
    ]
  }
}
```

**关键配置元素**:

| 元素 | 用途 | 示例 |
|------|------|------|
| `source-table` | 数据源 | `"card__3953"` 表示 Model 3953 |
| `filter` | 筛选条件 | `["=", field, "新签"]` 筛选用户类型 |
| `breakout` | 分组维度 | 时间、国家、SKU 等 |
| `aggregation` | 聚合计算 | count, distinct, sum, avg |

#### 类型 B: 基于子查询的复杂 Question

以 **Card 3959 - 新签-分国家聚合表** 为例:

**配置结构**:
```json
{
  "database": 4,
  "type": "query",
  "query": {
    "source-query": {  // 内层查询
      "source-table": "card__3953",
      "joins": [...],  // 关联用户维度表
      "filter": ["=", ["field", "user_type", ...], "新签"],
      "breakout": [["field", "国家", {"join-alias": "..."}]],
      "aggregation": [...]
    },
    "expressions": {  // 自定义计算字段
      "支付成功率": ["/", ["field", "支付成功人数", ...], ["field", "意向行为uv", ...]],
      "客单价": ["/", ["field", "sum", ...], ["field", "支付成功人数", ...]]
    },
    "order-by": [["desc", ["field", "意向行为pv", ...]], ...]
  }
}
```

**高级配置元素**:

| 元素 | 用途 | 示例 |
|------|------|------|
| `source-query` | 嵌套查询 | 基于内层查询结果再计算 |
| `expressions` | 自定义字段 | 支付成功率 = 支付成功人数 / 意向行为UV |
| `order-by` | 排序 | 按 PV 降序、按支付成功率降序 |
| `joins` | 表关联 | Left Join 用户维度表获取国家信息 |

### 3.3 可视化配置 (Visualization Settings)

#### 表格 (Table)
```json
{
  "table.cell_column": "is_payment_success",
  "table.pivot_column": "pay_success_date",
  "table.column_formatting": [
    {
      "columns": ["count", "sum"],
      "type": "range",
      "colors": ["white", "#8AE6E3"]
    },
    {
      "columns": ["支付成功率"],
      "type": "range",
      "colors": ["white", "#87BCEC"],
      "min_value": 0,
      "max_value": 0.2
    }
  ],
  "column_settings": {
    "[\"name\",\"支付成功率\"]": {"number_style": "percent"}
  }
}
```

#### 折线图 (Line Chart)
```json
{
  "graph.dimensions": ["ds_time"],  // X轴
  "graph.metrics": ["意向行为uv", "支付成功人数", "支付成功率"],  // Y轴
  "series_settings": {
    "意向行为uv": {"axis": "left"},
    "支付成功人数": {"axis": "left"},
    "支付成功率": {"axis": "right"}  // 双轴显示
  },
  "graph.show_values": true
}
```

#### 饼图 (Pie Chart)
```json
{
  "pie.dimension": ["用户有效国家（中文）..."],  // 分类维度
  "pie.metric": "count",  // 度量值
  "pie.slice_threshold": 1,
  "pie.percent_visibility": "legend",
  "pie.show_labels": true
}
```

#### 柱状图 (Bar Chart)
```json
{
  "graph.dimensions": ["ds_time", "sku"],  // X轴 + 分组
  "graph.metrics": ["支付成功人数"],
  "stackable.stack_type": "stacked"  // 堆叠显示
}
```

---

## 四、业务指标详解

### 4.1 核心指标定义

| 指标名 | 计算方式 | 业务含义 |
|--------|----------|----------|
| **意向行为PV** | Count(*) | 用户产生付费意向的总次数 |
| **意向行为UV** | Distinct(user_id) | 产生付费意向的去重用户数 |
| **支付成功人数** | Distinct(user_id where pay_success_date is not null) | 实际完成支付的去重用户数 |
| **支付成功率** | 支付成功人数 / 意向行为UV | 从意向到支付的转化率 |
| **客单价** | Sum(amt_usd) / 支付成功人数 | 平均每单支付金额 |
| **总收入** | Sum(amt_usd) | 支付总金额(USD) |

### 4.2 用户付费模式分类

| 类型 | 说明 | 业务场景 |
|------|------|----------|
| **新签** | 首次付费用户 | 新用户转化 |
| **升级** | 已有套餐升级 | 增值服务 |
| **召回** | 流失用户回流付费 | 用户回流 |

### 4.3 分析维度

| 维度 | 用途 |
|------|------|
| **时间** | 日/周趋势分析 |
| **国家** | 地域分布分析 |
| **SKU** | 产品偏好分析 |
| **用户类型** | 用户生命周期分析 |

---

## 五、Dashboard 参数配置

### 5.1 全局筛选参数

| 参数 ID | 名称 | 类型 | 默认值 | 说明 |
|---------|------|------|--------|------|
| 9e1af658 | Date | date/all-options | past1months~ | 日期范围筛选 |
| 1320d005 | sku | string/= | - | SKU筛选(从Card 3953取值) |
| 263ad5a1 | 国家 | string/= | - | 国家筛选(从Card 597取值) |
| 728e6b13 | 用户付费模式 | string/= | - | 用户类型筛选(从Card 3953取值) |

### 5.2 参数映射示例

```json
{
  "parameter_mappings": [
    {
      "parameter_id": "9e1af658",
      "card_id": 3954,
      "target": ["dimension", ["field", "ds_time", {...}], {"stage-number": 0}]
    },
    {
      "parameter_id": "728e6b13",
      "card_id": 3966,
      "target": ["dimension", ["field", "user_type", {...}], {"stage-number": 0}]
    }
  ]
}
```

---

## 六、API 使用指南

### 6.1 获取 Dashboard 信息

```bash
curl -X GET "https://kmb.qunhequnhe.com/api/dashboard/312" \
  -H "X-Api-Key: mb_h5ddq58TgNTAZsV7e81myvAxMlMcqXWrx1y9TdqArl8="
```

### 6.2 获取 Model/Question 详情

```bash
# 获取 Model 3953 详情
curl -X GET "https://kmb.qunhequnhe.com/api/card/3953" \
  -H "X-Api-Key: mb_h5ddq58TgNTAZsV7e81myvAxMlMcqXWrx1y9TdqArl8="

# 获取 Question 3954 详情  
curl -X GET "https://kmb.qunhequnhe.com/api/card/3954" \
  -H "X-Api-Key: mb_h5ddq58TgNTAZsV7e81myvAxMlMcqXWrx1y9TdqArl8="
```

### 6.3 执行查询获取数据

```bash
# 执行 Question 3954 查询
curl -X POST "https://kmb.qunhequnhe.com/api/card/3954/query" \
  -H "X-Api-Key: mb_h5ddq58TgNTAZsV7e81myvAxMlMcqXWrx1y9TdqArl8=" \
  -H "Content-Type: application/json"
```

### 6.4 Python 调用示例

```python
import requests
import json

METABASE_URL = "https://kmb.qunhequnhe.com"
API_KEY = "mb_h5ddq58TgNTAZsV7e81myvAxMlMcqXWrx1y9TdqArl8="

def get_card_data(card_id):
    """获取 Question/Model 数据"""
    url = f"{METABASE_URL}/api/card/{card_id}/query"
    headers = {"X-Api-Key": API_KEY}
    
    response = requests.post(url, headers=headers)
    return response.json()

def parse_metabase_data(result):
    """解析 Metabase 查询结果"""
    data = result['data']
    rows = data['rows']
    columns = [col['name'] for col in data['cols']]
    
    import pandas as pd
    return pd.DataFrame(rows, columns=columns)

# 使用示例
data_3954 = get_card_data(3954)
df = parse_metabase_data(data_3954)
print(df.head())
```

### 6.5 带参数的查询

```python
def query_with_params(card_id, params=None):
    """
    执行带参数的查询
    
    params 格式:
    {
        "parameters": [
            {
                "type": "date/all-options",
                "value": "past7days~",
                "target": ["dimension", ["field", "ds_time", {...}]]
            },
            {
                "type": "string/=",
                "value": ["新签"],
                "target": ["dimension", ["field", "user_type", {...}]]
            }
        ]
    }
    """
    url = f"{METABASE_URL}/api/card/{card_id}/query"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=params or {})
    return response.json()
```

---

## 七、Metabase 核心概念

### 7.1 Model vs Question vs Dashboard

| 概念 | 说明 | 关系 |
|------|------|------|
| **Model** | 可复用的数据集，带有元数据定义 | 作为 Question 的数据源 |
| **Question** | 单个查询/可视化卡片 | 组合成 Dashboard |
| **Dashboard** | 多个 Question 的可视化组合 | 包含多个 Question |
| **Collection** | 文件夹，组织 Models/Questions/Dashboards | 包含多个资源 |

### 7.2 Query Type 类型

| 类型 | 说明 | 使用场景 |
|------|------|----------|
| `query` | 可视化查询构建器 | 简单查询、快速探索 |
| `native` | 原生 SQL | 复杂查询、性能优化 |
| `internal` | 内部查询 | Metabase 系统使用 |

### 7.3 Aggregation 类型

| 聚合 | MBQL | 说明 |
|------|------|------|
| 计数 | `["count"]` | 行数统计 |
| 去重计数 | `["distinct", field]` | 去重后计数 |
| 求和 | `["sum", field]` | 数值求和 |
| 平均值 | `["avg", field]` | 数值平均 |
| 最小值 | `["min", field]` | 最小值 |
| 最大值 | `["max", field]` | 最大值 |
| 自定义 | `["aggregation-options", expr, options]` | 带自定义名称的聚合 |

### 7.4 Filter 操作符

| 操作符 | 示例 | 说明 |
|--------|------|------|
| `=` | `["=", field, value]` | 等于 |
| `!=` | `["!=", field, value]` | 不等于 |
| `<` `>` | `[">", field, value]` | 大于/小于 |
| `between` | `["between", field, min, max]` | 范围 |
| `is-null` | `["is-null", field]` | 为空 |
| `not-null` | `["not-null", field]` | 非空 |
| `and` `or` | `["and", cond1, cond2]` | 逻辑组合 |

---

## 八、扩展学习资源

### 8.1 Metabase 官方文档

- [API Documentation](https://www.metabase.com/docs/latest/api-documentation.html)
- [Query Language (MBQL)](https://www.metabase.com/docs/latest/questions/query-builder/introduction.html)
- [Data Model](https://www.metabase.com/docs/latest/data-modeling/models.html)

### 8.2 相关文档

- [METABASE_API.md](./METABASE_API.md) - API 使用基础
- [DATA_SOURCES.md](./DATA_SOURCES.md) - 数据源配置

---

## 九、更新记录

| 时间 | 更新内容 |
|------|----------|
| 2026-03-12 | 创建文档，分析 Dashboard 312 结构 |
| 2026-03-12 | 补充 Model/Question 配置方法 |
| 2026-03-12 | 添加业务指标详解和 API 示例 |

---

**文档状态**: 📝 持续更新中
