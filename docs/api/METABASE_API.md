# Metabase API 使用文档

本文档说明如何使用 Metabase API 获取数据用于日报和周报生成。

---

## 一、API 认证

### 方式1: API Key (推荐)

在 Metabase 管理后台生成 API Key，然后在请求头中使用：

```bash
curl -X GET \
  "https://your-metabase.com/api/card/123" \
  -H "X-API-KEY: your_api_key_here"
```

### 方式2: Session Token

1. 先登录获取 session token：

```bash
curl -X POST \
  "https://your-metabase.com/api/session" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_email@example.com",
    "password": "your_password"
  }'
```

2. 使用返回的 token 调用 API：

```bash
curl -X GET \
  "https://your-metabase.com/api/card/123" \
  -H "X-Metabase-Session: your_session_token"
```

---

## 二、核心 API 接口

### 1. 获取查询信息

```bash
GET /api/card/{question_id}
```

获取某个 question（查询）的基本信息。

### 2. 执行查询并获取数据

```bash
POST /api/card/{question_id}/query
```

执行指定的查询并返回结果。

**Python 示例：**

```python
import requests
import json
from datetime import datetime, timedelta

METABASE_URL = "https://your-metabase.com"
API_KEY = "your_api_key"

def run_query(question_id):
    """执行 Metabase 查询并返回数据"""
    url = f"{METABASE_URL}/api/card/{question_id}/query"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    
    return response.json()

# 示例：获取数据
data = run_query(123)  # 替换为实际的 question_id
print(data)
```

### 3. 使用 SQL 直接查询（高级）

如果需要更灵活的数据获取，可以使用原生 SQL：

```bash
POST /api/dataset
```

**Python 示例：**

```python
def run_sql_query(database_id, sql):
    """执行原生 SQL 查询"""
    url = f"{METABASE_URL}/api/dataset"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "type": "native",
        "native": {
            "query": sql
        },
        "database": database_id
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()
```

---

## 三、响应数据结构

### 查询结果格式

```json
{
  "data": {
    "rows": [
      [1234, "2024-03-10", 5678.90],
      [5678, "2024-03-11", 9012.34]
    ],
    "cols": [
      {"name": "user_id", "display_name": "User ID", "base_type": "type/Integer"},
      {"name": "date", "display_name": "Date", "base_type": "type/Date"},
      {"name": "amount", "display_name": "Amount", "base_type": "type/Float"}
    ]
  }
}
```

**Python 解析示例：**

```python
import pandas as pd

def parse_metabase_result(result):
    """解析 Metabase 查询结果为 DataFrame"""
    data = result['data']
    rows = data['rows']
    columns = [col['name'] for col in data['cols']]
    
    df = pd.DataFrame(rows, columns=columns)
    return df
```

---

## 四、周报数据获取函数

### 1. Acquisition / 流量获取

```python
def get_acquisition_data(question_id):
    """
    获取流量获取数据
    
    返回格式：
    {
        'total_visitors': 136911,
        'total_registrations': 25689,
        'overall_conversion': 18.76,
        'channels': [
            {
                'channel': 'paid ads',
                'visitors': 39956,
                'visitors_change': 8.2,
                'registrations': 18185,
                'registrations_change': 15.2,
                'conversion': 45.51,
                'conversion_change': 2.7
            },
            ...
        ]
    }
    """
    result = run_query(question_id)
    df = parse_metabase_result(result)
    
    # 处理数据...
    return data
```

### 2. Activation / 激活转化

```python
def get_activation_data(question_id):
    """
    获取激活转化数据
    
    对比周期：前两周 vs 上上两周
    
    返回格式：
    {
        'current_period': '2026/02/23',
        'compare_period': '2026/02/16',
        'funnel': [
            {'step': '新注册', 'current': 25399, 'compare': 22547, 'change': 12.63},
            {'step': '注册→进工具', 'current_rate': 81.31, 'compare_rate': 80.32, 'change_pp': 0.99},
            ...
        ],
        'history': [...]  # 近4周数据
    }
    """
    result = run_query(question_id)
    df = parse_metabase_result(result)
    
    # 处理数据...
    return data
```

### 3. Retention / 用户留存

```python
def get_retention_data(question_id):
    """
    获取用户留存数据
    
    返回格式：
    {
        'wau': 52436,
        'new_user_wau': 23468,
        'new_user_wau_change': 5.85,
        'old_user_wau': 28968,
        'old_user_wau_change': -0.98,
        'retention': {
            'new_user': {'current': 11.18, 'compare': 10.61, 'change_pp': 0.57},
            'old_user': {'current': 45.37, 'compare': 46.70, 'change_pp': -1.33}
        },
        'history': [...]  # 近4周数据
    }
    """
    result = run_query(question_id)
    df = parse_metabase_result(result)
    
    # 处理数据...
    return data
```

### 4. Revenue / 收入分析

```python
def get_revenue_data(question_id):
    """
    获取收入分析数据
    
    返回格式：
    {
        'total': 79157,
        'total_change': 26079,
        'total_change_pct': 49,
        'agency': {'amount': 2600, 'change': 2600, 'change_pct': '0->2600'},
        'normal': {'amount': 76557, 'change': 23479, 'change_pct': 44},
        'breakdown': {
            'billing': [
                {'type': '连续续约', 'amount': 14427},
                {'type': '新签', 'amount': 4329, 'positive': True},
                {'type': '升级', 'amount': 3382, 'positive': True}
            ],
            'countries': [
                {'country': '新加坡', 'amount': 2128, 'positive': True},
                {'country': '日本', 'amount': 1954, 'positive': True},
                {'country': '马来西亚', 'amount': 1719, 'positive': True}
            ],
            'skus': [
                {'sku': 'elite_year_cyclical', 'amount': 7789, 'positive': True},
                {'sku': 'pro_month_cyclical', 'amount': 6433, 'positive': True},
                {'sku': 'pro_year_cyclical', 'amount': 5287, 'positive': True}
            ]
        }
    }
    """
    result = run_query(question_id)
    df = parse_metabase_result(result)
    
    # 处理数据...
    return data
```

---

## 五、日报数据获取函数

```python
def get_daily_metrics(question_ids):
    """
    获取日报核心指标
    
    question_ids: {
        'spend': 101,
        'registrations': 102,
        'revenue': 103,
        'retention': 104
    }
    
    返回格式：
    {
        'date': '2026-03-05',
        'spend': {'current': 3818.01, 'change_pct': -50.7, 'yesterday': 7750.81},
        'registrations': {'current': 7950, 'change_pct': -48.2, 'yesterday': 15344},
        'revenue': {'current': 1106.39, 'change_pct': -58.7, 'yesterday': 2680.45},
        'retention': {'current': 0, 'change_pct': -100, 'yesterday': 1074}
    }
    """
    data = {}
    
    for metric, qid in question_ids.items():
        result = run_query(qid)
        df = parse_metabase_result(result)
        
        # 处理数据...
        data[metric] = {...}
    
    return data
```

---

## 六、数据缓存策略

为避免频繁调用 API，可以实现本地缓存：

```python
import json
import os
from datetime import datetime

def cache_data(key, data, cache_dir="/workspace/data"):
    """缓存数据到本地文件"""
    os.makedirs(cache_dir, exist_ok=True)
    
    filename = f"{cache_dir}/{key}_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f)
    
    return filename

def load_cached_data(key, date, cache_dir="/workspace/data"):
    """从本地缓存加载数据"""
    filename = f"{cache_dir}/{key}_{date}.json"
    
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    
    return None
```

---

## 七、错误处理

```python
import time

def safe_run_query(question_id, retries=3):
    """带重试机制的查询执行"""
    for i in range(retries):
        try:
            return run_query(question_id)
        except requests.exceptions.RequestException as e:
            if i == retries - 1:
                raise
            time.sleep(2 ** i)  # 指数退避
    
    return None
```

---

## 八、完整示例：生成周报

```python
#!/usr/bin/env python3
"""
生成 AARRR 周报
"""

import json
from datetime import datetime, timedelta

# Metabase 配置
METABASE_URL = "https://your-metabase.com"
API_KEY = "your_api_key"

# Query IDs (从 DATA_SOURCES.md 获取)
QUERY_IDS = {
    'acquisition': 201,
    'activation': 202,
    'retention': 203,
    'revenue': 204,
    'referral': 205
}

def generate_weekly_report():
    """生成周报数据"""
    
    # 1. 获取 Acquisition 数据
    acquisition = get_acquisition_data(QUERY_IDS['acquisition'])
    
    # 2. 获取 Activation 数据
    activation = get_activation_data(QUERY_IDS['activation'])
    
    # 3. 获取 Retention 数据
    retention = get_retention_data(QUERY_IDS['retention'])
    
    # 4. 获取 Revenue 数据
    revenue = get_revenue_data(QUERY_IDS['revenue'])
    
    # 5. 组合数据
    report = {
        'generated_at': datetime.now().isoformat(),
        'data_period': '2026/03/02 - 2026/03/09',
        'compare_period': '2026/02/23 - 2026/03/02',
        'acquisition': acquisition,
        'activation': activation,
        'retention': retention,
        'revenue': revenue
    }
    
    # 6. 保存数据
    cache_data('weekly_aarrr', report)
    
    return report

if __name__ == '__main__':
    report = generate_weekly_report()
    print(json.dumps(report, indent=2))
```

---

## 九、参考资料

- [Metabase API 官方文档](https://www.metabase.com/docs/latest/api-documentation.html)
- [Metabase 查询 API](https://www.metabase.com/docs/latest/api/card.html)
- [DATA_SOURCES.md](./DATA_SOURCES.md) - 数据源定义文档
- [METABASE_DASHBOARD_312_ANALYSIS.md](./METABASE_DASHBOARD_312_ANALYSIS.md) - Dashboard 结构分析示例

---

## 十、Model 与 Question 配置详解

### 10.1 Metabase 核心概念

| 概念 | 说明 | 关系 |
|------|------|------|
| **Model** | 可复用的数据集，带有元数据定义 | 作为 Question 的数据源 |
| **Question** | 单个查询/可视化卡片 | 组合成 Dashboard |
| **Dashboard** | 多个 Question 的可视化组合 | 包含多个 Question |
| **Collection** | 文件夹，组织 Models/Questions/Dashboards | 包含多个资源 |

### 10.2 创建 Model 的方法

Model 是一个带有元数据的查询结果，可以被其他 Question 引用。Model 层通常作为**明细层**，对接数仓的 DWD (Data Warehouse Detail) 层，提供统一的、清洗后的数据入口。

**Model 层设计原则**:
1. **明细层**: 保留最细粒度数据，一行代表一个业务实体/事件
2. **宽表设计**: 包含丰富的维度字段，支持上层灵活分析
3. **预清洗**: 完成数据标准化、字段命名规范化
4. **统一入口**: 避免多个 Question 直接引用原始表

#### 方式1: 从 SQL 创建 Model (推荐用于明细层)

适用于对接数仓明细层宽表：

```python
def create_model_from_sql(name, sql, database_id=4, collection_id=396):
    """从 SQL 创建 Model - 适用于明细层宽表"""
    url = f"{METABASE_URL}/api/card"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "dataset_query": {
            "type": "native",
            "native": {"query": sql},
            "database": database_id
        },
        "display": "table",
        "type": "model",  # 关键: 指定为 model 类型
        "collection_id": collection_id
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# 示例: 创建意向用户付费模型 (对接数仓 DWD 层)
sql = """
SELECT 
    user_id,
    ds_time,
    user_type,
    sku,
    amt_usd,
    pay_success_date,
    CASE WHEN pay_success_date IS NOT NULL THEN 1 ELSE 0 END as is_payment_success
FROM hive_prod.kdw_dw.dwd_coohom_trd_toc_payment_intention_i_d
WHERE ds_time >= '2025-01-01'
"""

model = create_model_from_sql("意向用户付费model", sql)
print(f"Model ID: {model['id']}")
```

**数仓分层参考**:
| 层级 | 前缀 | 说明 |
|------|------|------|
| ODS | `ods_` | 原始数据层，直接同步业务库 |
| DWD | `dwd_` | **明细层**，清洗、标准化后的明细数据 |
| DWS | `dws_` | 汇总层，轻度聚合的宽表 |
| ADS | `ads_` | 应用层，面向具体应用场景的汇总表 |

#### 方式2: 从 Query Builder 创建 Model

```python
def create_model_from_query(name, source_table, database_id=4, collection_id=396):
    """从 Query Builder 配置创建 Model"""
    url = f"{METABASE_URL}/api/card"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "dataset_query": {
            "type": "query",
            "query": {
                "source-table": source_table,
                "fields": [
                    ["field", "user_id", {"base-type": "type/BigInteger"}],
                    ["field", "ds_time", {"base-type": "type/DateTime"}],
                    ["field", "user_type", {"base-type": "type/Text"}],
                    ["field", "amt_usd", {"base-type": "type/Float"}]
                ]
            },
            "database": database_id
        },
        "display": "table",
        "type": "model",
        "collection_id": collection_id
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

### 10.3 创建 Question 的两种方式

| 方式 | 类型 | 适用场景 | 数据源 |
|------|------|----------|--------|
| **配置式 (MBQL)** | `type: "query"` | 标准分析、基于 Model 的聚合 | Model 或 表 |
| **SQL 式 (Native)** | `type: "native"` | 复杂逻辑、性能优化、特殊语法 | 任意 SQL |

#### 方式 A: 配置式 Question (MBQL) - 推荐用于基于 Model 的分析

基于已有的 Model 或表，使用可视化查询构建器配置。

**适用场景**:
- 基于 Model 做聚合统计
- 需要灵活筛选、分组、排序
- 业务人员可能需要调整
- 复用 Model 的元数据定义

**API 结构**:
```json
{
  "name": "Question 名称",
  "type": "question",
  "dataset_query": {
    "type": "query",           // 固定值: query
    "database": 4,
    "query": {
      "source-table": "card__3953",  // 基于 Model 3953
      "filter": [...],         // 筛选条件
      "breakout": [...],       // 分组维度
      "aggregation": [...],    // 聚合计算
      "order-by": [...],       // 排序
      "limit": 100             // 限制条数
    }
  },
  "display": "line",           // 可视化类型
  "visualization_settings": {} // 可视化配置
}
```

**Python 示例 - 基于 Model 的配置式 Question**:

```python
def create_mbql_question(name, source_model_id, filters=None, 
                         breakouts=None, aggregations=None,
                         display="table", visualization_settings=None):
    """
    创建配置式 Question (MBQL)
    
    Args:
        name: Question 名称
        source_model_id: 数据源 Model ID (如 3953)
        filters: 筛选条件列表
        breakouts: 分组维度列表
        aggregations: 聚合计算列表
        display: 可视化类型 (table/line/bar/pie/scalar)
        visualization_settings: 可视化配置
    """
    url = f"{METABASE_URL}/api/card"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    query = {
        "source-table": f"card__{source_model_id}"
    }
    
    if filters:
        query["filter"] = filters if len(filters) == 1 else ["and"] + filters
    if breakouts:
        query["breakout"] = breakouts
    if aggregations:
        query["aggregation"] = aggregations
    
    payload = {
        "name": name,
        "type": "question",
        "dataset_query": {
            "type": "query",
            "database": 4,
            "query": query
        },
        "display": display,
        "collection_id": 396,
        "visualization_settings": visualization_settings or {}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


# ========== 实际使用示例 ==========

# 示例 1: 新签用户每日统计 (基于 Model 3953)
# 对应 Dashboard 312 中的 Card 3954
question1 = create_mbql_question(
    name="新签用户每日统计",
    source_model_id=3953,
    filters=[
        ["=", ["field", "user_type", {"base-type": "type/Text"}], "新签"]
    ],
    breakouts=[
        ["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "day"}]
    ],
    aggregations=[
        ["count"],
        ["distinct", ["field", "user_id", {"base-type": "type/BigInteger"}]],
        ["sum", ["field", "amt_usd", {"base-type": "type/Float"}]]
    ],
    display="line",
    visualization_settings={
        "graph.dimensions": ["ds_time"],
        "graph.metrics": ["count", "sum"],
        "graph.show_values": True
    }
)

# 示例 2: 分 SKU 客单价分析 (带自定义表达式)
# 对应 Dashboard 312 中的 Card 3957
query_advanced = {
    "source-query": {
        "source-table": "card__3953",
        "aggregation": [
            ["aggregation-options", 
             ["distinct", ["if", [[["not-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]], 
                                   ["field", "user_id", {"base-type": "type/BigInteger"}]]]]],
             {"name": "支付成功人数", "display-name": "支付成功人数"}],
            ["sum", ["field", "amt_usd", {"base-type": "type/Float"}]]
        ],
        "breakout": [
            ["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "day"}],
            ["field", "sku", {"base-type": "type/Text"}]
        ]
    },
    "expressions": {
        "客单价": [
            "/",
            ["field", "sum", {"base-type": "type/Float"}],
            ["field", "支付成功人数", {"base-type": "type/Integer"}]
        ]
    },
    "filter": ["=", ["field", "user_type", {"base-type": "type/Text"}], "新签"]
}

question2 = create_mbql_question(
    name="新签用户分SKU客单价分析",
    source_model_id=3953,
    display="bar",
    visualization_settings={
        "stackable.stack_type": "stacked",
        "graph.dimensions": ["ds_time", "sku"],
        "graph.metrics": ["支付成功人数"]
    }
)
# 注意: question2 需要直接传入完整的 dataset_query
```

#### 方式 B: SQL 式 Question (Native SQL)

直接编写原生 SQL，灵活性最高。

**适用场景**:
- 复杂的多表关联逻辑
- 需要使用数据库特有函数
- 性能敏感，需要优化 SQL
- 配置式难以实现的计算

**API 结构**:
```json
{
  "name": "Question 名称",
  "type": "question",
  "dataset_query": {
    "type": "native",          // 固定值: native
    "database": 4,
    "native": {
      "query": "SELECT ...",   // 原生 SQL
      "template-tags": {}      // 参数占位符 (可选)
    }
  },
  "display": "table",
  "visualization_settings": {}
}
```

**Python 示例 - SQL 式 Question**:

```python
def create_sql_question(name, sql, database_id=4, display="table", 
                        template_tags=None, visualization_settings=None):
    """
    创建 SQL 式 Question (Native SQL)
    
    Args:
        name: Question 名称
        sql: 原生 SQL 语句
        database_id: 数据库 ID
        template_tags: 参数模板 (用于带参数的 SQL)
        display: 可视化类型
        visualization_settings: 可视化配置
    """
    url = f"{METABASE_URL}/api/card"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "type": "question",
        "dataset_query": {
            "type": "native",
            "database": database_id,
            "native": {
                "query": sql,
                "template-tags": template_tags or {}
            }
        },
        "display": display,
        "collection_id": 396,
        "visualization_settings": visualization_settings or {}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


# ========== 实际使用示例 ==========

# 示例 1: 复杂的多表关联分析
sql_complex = """
SELECT 
    DATE(a.ds_time) as dt,
    b.country,
    COUNT(DISTINCT a.user_id) as uv,
    SUM(CASE WHEN a.pay_success_date IS NOT NULL THEN 1 ELSE 0 END) as paid_users,
    SUM(a.amt_usd) as revenue,
    SUM(a.amt_usd) / NULLIF(COUNT(DISTINCT CASE WHEN a.pay_success_date IS NOT NULL THEN a.user_id END), 0) as arpu
FROM hive_prod.kdw_dw.dwd_coohom_trd_toc_payment_intention_i_d a
LEFT JOIN (
    SELECT 酷家乐userid, 
           COALESCE(活跃国家, 注册国家) as country
    FROM user_dim
) b ON a.user_id = b.酷家乐userid
WHERE a.ds_time >= '{{start_date}}'
  AND a.user_type = '{{user_type}}'
GROUP BY DATE(a.ds_time), b.country
ORDER BY dt DESC, revenue DESC
"""

# 带参数的 SQL Question
template_tags = {
    "start_date": {
        "type": "date",
        "name": "start_date",
        "display-name": "开始日期",
        "default": "2025-01-01"
    },
    "user_type": {
        "type": "text",
        "name": "user_type", 
        "display-name": "用户类型",
        "default": "新签"
    }
}

question_sql = create_sql_question(
    name="复杂多表关联分析",
    sql=sql_complex,
    template_tags=template_tags,
    display="table"
)

# 示例 2: 使用窗口函数的趋势分析
sql_window = """
SELECT 
    ds_time,
    user_type,
    daily_uv,
    SUM(daily_uv) OVER (PARTITION BY user_type ORDER BY ds_time ROWS 6 PRECEDING) as rolling_7d_uv,
    AVG(daily_revenue) OVER (PARTITION BY user_type ORDER BY ds_time ROWS 6 PRECEDING) as avg_7d_revenue
FROM (
    SELECT 
        DATE(ds_time) as ds_time,
        user_type,
        COUNT(DISTINCT user_id) as daily_uv,
        SUM(amt_usd) as daily_revenue
    FROM hive_prod.kdw_dw.dwd_coohom_trd_toc_payment_intention_i_d
    WHERE ds_time >= DATE_SUB(CURRENT_DATE, 90)
    GROUP BY DATE(ds_time), user_type
) t
ORDER BY ds_time DESC, user_type
"""

question_trend = create_sql_question(
    name="7日滚动趋势分析",
    sql=sql_window,
    display="line",
    visualization_settings={
        "graph.dimensions": ["ds_time"],
        "graph.metrics": ["daily_uv", "rolling_7d_uv"],
        "series_settings": {
            "daily_uv": {"axis": "left"},
            "rolling_7d_uv": {"axis": "left", "line.interpolate": "linear"}
        }
    }
)
```

### 10.4 MBQL 配置场景示例参考

**注意**: 以下只是常见场景的示例，实际配置需根据业务需求、数据源结构灵活调整。

#### 场景 1: 简单计数 + 时间趋势
```python
# 每日注册用户数统计
{
    "source-table": "card__3953",
    "breakout": [
        ["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "day"}]
    ],
    "aggregation": [
        ["distinct", ["field", "user_id", {"base-type": "type/BigInteger"}]]
    ]
}
```

#### 场景 2: 多维度分组 + 多指标
```python
# 按用户类型和国家统计支付人数、收入
{
    "source-table": "card__3953",
    "filter": ["not-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]],
    "breakout": [
        ["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "week"}],
        ["field", "user_type", {"base-type": "type/Text"}],
        ["field", "country", {"base-type": "type/Text", "join-alias": "用户维度表"}]
    ],
    "aggregation": [
        ["distinct", ["field", "user_id", {"base-type": "type/BigInteger"}]],  # 支付人数
        ["sum", ["field", "amt_usd", {"base-type": "type/Float"}]]           # 总收入
    ]
}
```

#### 场景 3: 条件聚合（如支付成功人数）
```python
# 统计有支付行为的去重用户数
{
    "source-table": "card__3953",
    "breakout": [
        ["field", "ds_time", {"base-type": "type/DateTime", "temporal-unit": "day"}]
    ],
    "aggregation": [
        ["aggregation-options",
         ["distinct", 
          ["if", [[["not-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]],
                   ["field", "user_id", {"base-type": "type/BigInteger"}]]]]],
         {"name": "支付成功人数", "display-name": "支付成功人数"}]
    ]
}
```

#### 场景 4: 自定义表达式计算
```python
# 计算客单价、支付成功率等派生指标
{
    "source-query": {
        "source-table": "card__3953",
        "breakout": [["field", "sku", {"base-type": "type/Text"}]],
        "aggregation": [
            ["aggregation-options", ["count"], {"name": "意向行为pv", "display-name": "意向行为pv"}],
            ["distinct", ["field", "user_id", {"base-type": "type/BigInteger"}]],  # uv
            ["sum", ["field", "amt_usd", {"base-type": "type/Float"}]]
        ]
    },
    "expressions": {
        "客单价": ["/", 
                   ["field", "sum", {"base-type": "type/Float"}], 
                   ["field", "count", {"base-type": "type/Integer"}]]
    }
}
```

#### 场景 5: 多条件组合筛选
```python
# 新签用户 + 特定SKU + 最近7天
{
    "source-table": "card__3953",
    "filter": ["and",
        ["=", ["field", "user_type", {"base-type": "type/Text"}], "新签"],
        ["=", ["field", "sku", {"base-type": "type/Text"}], "elite_year_cyclical"],
        ["time-interval", ["field", "ds_time", {"base-type": "type/DateTime"}], -7, "day"]
    ],
    "aggregation": [["sum", ["field", "amt_usd", {"base-type": "type/Float"}]]]
}
```

#### 场景 6: 排序 + 限制条数
```python
# TOP 10 SKU 按收入排序
{
    "source-table": "card__3953",
    "breakout": [["field", "sku", {"base-type": "type/Text"}]],
    "aggregation": [["sum", ["field", "amt_usd", {"base-type": "type/Float"}]]],
    "order-by": [["desc", ["aggregation", 0]]],  # 按第1个聚合字段降序
    "limit": 10
}
```

### 10.5 两种方式对比速查

| 特性 | 配置式 (MBQL) | SQL 式 (Native) |
|------|---------------|-----------------|
| **type 值** | `"query"` | `"native"` |
| **dataset_query 结构** | `{"type": "query", "query": {...}}` | `{"type": "native", "native": {"query": "..."}}` |
| **数据源** | Model ID (`card__3953`) 或表名 | 任意 SQL 语句 |
| **灵活性** | 中等，受限于 MBQL 语法 | 极高，可用任意 SQL 功能 |
| **维护成本** | 低，可视化界面可修改 | 高，需懂 SQL |
| **性能控制** | 依赖 Metabase 优化 | 可自行优化 SQL |
| **字段变更适配** | 自动适配 Model 变更 | 需手动修改 SQL |
| **适用人员** | 分析师/业务人员 | 数据工程师/资深分析师 |
}

question2 = create_question(
    name="SKU 客单价分析",
    query_config=query_config_advanced,
    display="bar"
)
```

### 10.4 常用 Filter 配置

| 场景 | MBQL 配置 |
|------|-----------|
| 等于 | `["=", ["field", "user_type", {...}], "新签"]` |
| 不等于 | `["!=", ["field", "status", {...}], "deleted"]` |
| 大于/小于 | `[">", ["field", "amt_usd", {...}], 100]` |
| 范围 | `["between", ["field", "ds_time", {...}], "2026-01-01", "2026-03-01"]` |
| 多值匹配 | `["=", ["field", "country", {...}], ["美国", "日本", "新加坡"]]` |
| 为空 | `["is-null", ["field", "pay_success_date", {...}]]` |
| 非空 | `["not-null", ["field", "pay_success_date", {...}]]` |
| 包含 | `["contains", ["field", "sku", {...}], "elite"]` |
| AND | `["and", condition1, condition2]` |
| OR | `["or", condition1, condition2]` |

### 10.5 常用 Aggregation 配置

| 聚合类型 | MBQL 配置 |
|----------|-----------|
| 计数 | `["count"]` |
| 去重计数 | `["distinct", ["field", "user_id", {...}]]` |
| 求和 | `["sum", ["field", "amt_usd", {...}]]` |
| 平均值 | `["avg", ["field", "amt_usd", {...}]]` |
| 最小值 | `["min", ["field", "ds_time", {...}]]` |
| 最大值 | `["max", ["field", "ds_time", {...}]]` |
| 标准差 | `["stddev", ["field", "amt_usd", {...}]]` |
| 自定义名称 | `["aggregation-options", ["count"], {"name": "订单数"}]` |

### 10.6 Breakout (分组) 配置

| 维度类型 | MBQL 配置 |
|----------|-----------|
| 时间-按天 | `["field", "ds_time", {"temporal-unit": "day"}]` |
| 时间-按周 | `["field", "ds_time", {"temporal-unit": "week"}]` |
| 时间-按月 | `["field", "ds_time", {"temporal-unit": "month"}]` |
| 分类字段 | `["field", "user_type", {"base-type": "type/Text"}]` |
| 关联表字段 | `["field", "country", {"join-alias": "用户维度表"}]` |

### 10.7 Join 配置

```python
"joins": [
    {
        "ident": "unique_join_identifier",
        "strategy": "left-join",
        "alias": "用户维度表",
        "condition": [
            "=",
            ["field", "user_id", {"base-type": "type/BigInteger"}],
            ["field", "酷家乐userid", {"base-type": "type/BigInteger", "join-alias": "用户维度表"}]
        ]
    }
]
```

### 10.8 可视化配置 (Visualization Settings)

#### 表格
```json
{
  "table.cell_column": "is_payment_success",
  "table.column_formatting": [
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

#### 折线图
```json
{
  "graph.dimensions": ["ds_time"],
  "graph.metrics": ["uv", "支付人数", "支付成功率"],
  "series_settings": {
    "uv": {"axis": "left"},
    "支付成功率": {"axis": "right"}
  },
  "graph.show_values": true
}
```

#### 饼图
```json
{
  "pie.dimension": ["country"],
  "pie.metric": "count",
  "pie.slice_threshold": 1,
  "pie.percent_visibility": "legend"
}
```

---

## 十一、完整工作流示例

### 创建 Dashboard 完整流程

```python
def create_dashboard_workflow():
    """完整的 Dashboard 创建工作流"""
    
    # 1. 创建底层 Model
    model_sql = """
    SELECT 
        user_id,
        DATE(ds_time) as ds_time,
        user_type,
        sku,
        amt_usd,
        pay_success_date
    FROM user_payment_fact
    WHERE ds_time >= '2025-01-01'
    """
    model = create_model_from_sql("付费数据模型", model_sql)
    model_id = model['id']
    
    # 2. 创建 Questions
    overview_query = {
        "database": 4,
        "type": "query",
        "query": {
            "source-table": f"card__{model_id}",
            "breakout": [["field", "ds_time", {"temporal-unit": "day"}]],
            "aggregation": [
                ["distinct", ["field", "user_id", {"base-type": "type/BigInteger"}]],
                ["sum", ["field", "amt_usd", {"base-type": "type/Float"}]]
            ]
        }
    }
    q_overview = create_question(
        "每日总览",
        overview_query,
        display="line"
    )
    
    # 3. 创建 Dashboard
    dashboard_payload = {
        "name": "收入分析 Dashboard",
        "collection_id": 396,
        "dashcards": [
            {
                "cardId": q_overview['id'],
                "row": 0,
                "col": 0,
                "sizeX": 12,
                "sizeY": 6
            }
        ]
    }
    
    response = requests.post(
        f"{METABASE_URL}/api/dashboard",
        headers={"X-API-KEY": API_KEY, "Content-Type": "application/json"},
        json=dashboard_payload
    )
    
    return response.json()
```

---

## 十二、Dashboard 操作 API

### 12.1 创建 Dashboard

```python
def create_dashboard(name, collection_id, description=""):
    """创建 Dashboard"""
    url = f"{METABASE_URL}/api/dashboard"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "name": name,
        "collection_id": collection_id,
        "description": description
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

### 12.2 添加 Question 到 Dashboard (关键经验)

**注意**: 创建 Dashboard 后需要通过 PUT 请求添加卡片，且字段名为 `card_id`（不是 `cardId`）。

```python
def add_cards_to_dashboard(dashboard_id, cards):
    """添加 Question 到 Dashboard"""
    url = f"{METABASE_URL}/api/dashboard/{dashboard_id}"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    dashcards = []
    for i, card in enumerate(cards):
        dashcards.append({
            "id": -(i + 1),           # 临时负数 ID
            "card_id": card["card_id"],  # 注意: card_id 不是 cardId
            "row": card["row"],       # 行位置 (0开始)
            "col": card["col"],       # 列位置 (0-23，总宽24格)
            "size_x": card["size_x"], # 宽度
            "size_y": card["size_y"], # 高度
            "parameter_mappings": []
        })
    
    response = requests.put(url, headers=headers, json={"dashcards": dashcards})
    return response.json()

# 示例: 添加两个卡片
cards = [
    {"card_id": 4374, "row": 0, "col": 0, "size_x": 16, "size_y": 8},
    {"card_id": 4371, "row": 0, "col": 16, "size_x": 8, "size_y": 8}
]
add_cards_to_dashboard(337, cards)
```

### 12.3 Dashboard 网格系统

- **总宽度**: 24 格
- **原点**: 左上角 (row=0, col=0)
- **常见布局**: 12+12 并排，或 16+8 主次分布

---

## 待填写信息

请补充以下信息到 DATA_SOURCES.md：

1. Metabase URL
2. API Key 或登录凭证
3. 各指标对应的 Question ID
4. 数据库 ID（如使用原生 SQL）