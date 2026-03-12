#!/usr/bin/env python3
"""
AARRR 周报数据处理器
处理 Metabase API 获取的原始数据，生成周报报告
"""

import json
from datetime import datetime

def load_json(filepath):
    """加载 JSON 文件"""
    with open(filepath, 'r') as f:
        return json.load(f)

def parse_acquisition_data(data):
    """解析 Acquisition 数据"""
    rows = data['data']['rows']
    
    # 按周分组
    weekly_data = {}
    for row in rows:
        week = row[0]  # 日期
        channel = row[1]  # 渠道
        visitors = row[2]  # 新访客数
        registrations = row[3]  # 新访客注册数
        conversion = row[4] * 100 if row[4] else 0  # 转化率
        
        if week not in weekly_data:
            weekly_data[week] = {}
        weekly_data[week][channel] = {
            'visitors': visitors,
            'registrations': registrations,
            'conversion': conversion
        }
    
    return weekly_data

def parse_activation_data(data):
    """解析 Activation 数据"""
    rows = data['data']['rows']
    
    weekly_data = {}
    for row in rows:
        week = row[0]
        weekly_data[week] = {
            'new_users': row[1],
            'tool_conversion': row[2] * 100,
            'tool_users': row[3],
            'draw_conversion': row[4] * 100,
            'draw_users': row[5],
            'model_conversion': row[6] * 100,
            'model_users': row[7],
            'render_conversion': row[8] * 100,
            'render_users': row[9],
            'total_tool': row[10] * 100,
            'total_draw': row[11] * 100,
            'total_model': row[12] * 100,
            'total_render': row[13] * 100
        }
    
    return weekly_data

def parse_retention_wau(data):
    """解析 WAU 数据"""
    rows = data['data']['rows']
    
    weekly_data = {}
    for row in rows:
        week = row[0]
        weekly_data[week] = {
            'total_wau': row[1],
            'new_wau': row[2],
            'old_wau': row[3]
        }
    
    return weekly_data

def parse_retention_rate(data):
    """解析留存率数据"""
    rows = data['data']['rows']
    
    weekly_data = {}
    for row in rows:
        week = row[0]
        user_type = row[1]  # 新注册/老用户
        last_week_wau = row[2]
        this_week_wau = row[3]
        retention = row[4] * 100
        
        if week not in weekly_data:
            weekly_data[week] = {}
        weekly_data[week][user_type] = {
            'last_wau': last_week_wau,
            'this_wau': this_week_wau,
            'retention': retention
        }
    
    return weekly_data

def parse_revenue_data(data):
    """解析收入数据"""
    rows = data['data']['rows']
    
    weekly_data = {}
    for row in rows:
        week = row[0]
        weekly_data[week] = {
            'total': row[1],
            'new': row[2],
            'renewal': row[3],
            'total_users': row[4],
            'new_users': row[5],
            'renewal_users': row[6],
            'avg_price': row[7],
            'new_price': row[8],
            'renewal_price': row[9]
        }
    
    return weekly_data

def calc_change(current, previous):
    """计算变化率和箭头"""
    if previous == 0:
        return "-", "→"
    change = ((current - previous) / previous) * 100
    arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
    return f"{change:+.2f}%", arrow

def generate_report():
    """生成完整周报"""
    
    # 加载数据
    acquisition_data = parse_acquisition_data(
        load_json('/Users/imsuansuanru/.openclaw/workspace/data/acquisition_visitors.json')
    )
    activation_data = parse_activation_data(
        load_json('/Users/imsuansuanru/.openclaw/workspace/data/activation_funnel.json')
    )
    retention_wau = parse_retention_wau(
        load_json('/Users/imsuansuanru/.openclaw/workspace/data/retention_wau.json')
    )
    retention_rate = parse_retention_rate(
        load_json('/Users/imsuansuanru/.openclaw/workspace/data/retention_rate.json')
    )
    revenue_data = parse_revenue_data(
        load_json('/Users/imsuansuanru/.openclaw/workspace/data/revenue.json')
    )
    
    # 确定数据周期
    current_week = '20260302'  # 本周
    last_week = '20260223'     # 上周
    
    # Acquisition 当前周 vs 上周
    curr_acq = acquisition_data.get(current_week, {})
    last_acq = acquisition_data.get(last_week, {})
    
    # 计算整体表现
    total_visitors_curr = sum(v['visitors'] for v in curr_acq.values())
    total_registrations_curr = sum(v['registrations'] for v in curr_acq.values())
    total_conversion_curr = (total_registrations_curr / total_visitors_curr * 100) if total_visitors_curr else 0
    
    total_visitors_last = sum(v['visitors'] for v in last_acq.values())
    total_registrations_last = sum(v['registrations'] for v in last_acq.values())
    total_conversion_last = (total_registrations_last / total_visitors_last * 100) if total_visitors_last else 0
    
    # Activation 对比前两周（转化完成周期）
    # 当前分析的是 20260223 vs 20260216
    activation_current = activation_data.get('20260223', {})
    activation_compare = activation_data.get('20260216', {})
    
    # Retention - WAU 用本周，留存率用前两周（已转化完成）
    wau_current = retention_wau.get(current_week, {})
    wau_last = retention_wau.get(last_week, {})
    
    # 留存率用 20260223（对比 20260216 的留存）
    retention_current = retention_rate.get('20260223', {})
    retention_compare_week = '20260216'
    retention_compare = retention_rate.get(retention_compare_week, {})
    
    # Revenue 当前周 vs 上周
    revenue_current = revenue_data.get(current_week, {})
    revenue_last = revenue_data.get(last_week, {})
    
    # 计算变化
    visitors_change, visitors_arrow = calc_change(total_visitors_curr, total_visitors_last)
    reg_change, reg_arrow = calc_change(total_registrations_curr, total_registrations_last)
    conv_change = total_conversion_curr - total_conversion_last
    conv_arrow = "↑" if conv_change > 0 else "↓" if conv_change < 0 else "→"
    
    wau_change, wau_arrow = calc_change(wau_current.get('total_wau', 0), wau_last.get('total_wau', 0))
    new_wau_change, new_wau_arrow = calc_change(wau_current.get('new_wau', 0), wau_last.get('new_wau', 0))
    old_wau_change, old_wau_arrow = calc_change(wau_current.get('old_wau', 0), wau_last.get('old_wau', 0))
    
    # Revenue 变化
    rev_change = revenue_current.get('total', 0) - revenue_last.get('total', 0)
    rev_change_pct = (rev_change / revenue_last.get('total', 1)) * 100 if revenue_last.get('total', 0) else 0
    rev_arrow = "↑" if rev_change > 0 else "↓" if rev_change < 0 else "→"
    
    # 构建报告
    report = f"""# AARRR周报 - 2026年3月9日周

> 📅 数据周期：2026/03/02 - 2026/03/09
> 📈 对比周期：2026/02/23 - 2026/03/02
> 🕐 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 一、Acquisition / 流量获取

### 整体表现
- 总新访客: {total_visitors_curr:,}人
- 总注册数: {total_registrations_curr:,}人
- 整体转化率: {total_conversion_curr:.2f}%

### 环比上周变化
- 新访客: {visitors_arrow} {visitors_change}
- 注册数: {reg_arrow} {reg_change}
- 注册转化率: {conv_arrow} {conv_change:+.2f}个百分点

### 注意项
"""
    
    # 添加渠道注意项 - 特别关注 paid ads 和 organic search（每周必看）
    # 1. 优先处理 paid ads 和 organic search
    priority_channels = ['paid ads', 'organic search']
    for channel in priority_channels:
        if channel in curr_acq and channel in last_acq:
            curr_data = curr_acq[channel]
            last_data = last_acq[channel]
            visitor_change = ((curr_data['visitors'] - last_data['visitors']) / last_data['visitors']) * 100
            conv_change_val = curr_data['conversion'] - last_data['conversion']
            
            if channel == 'paid ads':
                # paid ads 分析：关注量增质降
                if visitor_change > 0 and conv_change_val < 0:
                    report += f"- paid ads: 渠道访客增长{visitor_change:.1f}%，但转化率下降{abs(conv_change_val):.1f}pp，出现量增质降，需优化投放素材/定向\n"
                elif visitor_change > 0:
                    report += f"- paid ads: 渠道访客增长{visitor_change:.1f}%，转化率{conv_change_val:+.1f}pp，投放效果{'良好' if conv_change_val >= 0 else '需优化'}\n"
                else:
                    report += f"- paid ads: 渠道访客下降{abs(visitor_change):.1f}%，需检查预算/出价策略\n"
            
            elif channel == 'organic search':
                # organic search 分析：关注SEO效果
                if visitor_change < -5:
                    report += f"- organic search: 渠道访客量下降{abs(visitor_change):.1f}%，转化率{conv_change_val:+.1f}pp，需关注SEO效果及核心关键词排名\n"
                elif conv_change_val < -1:
                    report += f"- organic search: 渠道转化率下降{abs(conv_change_val):.1f}pp，需优化着陆页体验\n"
                else:
                    report += f"- organic search: 渠道访客量{visitor_change:+.1f}%，整体表现{'平稳' if abs(visitor_change) < 5 else '波动'}\n"
    
    # 2. 其他异常渠道
    for channel, curr_data in curr_acq.items():
        if channel in priority_channels:
            continue  # 跳过已处理的优先渠道
        last_data = last_acq.get(channel, {'visitors': 0, 'registrations': 0, 'conversion': 0})
        if last_data['visitors'] > 0:
            visitor_change = ((curr_data['visitors'] - last_data['visitors']) / last_data['visitors']) * 100
            conv_change_val = curr_data['conversion'] - last_data['conversion']
            
            # 标记异常渠道
            if abs(visitor_change) > 30 or abs(conv_change_val) > 5:
                change_desc = f"访客量{'增长' if visitor_change > 0 else '下降'}{abs(visitor_change):.1f}%"
                conv_desc = f"转化率{'提升' if conv_change_val > 0 else '下降'}{abs(conv_change_val):.1f}pp"
                
                if visitor_change > 30 and conv_change_val < -2:
                    report += f"- {channel}: 渠道出现量增质降（{change_desc}但{conv_desc}）\n"
                elif visitor_change < -10:
                    report += f"- {channel}: 渠道访客量下降{abs(visitor_change):.1f}%，需关注\n"
                elif conv_change_val > 3:
                    report += f"- {channel}: 渠道转化率提升{conv_change_val:.1f}pp至{curr_data['conversion']:.2f}%\n"
    
    # 添加详细表格
    report += "\n### 详细数据\n\n| 渠道 | 新访客(环比) | 注册数(环比) | 转化率(环比) |\n|------|-------------|-------------|-------------|\n"
    
    # 按访客数排序
    sorted_channels = sorted(curr_acq.items(), key=lambda x: x[1]['visitors'], reverse=True)
    for channel, curr_data in sorted_channels[:8]:  # 取前8个渠道
        last_data = last_acq.get(channel, {'visitors': 0, 'registrations': 0, 'conversion': 0})
        
        if last_data['visitors'] > 0:
            visitor_change = ((curr_data['visitors'] - last_data['visitors']) / last_data['visitors']) * 100
            reg_change_val = ((curr_data['registrations'] - last_data['registrations']) / last_data['registrations']) * 100 if last_data['registrations'] else 0
            conv_change_val = curr_data['conversion'] - last_data['conversion']
            
            v_arrow = "↑" if visitor_change > 0 else "↓"
            r_arrow = "↑" if reg_change_val > 0 else "↓"
            c_arrow = "↑" if conv_change_val > 0 else "↓"
            
            report += f"| {channel} | {curr_data['visitors']:,} ({v_arrow}{visitor_change:.1f}%) | {curr_data['registrations']:,} ({r_arrow}{reg_change_val:.1f}%) | {curr_data['conversion']:.2f}% ({c_arrow}{conv_change_val:.1f}pp) |\n"
        else:
            report += f"| {channel} | {curr_data['visitors']:,} (new) | {curr_data['registrations']:,} (new) | {curr_data['conversion']:.2f}% (new) |\n"
    
    # Activation 部分
    report += f"""\n---

## 二、Activation / 激活转化

> 说明：Activation数据对比逻辑为"转化完成的周"，故对比前两周数据（2026/02/23 vs 2026/02/16）

### 完整数据对比

| 步骤 | 当前周期(2026/02/23) | 对比周期(2026/02/16) | 环比变化 |
|------|---------------------|---------------------|---------|
| 新注册用户数 | {activation_current.get('new_users', 0):,} | {activation_compare.get('new_users', 0):,} | {calc_change(activation_current.get('new_users', 0), activation_compare.get('new_users', 0))[1]} {calc_change(activation_current.get('new_users', 0), activation_compare.get('new_users', 0))[0]} |
| 注册→进工具 | {activation_current.get('tool_users', 0):,} ({activation_current.get('tool_conversion', 0):.2f}%) | {activation_compare.get('tool_users', 0):,} ({activation_compare.get('tool_conversion', 0):.2f}%) | {activation_current.get('tool_conversion', 0) - activation_compare.get('tool_conversion', 0):+.2f}pp |
| 进工具→画户型 | {activation_current.get('draw_users', 0):,} ({activation_current.get('draw_conversion', 0):.2f}%) | {activation_compare.get('draw_users', 0):,} ({activation_compare.get('draw_conversion', 0):.2f}%) | {activation_current.get('draw_conversion', 0) - activation_compare.get('draw_conversion', 0):+.2f}pp |
| 画户型→拖模型 | {activation_current.get('model_users', 0):,} ({activation_current.get('model_conversion', 0):.2f}%) | {activation_compare.get('model_users', 0):,} ({activation_compare.get('model_conversion', 0):.2f}%) | {activation_current.get('model_conversion', 0) - activation_compare.get('model_conversion', 0):+.2f}pp |
| 拖模型→渲染 | {activation_current.get('render_users', 0):,} ({activation_current.get('render_conversion', 0):.2f}%) | {activation_compare.get('render_users', 0):,} ({activation_compare.get('render_conversion', 0):.2f}%) | {activation_current.get('render_conversion', 0) - activation_compare.get('render_conversion', 0):+.2f}pp |
| 渲染总转化率 | {activation_current.get('total_render', 0):.2f}% | {activation_compare.get('total_render', 0):.2f}% | {activation_current.get('total_render', 0) - activation_compare.get('total_render', 0):+.2f}pp |

### 关键发现
"""
    
    # 添加 Activation 关键发现
    render_change = activation_current.get('total_render', 0) - activation_compare.get('total_render', 0)
    if render_change > 0:
        report += f"- 渲染总转化率提升：{activation_compare.get('total_render', 0):.2f}% → {activation_current.get('total_render', 0):.2f}%（↑{render_change:.2f}pp），是本周亮点\n"
    else:
        report += f"- 渲染总转化率下降：{activation_compare.get('total_render', 0):.2f}% → {activation_current.get('total_render', 0):.2f}%（↓{abs(render_change):.2f}pp），需关注\n"
    
    tool_change = activation_current.get('tool_conversion', 0) - activation_compare.get('tool_conversion', 0)
    report += f"- 注册→进工具转化率：{activation_compare.get('tool_conversion', 0):.2f}% → {activation_current.get('tool_conversion', 0):.2f}%（{'↑' if tool_change > 0 else '↓'}{abs(tool_change):.2f}pp）\n"
    
    # Retention 部分
    report += f"""\n---

## 三、Retention / 用户留存

### WAU分析
- 当周WAU: {wau_current.get('total_wau', 0):,}人
- 新用户WAU: {wau_current.get('new_wau', 0):,}人（环比{new_wau_arrow} {new_wau_change}）
- 老用户WAU: {wau_current.get('old_wau', 0):,}人（环比{old_wau_arrow} {old_wau_change}）

### 留存率统计（次周留存）
> 说明：对比第N-2周注册用户在第N周的留存（已转化完成周期）

| 用户类型 | 当前周期(2026/02/23) | 对比周期(2026/02/16) | 环比变化 |
|---------|---------------------|---------------------|---------|
| 新用户留存率 | {retention_current.get('新注册', {}).get('retention', 0):.2f}% | {retention_compare.get('新注册', {}).get('retention', 0):.2f}% | {(retention_current.get('新注册', {}).get('retention', 0) - retention_compare.get('新注册', {}).get('retention', 0)):+.2f}个百分点 |
| 老用户留存率 | {retention_current.get('老用户', {}).get('retention', 0):.2f}% | {retention_compare.get('老用户', {}).get('retention', 0):.2f}% | {(retention_current.get('老用户', {}).get('retention', 0) - retention_compare.get('老用户', {}).get('retention', 0)):+.2f}个百分点 |

### 关键发现
"""
    
    new_ret_change = retention_current.get('新注册', {}).get('retention', 0) - retention_compare.get('新注册', {}).get('retention', 0)
    old_ret_change = retention_current.get('老用户', {}).get('retention', 0) - retention_compare.get('老用户', {}).get('retention', 0)
    
    if new_ret_change > 0:
        report += f"- 新用户留存率提升：{retention_compare.get('新注册', {}).get('retention', 0):.2f}% → {retention_current.get('新注册', {}).get('retention', 0):.2f}%（↑{new_ret_change:.2f}pp）\n"
    else:
        report += f"- 新用户留存率下降：{retention_compare.get('新注册', {}).get('retention', 0):.2f}% → {retention_current.get('新注册', {}).get('retention', 0):.2f}%（↓{abs(new_ret_change):.2f}pp）\n"
    
    if old_ret_change > 0:
        report += f"- 老用户留存率提升：{retention_compare.get('老用户', {}).get('retention', 0):.2f}% → {retention_current.get('老用户', {}).get('retention', 0):.2f}%（↑{old_ret_change:.2f}pp）\n"
    else:
        report += f"- 老用户留存率下降：{retention_compare.get('老用户', {}).get('retention', 0):.2f}% → {retention_current.get('老用户', {}).get('retention', 0):.2f}%（↓{abs(old_ret_change):.2f}pp）\n"
    
    # Revenue 部分
    report += f"""\n---

## 四、Revenue / 收入分析

当周收入 {revenue_current.get('total', 0):,.0f} 美元，较上周 {rev_arrow} {abs(rev_change):,.0f}美元，增长率 {rev_change_pct:+.1f}%。
其中，新签收入{'增加' if revenue_current.get('new', 0) > revenue_last.get('new', 0) else '减少'} {abs(revenue_current.get('new', 0) - revenue_last.get('new', 0)):,.0f} 美元（增长率 {((revenue_current.get('new', 0) - revenue_last.get('new', 0)) / revenue_last.get('new', 0) * 100) if revenue_last.get('new', 0) else 0:+.0f}%），续约收入{'增加' if revenue_current.get('renewal', 0) > revenue_last.get('renewal', 0) else '减少'} {abs(revenue_current.get('renewal', 0) - revenue_last.get('renewal', 0)):,.0f} 美元（增长率 {((revenue_current.get('renewal', 0) - revenue_last.get('renewal', 0)) / revenue_last.get('renewal', 0) * 100) if revenue_last.get('renewal', 0) else 0:+.0f}%）。

### 详细数据
- 付费用户数：{revenue_current.get('total_users', 0):,}人（环比{calc_change(revenue_current.get('total_users', 0), revenue_last.get('total_users', 0))[1]} {calc_change(revenue_current.get('total_users', 0), revenue_last.get('total_users', 0))[0]}）
- 新签用户数：{revenue_current.get('new_users', 0):,}人
- 续约用户数：{revenue_current.get('renewal_users', 0):,}人
- 整体客单价：${revenue_current.get('avg_price', 0):.1f}（环比{calc_change(revenue_current.get('avg_price', 0), revenue_last.get('avg_price', 0))[1]} {calc_change(revenue_current.get('avg_price', 0), revenue_last.get('avg_price', 0))[0]}）
- 新签客单价：${revenue_current.get('new_price', 0):.1f}
- 续约客单价：${revenue_current.get('renewal_price', 0):.1f}

---

## 五、Referral / 推荐传播

> 当前仪表板暂未配置推荐相关数据指标

### 建议追踪指标
- 邀请注册数
- 邀请转化率
- 病毒系数 (K-factor)
- 分享次数/用户

---

## 六、综合分析与建议

### 本周亮点
"""
    
    # 添加亮点
    if total_conversion_curr > total_conversion_last:
        report += f"- 整体转化率提升：{total_conversion_last:.2f}% → {total_conversion_curr:.2f}%（↑{conv_change:.2f}pp）\n"
    if render_change > 0:
        report += f"- 渲染转化率大幅提升：{activation_compare.get('total_render', 0):.2f}% → {activation_current.get('total_render', 0):.2f}%（↑{render_change:.2f}pp）\n"
    if new_ret_change > 0:
        report += f"- 新用户留存率回升：{retention_compare.get('新注册', {}).get('retention', 0):.2f}% → {retention_current.get('新注册', {}).get('retention', 0):.2f}%（↑{new_ret_change:.2f}pp）\n"
    if revenue_current.get('new', 0) > revenue_last.get('new', 0):
        report += f"- 新签收入增长：+{revenue_current.get('new', 0) - revenue_last.get('new', 0):,.0f}美元（+{((revenue_current.get('new', 0) - revenue_last.get('new', 0)) / revenue_last.get('new', 0) * 100) if revenue_last.get('new', 0) else 0:.0f}%）\n"
    
    report += "\n### 核心风险\n"
    
    # 添加风险
    if total_visitors_curr < total_visitors_last:
        report += f"- 总访客量下滑：{visitors_change}\n"
    if revenue_current.get('total', 0) < revenue_last.get('total', 0):
        report += f"- 总收入下滑：{rev_arrow}{abs(rev_change_pct):.0f}%\n"
    if old_ret_change < 0:
        report += f"- 老用户留存率下降：↓{abs(old_ret_change):.2f}pp\n"
    
    report += "\n### 行动建议\n\n**紧急（本周内）**\n"
    
    # 添加行动建议
    if revenue_current.get('renewal', 0) < revenue_last.get('renewal', 0):
        report += "- 关注续约收入下滑，联系客户成功团队排查高价值客户流失\n"
    
    # 检查是否有渠道流量暴跌
    for channel, curr_data in curr_acq.items():
        last_data = last_acq.get(channel, {'visitors': 0})
        if last_data['visitors'] > 0:
            visitor_change = ((curr_data['visitors'] - last_data['visitors']) / last_data['visitors']) * 100
            if visitor_change < -30:
                report += f"- 排查{channel}渠道：流量暴跌{abs(visitor_change):.0f}%，需紧急检查\n"
                break
    
    report += """\n**重要（本月内）**
- 持续监控渠道转化率变化，优化投放策略
- 分析用户留存率波动原因，制定提升方案
\n**规划（季度）**
- 搭建Referral推荐体系
- 建立渠道ROI评估体系
\n---

报告由系统自动生成，数据仅供参考。
"""
    
    return report

if __name__ == '__main__':
    report = generate_report()
    
    # 保存报告
    with open('/Users/imsuansuanru/.openclaw/workspace/reports/aarrr_weekly_report_20260309.md', 'w') as f:
        f.write(report)
    
    print("报告生成完成！")
    print("=" * 50)
    print(report[:1000])
    print("...")
    print(f"\n完整报告已保存到: /Users/imsuansuanru/.openclaw/workspace/reports/aarrr_weekly_report_20260309.md")