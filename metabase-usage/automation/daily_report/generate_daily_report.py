#!/usr/bin/env python3
"""
GA 投放数据日报自动生成脚本
每日运行生成飞书云文档报告

使用方式:
  python3 generate_daily_report.py [日期，默认为今天]
  
示例:
  python3 generate_daily_report.py          # 生成今天报告
  python3 generate_daily_report.py 2026-03-05  # 生成指定日期报告
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 配置
WORKSPACE = Path("/Users/imsuansuanru/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
CHARTS_DIR = WORKSPACE / "charts"
REPORTS_DIR = WORKSPACE / "reports"

def get_report_date():
    """获取报告日期（默认为昨天，因为数据通常滞后一天）"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

def load_data(report_date):
    """加载 GA 报告数据"""
    data_file = DATA_DIR / f"ga_report_{report_date}.json"
    if not data_file.exists():
        # 尝试其他命名格式
        data_file = DATA_DIR / f"ga_report_{report_date.replace('-', '')}.json"
    
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def generate_doc_title(report_date):
    """生成文档标题"""
    date_obj = datetime.strptime(report_date, "%Y-%m-%d")
    return f"📊 GA日报 {date_obj.strftime('%Y%m%d')} | 投放数据日报"

def generate_markdown_content(data, report_date):
    """生成报告 Markdown 内容"""
    if not data:
        return f"""# 📊 GA 投放数据日报

**报告日期：** {report_date}

⚠️ 数据文件未找到，请检查数据源。
"""
    
    results = data.get("results", {})
    
    # 提取关键指标
    spend = results.get("推广花费", {})
    reg = results.get("注册用户数", {})
    pay = results.get("累计付费", {})
    ret = results.get("次周留存", {})
    
    def fmt_change(metric):
        """格式化变化百分比"""
        change_pct = metric.get("change_pct", 0)
        arrow = "📈" if metric.get("is_increase") else "📉"
        return f"{arrow} {change_pct:+.1f}%"
    
    def fmt_val(val):
        """格式化数值"""
        if isinstance(val, (int, float)):
            if val >= 1000:
                return f"{val:,.0f}"
            return f"{val:,.2f}" if isinstance(val, float) else str(val)
        return str(val)
    
    return f"""# 📊 GA 投放数据日报

**报告日期：** {report_date}  
**数据截至：** {data.get("date", report_date)}

---

## 📈 核心指标概览

| 指标 | 当前值 | 日环比 | 周同比 | 状态 |
|------|--------|--------|--------|------|
| 推广花费 | ${fmt_val(spend.get("latest_value", 0))} | {fmt_change(spend.get("day_over_day", {{}}))} | {fmt_change(spend.get("week_over_week", {{}}))} | {"🔴 异常" if spend.get("alert") else "🟢 正常"} |
| 注册用户数 | {fmt_val(reg.get("latest_value", 0))} | {fmt_change(reg.get("day_over_day", {{}}))} | {fmt_change(reg.get("week_over_week", {{}}))} | {"🔴 异常" if reg.get("alert") else "🟢 正常"} |
| 累计付费 | ${fmt_val(pay.get("latest_value", 0))} | {fmt_change(pay.get("day_over_week", {{}}))} | {fmt_change(pay.get("week_over_week", {{}}))} | {"🔴 异常" if pay.get("alert") else "🟢 正常"} |
| 次周留存 | {fmt_val(ret.get("latest_value", 0))} | {fmt_change(ret.get("day_over_day", {{}}))} | {fmt_change(ret.get("week_over_week", {{}}))} | {"🔴 异常" if ret.get("alert") else "🟢 正常"} |

---

## ⚠️ 关键洞察

{"**所有核心指标均出现显著下滑**，建议立即排查投放渠道状态、预算是否充足。" if any([spend.get("alert"), reg.get("alert"), pay.get("alert"), ret.get("alert")]) else "**整体数据表现平稳**，继续保持现有投放策略。"}

---

## 📉 注册趋势图

**数据解读：** 查看长期注册趋势变化，识别季节性波动和异常点。

---

## 💰 成本趋势图

**数据解读：** 监控推广成本变化，优化投放效率。

---

## 📊 ROAS趋势图

**数据解读：** 广告支出回报率趋势，评估投放效果。

---

## 💡 综合建议

1. **数据监控**：持续关注核心指标变化趋势
2. **异常处理**：发现异常及时排查原因
3. **优化方向**：基于 ROAS 数据调整投放策略
4. **留存优化**：重点关注次周留存指标

---

*生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 数据来源：GA 投放数据系统*
"""

def main():
    """主函数"""
    report_date = get_report_date()
    print(f"📝 正在生成 {report_date} 的日报...")
    
    # 加载数据
    data = load_data(report_date)
    if data:
        print(f"✅ 已加载数据文件")
    else:
        print(f"⚠️ 未找到 {report_date} 的数据文件，生成空模板")
    
    # 生成内容
    title = generate_doc_title(report_date)
    content = generate_markdown_content(data, report_date)
    
    # 输出信息（实际创建飞书文档需要通过 API）
    print(f"\n📄 文档标题：{title}")
    print(f"📅 报告日期：{report_date}")
    print(f"\n📋 内容预览（前500字符）：")
    print(content[:500] + "...")
    
    # 保存到本地（可选）
    output_file = REPORTS_DIR / f"report_{report_date}.md"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n💾 报告已保存：{output_file}")
    
    return title, content

if __name__ == "__main__":
    main()
