#!/usr/bin/env python3
"""
创建新的 MBQL Question - 分用户类型支付转化率分析
基于 Model 3953，保存在 Collection 396 (COOHOM折扣体系)
"""

import requests
import json

METABASE_URL = "https://kmb.qunhequnhe.com"
API_KEY = "mb_h5ddq58TgNTAZsV7e81myvAxMlMcqXWrx1y9TdqArl8="

def create_question():
    # 构建 MBQL: 分用户类型支付转化率分析
    mbql_query = {
        "source-table": "card__3953",
        "breakout": [
            ["field", "user_type", {"base-type": "type/Text"}]
        ],
        "aggregation": [
            # 意向行为UV (去重用户数)
            ["aggregation-options",
             ["distinct", ["field", "user_id", {"base-type": "type/BigInteger"}]],
             {"name": "意向用户", "display-name": "意向用户"}],
            
            # 支付成功人数 (条件聚合)
            ["aggregation-options",
             ["distinct",
              ["if",
               [[["not-null", ["field", "pay_success_date", {"base-type": "type/DateTime"}]],
                 ["field", "user_id", {"base-type": "type/BigInteger"}]]]]],
             {"name": "支付成功", "display-name": "支付成功"}],
            
            # 总收入
            ["aggregation-options",
             ["sum", ["field", "amt_usd", {"base-type": "type/Float"}]],
             {"name": "总收入", "display-name": "总收入(USD)"}]
        ],
        "order-by": [
            ["desc", ["aggregation", 1]]  # 按支付成功人数降序
        ]
    }
    
    # 可视化配置 - 柱状图，双轴显示
    viz_settings = {
        "graph.dimensions": ["user_type"],
        "graph.metrics": ["意向用户", "支付成功", "总收入"],
        "series_settings": {
            "意向用户": {"axis": "left", "color": "#8AE6E3"},
            "支付成功": {"axis": "left", "color": "#87BCEC"},
            "总收入": {"axis": "right", "color": "#F9D423"}
        },
        "graph.show_values": True,
        "stackable.stack_type": None
    }
    
    # API 请求
    url = f"{METABASE_URL}/api/card"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": "分用户类型转化分析 - 萝卜测试",
        "type": "question",
        "dataset_query": {
            "type": "query",
            "database": 4,
            "query": mbql_query
        },
        "display": "bar",  # 柱状图
        "collection_id": 396,  # COOHOM折扣体系集合
        "visualization_settings": viz_settings
    }
    
    print("=" * 50)
    print("创建 MBQL Question")
    print("=" * 50)
    print(f"\n请求 URL: {url}")
    print(f"集合 ID: 396 (COOHOM折扣体系)")
    print(f"数据源: Model 3953 (意向用户付费model)")
    
    print("\n--- MBQL Query ---")
    print(json.dumps(mbql_query, indent=2, ensure_ascii=False))
    
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    print("\n" + "=" * 50)
    print("响应结果")
    print("=" * 50)
    
    if 'id' in result:
        print(f"\n✅ Question 创建成功!")
        print(f"   ID: {result['id']}")
        print(f"   名称: {result['name']}")
        print(f"   集合 ID: {result.get('collection_id')}")
        print(f"   查询类型: {result.get('query_type')}")
        print(f"   可视化: {result.get('display')}")
        print(f"\n   访问链接:")
        print(f"   https://kmb.qunhequnhe.com/question/{result['id']}")
        return result['id']
    else:
        print(f"\n❌ 创建失败:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return None

if __name__ == "__main__":
    question_id = create_question()
    if question_id:
        print(f"\n🎉 成功创建 Question ID: {question_id}")
