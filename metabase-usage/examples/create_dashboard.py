#!/usr/bin/env python3
"""
创建新的 Dashboard 并引用 Question 4374
"""

import requests
import json

METABASE_URL = "https://kmb.qunhequnhe.com"
API_KEY = "mb_h5ddq58TgNTAZsV7e81myvAxMlMcqXWrx1y9TdqArl8="

def create_dashboard_with_question():
    """创建 Dashboard 并添加 Question 4374"""
    
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # 1. 先创建 Dashboard
    dashboard_payload = {
        "name": "转化效率分析 Dashboard - 萝卜测试",
        "collection_id": 396,  # COOHOM折扣体系
        "description": "用户类型转化效率分析，包含转化率和客单价核心指标"
    }
    
    print("=" * 60)
    print("创建 Dashboard")
    print("=" * 60)
    
    resp = requests.post(
        f"{METABASE_URL}/api/dashboard",
        headers=headers,
        json=dashboard_payload
    )
    
    dashboard = resp.json()
    
    if 'id' not in dashboard:
        print(f"❌ 创建失败: {dashboard}")
        return None
    
    dashboard_id = dashboard['id']
    print(f"\n✅ Dashboard 创建成功!")
    print(f"   ID: {dashboard_id}")
    print(f"   名称: {dashboard['name']}")
    
    # 2. 添加 Question 4374 到 Dashboard
    # Dashboard 网格: 24列 x N行，每个卡片用 (col, row, size_x, size_y) 定位
    dashcard_payload = {
        "cardId": 4374,  # 用户类型转化效率分析
        "row": 0,        # 第0行开始
        "col": 0,        # 第0列开始
        "size_x": 18,    # 宽度占18格 (24格满宽)
        "size_y": 8      # 高度8格
    }
    
    print(f"\n添加 Question 4374 到 Dashboard...")
    
    resp2 = requests.post(
        f"{METABASE_URL}/api/dashboard/{dashboard_id}/cards",
        headers=headers,
        json=dashcard_payload
    )
    
    result = resp2.json()
    
    if resp2.status_code in [200, 201]:
        print(f"✅ Question 添加成功!")
        print(f"\n" + "=" * 60)
        print("完成!")
        print("=" * 60)
        print(f"Dashboard ID: {dashboard_id}")
        print(f"访问链接: https://kmb.qunhequnhe.com/dashboard/{dashboard_id}")
        print(f"\n包含的 Question:")
        print(f"  • 4374 - 用户类型转化效率分析")
        print(f"    (转化率柱状图 + 详细数据表)")
        return dashboard_id
    else:
        print(f"❌ 添加 Question 失败: {result}")
        return None

def create_full_dashboard():
    """创建一个更完整的 Dashboard，包含多个卡片"""
    
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # 创建 Dashboard
    dashboard_payload = {
        "name": "萝卜的转化分析看板",
        "collection_id": 396,
        "description": "基于 Model 3953 的转化效率分析"
    }
    
    print("=" * 60)
    print("创建完整版 Dashboard")
    print("=" * 60)
    
    resp = requests.post(
        f"{METABASE_URL}/api/dashboard",
        headers=headers,
        json=dashboard_payload
    )
    
    dashboard = resp.json()
    
    if 'id' not in dashboard:
        print(f"❌ 失败: {dashboard}")
        return None
    
    dashboard_id = dashboard['id']
    print(f"\n✅ Dashboard 创建: ID {dashboard_id}")
    
    # 添加多个卡片
    cards = [
        {
            "cardId": 4374,      # 转化效率分析
            "row": 0,
            "col": 0,
            "size_x": 16,
            "size_y": 8
        },
        {
            "cardId": 4371,      # 原来的对比分析
            "row": 0,
            "col": 16,
            "size_x": 8,
            "size_y": 8
        }
    ]
    
    for i, card in enumerate(cards):
        resp = requests.post(
            f"{METABASE_URL}/api/dashboard/{dashboard_id}/cards",
            headers=headers,
            json=card
        )
        if resp.status_code in [200, 201]:
            print(f"✅ 卡片 {i+1} (Question {card['cardId']}) 添加成功")
        else:
            print(f"⚠️ 卡片 {i+1} 添加失败: {resp.text[:100]}")
    
    print(f"\n访问: https://kmb.qunhequnhe.com/dashboard/{dashboard_id}")
    return dashboard_id

if __name__ == "__main__":
    # 创建简单版
    id1 = create_dashboard_with_question()
    
    print("\n" + "-" * 60)
    
    # 创建完整版
    id2 = create_full_dashboard()
