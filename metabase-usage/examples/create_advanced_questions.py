#!/usr/bin/env python3
"""
重新创建专业的转化分析 Question - 分开人数和收入
基于 Model 3953
"""

import requests
import json

METABASE_URL = "https://kmb.qunhequnhe.com"
API_KEY = "mb_h5ddq58TgNTAZsV7e81myvAxMlMcqXWrx1y9TdqArl8="

def create_conversion_rate_question():
    """创建转化率分析 Question - 使用表达式计算同单位指标"""
    
    # MBQL: 分用户类型，计算转化率（百分比，同单位可比）
    mbql_query = {
        "source-query": {
            "source-table": "card__3953",
            "breakout": [
                ["field", "user_type", {"base-type": "type/Text"}]
            ],
            "aggregation": [
                # 意向UV
                ["aggregation-options",
                 ["distinct", ["field", "user_id", {"base-type": "type/BigInteger"}]],
                 {"name": "意向UV", "display-name": "意向UV"}],
                
                # 支付成功人数
                ["aggregation-options",
                 ["distinct",
                  ["if",
                   [[["not-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]],
                     ["field", "user_id", {"base-type": "type/BigInteger"}]]]]],
                 {"name": "支付人数", "display-name": "支付人数"}],
                
                # 总收入
                ["aggregation-options",
                 ["sum", ["field", "amt_usd", {"base-type": "type/Float"}]],
                 {"name": "总收入", "display-name": "总收入"}]
            ]
        },
        # 计算派生指标
        "expressions": {
            "支付转化率": [
                "/",
                ["field", "支付人数", {"base-type": "type/BigInteger"}],
                ["field", "意向UV", {"base-type": "type/BigInteger"}]
            ],
            "客单价": [
                "/",
                ["field", "总收入", {"base-type": "type/Float"}],
                ["field", "支付人数", {"base-type": "type/BigInteger"}]
            ]
        },
        "order-by": [
            ["desc", ["expression", "支付转化率", {"base-type": "type/Float"}]]
        ]
    }
    
    # 可视化配置 - 只显示转化率和客单价（同单位或比例指标）
    viz_settings = {
        "graph.dimensions": ["user_type"],
        "graph.metrics": ["支付转化率"],  # 只显示转化率，百分比指标可比
        "graph.show_values": True,
        "series_settings": {
            "支付转化率": {
                "axis": "left",
                "color": "#509EE3"
            }
        },
        "column_settings": {
            "[\"name\",\"支付转化率\"]": {
                "number_style": "percent",
                "decimals": 2
            }
        }
    }
    
    url = f"{METABASE_URL}/api/card"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": "用户类型转化效率分析 - 萝卜测试",
        "type": "question",
        "dataset_query": {
            "type": "query",
            "database": 4,
            "query": mbql_query
        },
        "display": "bar",
        "collection_id": 396,
        "visualization_settings": viz_settings
    }
    
    print("=" * 60)
    print("创建专业的转化分析 Question")
    print("=" * 60)
    print("\n改进点:")
    print("  ✓ 使用表达式计算派生指标")
    print("  ✓ 只显示转化率(百分比)，同单位可比")
    print("  ✓ 人数和收入分开，避免混用单位")
    
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    if 'id' in result:
        print(f"\n✅ 创建成功!")
        print(f"   ID: {result['id']}")
        print(f"   名称: {result['name']}")
        print(f"   访问: https://kmb.qunhequnhe.com/question/{result['id']}")
        return result['id']
    else:
        print(f"\n❌ 失败: {result}")
        return None

def create_two_chart_dashboard():
    """创建两个独立的 Question: 人数趋势 + 收入分析"""
    
    # Question 1: 纯人数漏斗分析
    mbql_users = {
        "source-table": "card__3953",
        "breakout": [
            ["field", "user_type", {"base-type": "type/Text"}]
        ],
        "aggregation": [
            ["aggregation-options",
             ["distinct", ["field", "user_id", {"base-type": "type/BigInteger"}]],
             {"name": "意向UV", "display-name": "意向UV"}],
            ["aggregation-options",
             ["distinct",
              ["if",
               [[["not-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]],
                 ["field", "user_id", {"base-type": "type/BigInteger"}]]]]],
             {"name": "支付人数", "display-name": "支付人数"}]
        ],
        "order-by": [["desc", ["aggregation", 1]]]
    }
    
    viz_users = {
        "graph.dimensions": ["user_type"],
        "graph.metrics": ["意向UV", "支付人数"],
        "stackable.stack_type": null,
        "graph.show_values": True
    }
    
    # Question 2: 收入分析
    mbql_revenue = {
        "source-table": "card__3953",
        "breakout": [
            ["field", "user_type", {"base-type": "type/Text"}]
        ],
        "aggregation": [
            ["aggregation-options",
             ["sum", ["field", "amt_usd", {"base-type": "type/Float"}]],
             {"name": "总收入", "display-name": "总收入(USD)"}],
            ["aggregation-options",
             ["distinct",
              ["if",
               [[["not-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]],
                 ["field", "user_id", {"base-type": "type/BigInteger"}]]]]],
             {"name": "支付人数", "display-name": "支付人数"}]
        ],
        "order-by": [["desc", ["aggregation", 0]]]
    }
    
    viz_revenue = {
        "graph.dimensions": ["user_type"],
        "graph.metrics": ["总收入"],
        "graph.show_values": True,
        "series_settings": {
            "总收入": {"color": "#F9D423"}
        }
    }
    
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # 创建 Question 1
    r1 = requests.post(f"{METABASE_URL}/api/card", headers=headers, json={
        "name": "【人数漏斗】用户类型转化 - 萝卜测试",
        "type": "question",
        "dataset_query": {"type": "query", "database": 4, "query": mbql_users},
        "display": "bar",
        "collection_id": 396,
        "visualization_settings": viz_users
    }).json()
    
    # 创建 Question 2
    r2 = requests.post(f"{METABASE_URL}/api/card", headers=headers, json={
        "name": "【收入分析】用户类型收入分布 - 萝卜测试",
        "type": "question",
        "dataset_query": {"type": "query", "database": 4, "query": mbql_revenue},
        "display": "bar",
        "collection_id": 396,
        "visualization_settings": viz_revenue
    }).json()
    
    print("\n" + "=" * 60)
    print("创建两个独立的分析 Question")
    print("=" * 60)
    
    ids = []
    if 'id' in r1:
        print(f"\n✅ 人数漏斗 (ID: {r1['id']})")
        print(f"   https://kmb.qunhequnhe.com/question/{r1['id']}")
        ids.append(r1['id'])
    
    if 'id' in r2:
        print(f"\n✅ 收入分析 (ID: {r2['id']})")
        print(f"   https://kmb.qunhequnhe.com/question/{r2['id']}")
        ids.append(r2['id'])
    
    return ids

if __name__ == "__main__":
    print("选择创建方式:")
    print("1. 转化率分析 (使用表达式计算百分比)")
    print("2. 两个独立图表 (人数 + 收入分开)")
    
    # 默认创建方式1
    id1 = create_conversion_rate_question()
    ids2 = create_two_chart_dashboard()
    
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print("\n专业做法:")
    print("  • 方式1: 计算转化率/客单价等派生指标，同单位可比")
    print("  • 方式2: 人数和收入完全分开两个图表，避免混淆")
    print("\n之前的问题:")
    print("  ❌ 人数(人)和金额($)混在同一个柱状图")
    print("  ❌ 量级差异大(千 vs 十万)，视觉不可比")
