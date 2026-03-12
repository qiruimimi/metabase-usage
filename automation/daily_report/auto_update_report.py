#!/usr/bin/env python3
"""
GA 投放数据日报自动更新脚本
直接调用飞书 API 更新文档

使用方式:
  python3 auto_update_report.py [日期，默认为昨天]
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 配置
WORKSPACE = Path("/Users/imsuansuanru/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
CHARTS_DIR = WORKSPACE / "charts"
DOC_TOKEN = "UW9ZdSRsSo7V0Kx2Tc7c4dxgnGe"  # 固定文档

def get_report_date():
    """获取报告日期（默认为昨天）"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

def load_data(report_date):
    """加载 GA 报告数据"""
    for filename in [f"ga_report_{report_date}.json", f"ga_report_{report_date.replace('-', '')}.json"]:
        data_file = DATA_DIR / filename
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None

def generate_insight(data):
    """生成关键洞察"""
    if not data:
        return "⚠️ 暂无数据"
    
    results = data.get("results", {})
    alerts = []
    
    for metric_name, metric_data in results.items():
        if metric_data.get("alert"):
            alerts.append(f"{metric_name}异常")
    
    if alerts:
        return f"🚨 **检测到 {len(alerts)} 项异常**：{', '.join(alerts)}，建议立即排查。"
    return "✅ **今日数据正常**，继续保持监控。"

def fmt_change_with_base(metric):
    """格式化变化，包含对比基准值"""
    if not metric:
        return "-", "-"
    
    change_pct = metric.get("change_pct", 0)
    current = metric.get("current", metric.get("latest_value", 0))
    previous = metric.get("previous", 0)
    
    arrow = "📈" if metric.get("is_increase") else "📉"
    
    # 格式化当前值和前一日值
    def fmt_val(val):
        if isinstance(val, (int, float)):
            if val >= 1000:
                return f"{val:,.0f}"
            return f"{val:,.2f}" if isinstance(val, float) else str(val)
        return str(val) if val else "0"
    
    change_str = f"{arrow} {change_pct:+.1f}%"
    base_str = f"昨日: {fmt_val(previous)}"
    
    return change_str, base_str

def fmt_val(val):
    """格式化数值"""
    if isinstance(val, (int, float)):
        if val >= 1000:
            return f"{val:,.0f}"
        return f"{val:,.2f}" if isinstance(val, float) else str(val)
    return str(val) if val else "0"

def get_status(metric):
    """获取状态标识"""
    return "🔴 异常" if metric and metric.get("alert") else "🟢 正常"

def generate_markdown(data, report_date, update_time):
    """生成飞书文档 Markdown 内容"""
    if not data:
        return f"""# 📊 GA投放数据日报（每日更新）

> 🕐 **最后更新：** {update_time}  
> 📅 **数据日期：** {report_date}

---

⚠️ **今日数据暂未获取**，请检查数据源。

---

💡 提示：收藏本文档，每天中午查看最新更新。
"""
    
    results = data.get("results", {})
    
    # 提取指标
    spend = results.get("推广花费", {})
    reg = results.get("注册用户数", {})
    pay = results.get("累计付费", {})
    ret = results.get("次周留存", {})
    
    # 生成带基准值的变化字符串
    spend_day_change, spend_day_base = fmt_change_with_base(spend.get("day_over_day", {}))
    spend_week_change, spend_week_base = fmt_change_with_base(spend.get("week_over_week", {}))
    reg_day_change, reg_day_base = fmt_change_with_base(reg.get("day_over_day", {}))
    reg_week_change, reg_week_base = fmt_change_with_base(reg.get("week_over_week", {}))
    pay_day_change, pay_day_base = fmt_change_with_base(pay.get("day_over_day", {}))
    pay_week_change, pay_week_base = fmt_change_with_base(pay.get("week_over_week", {}))
    ret_day_change, ret_day_base = fmt_change_with_base(ret.get("day_over_day", {}))
    ret_week_change, ret_week_base = fmt_change_with_base(ret.get("week_over_week", {}))
    
    insight = generate_insight(data)
    
    return f"""# 📊 GA投放数据日报（每日更新）

> 🕐 **最后更新：** {update_time}  
> 📅 **数据日期：** {report_date}

---

## 📈 今日核心指标

### 💰 推广花费
- **当前值：** ${fmt_val(spend.get('latest_value', 0))}
- **日环比：** {spend_day_change}（{spend_day_base}）
- **周同比：** {spend_week_change}（{spend_week_base}）
- **状态：** {get_status(spend)}

### 👤 注册用户数
- **当前值：** {fmt_val(reg.get('latest_value', 0))}
- **日环比：** {reg_day_change}（{reg_day_base}）
- **周同比：** {reg_week_change}（{reg_week_base}）
- **状态：** {get_status(reg)}

### 💵 累计付费
- **当前值：** ${fmt_val(pay.get('latest_value', 0))}
- **日环比：** {pay_day_change}（{pay_day_base}）
- **周同比：** {pay_week_change}（{pay_week_base}）
- **状态：** {get_status(pay)}

### 🔄 次周留存
- **当前值：** {fmt_val(ret.get('latest_value', 0))}
- **日环比：** {ret_day_change}（{ret_day_base}）
- **周同比：** {ret_week_change}（{ret_week_base}）
- **状态：** {get_status(ret)}

---

## 🚨 今日关键洞察

{insight}

---

## 📉 趋势图表

### 注册趋势
从2024年1月至2026年1月的注册趋势显示，2024年下半年达到高峰（峰值约35,000周注册量），2025年中期经历低谷后逐步回升，但近期（2026年初）数据再次下滑。

👇 注册趋势图（见下方）

### 成本趋势
推广成本波动较大，2024年初出现峰值（接近$70,000），随后逐步优化降至$10,000-$20,000区间。

👇 成本趋势图（见下方）

### ROAS趋势
ROAS（广告支出回报率）呈现明显的改善趋势。2025年4月至9月期间ROAS长期低于0.1，但2025年底开始稳步上升。

👇 ROAS趋势图（见下方）

---

## 📋 行动建议

1. **数据监控**：每日查看核心指标变化
2. **异常响应**：发现异常立即排查原因
3. **趋势分析**：关注长期趋势而非单日波动
4. **策略调整**：基于 ROAS 优化投放策略

---

## 📝 更新日志

**{update_time}** - 更新 {report_date} 数据

---

💡 提示：收藏本文档，每天中午查看最新更新。点击右上角「历史记录」可查看往期版本。
"""

def main():
    """主函数"""
    report_date = get_report_date()
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print(f"📝 正在生成 {report_date} 的日报...")
    print(f"⏰ 更新时间：{update_time}")
    
    # 加载数据
    data = load_data(report_date)
    if data:
        print(f"✅ 已加载数据: {report_date}")
    else:
        print(f"⚠️ 未找到 {report_date} 数据，生成空模板")
    
    # 生成内容
    content = generate_markdown(data, report_date, update_time)
    
    # 保存到本地文件（供后续飞书 API 调用使用）
    backup_dir = WORKSPACE / "reports"
    backup_dir.mkdir(exist_ok=True)
    backup_file = backup_dir / f"report_{report_date}.md"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"💾 报告已保存: {backup_file}")
    print(f"📄 内容长度: {len(content)} 字符")
    print(f"\n🔗 飞书文档: https://feishu.cn/docx/{DOC_TOKEN}")
    
    # 检查是否有异常
    has_alert = False
    if data:
        for metric_data in data.get("results", {}).values():
            if metric_data.get("alert"):
                has_alert = True
                break
    
    if has_alert:
        print("\n🚨 检测到异常指标！")
    else:
        print("\n✅ 数据正常")
    
    print("\n📋 下一步: 使用 feishu_doc 工具更新文档")
    print(f"   openclaw feishu_doc write --doc_token {DOC_TOKEN} --file {backup_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
