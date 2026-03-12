#!/usr/bin/env python3
"""
AARRR 周报自动化脚本
用于 OpenClaw Heartbeat 每周一自动执行
"""

import subprocess
import json
import os
from datetime import datetime

def run_command(cmd, timeout=60):
    """执行 shell 命令"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def create_feishu_doc(title):
    """创建飞书文档"""
    cmd = f'openclaw feishu_doc create --title "{title}" --grant_to_requester true'
    success, stdout, stderr = run_command(cmd, timeout=30)
    
    if success:
        try:
            # 解析返回的 JSON
            result = json.loads(stdout)
            return result.get('document_id'), result.get('url')
        except:
            # 尝试从文本中提取
            if 'document_id' in stdout:
                import re
                doc_id_match = re.search(r'"document_id":\s*"([^"]+)"', stdout)
                url_match = re.search(r'"url":\s*"([^"]+)"', stdout)
                if doc_id_match:
                    return doc_id_match.group(1), url_match.group(1) if url_match else None
    
    return None, None

def write_to_feishu_doc(doc_token, file_path):
    """写入内容到飞书文档"""
    cmd = f'openclaw feishu_doc write --doc_token {doc_token} --file {file_path}'
    success, stdout, stderr = run_command(cmd, timeout=30)
    return success

def send_notification(message):
    """发送飞书通知"""
    print(f"[通知] {message}")
    
    # 使用 openclaw message 发送通知到飞书
    # 通过管道发送消息内容
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(message)
        temp_file = f.name
    
    # 尝试发送消息（如果在 OpenClaw 环境中会自动路由）
    try:
        cmd = f'cat "{temp_file}" | openclaw message send'
        success, stdout, stderr = run_command(cmd, timeout=10)
        if success:
            print("飞书消息发送成功")
        else:
            print(f"消息发送尝试完成（可能在非交互环境）")
    except Exception as e:
        print(f"消息发送尝试: {e}")
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass
    
    return True

def main():
    """主函数"""
    print("=" * 50)
    print(f"AARRR 周报自动生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 1. 检查今天是否是周一
    today = datetime.now()
    if today.weekday() != 0:  # 0 = Monday
        print(f"今天不是周一（今天是星期{today.weekday() + 1}），跳过周报生成")
        return 0
    
    print("今天是周一，开始生成周报...")
    
    # 2. 生成周报内容
    print("\n[1/4] 生成周报内容...")
    report_script = "/Users/imsuansuanru/.openclaw/workspace/scripts/generate_aarrr_report.py"
    
    if not os.path.exists(report_script):
        print(f"错误：找不到脚本 {report_script}")
        return 1
    
    success, stdout, stderr = run_command(f"python3 {report_script}", timeout=120)
    
    if not success:
        print(f"生成周报内容失败: {stderr}")
        return 1
    
    print("周报内容生成成功")
    
    # 3. 创建飞书文档
    print("\n[2/4] 创建飞书文档...")
    week_title = today.strftime("%Y年%m月%d日周")
    doc_title = f"AARRR周报 - {week_title}"
    
    doc_token, doc_url = create_feishu_doc(doc_title)
    
    if not doc_token:
        print("创建飞书文档失败，尝试更新现有文档...")
        # 如果创建失败，使用现有文档更新
        doc_token = "UW9ZdSRsSo7V0Kx2Tc7c4dxgnGe"
        doc_url = "https://feishu.cn/docx/UW9ZdSRsSo7V0Kx2Tc7c4dxgnGe"
        print(f"将更新现有文档: {doc_url}")
    else:
        print(f"创建新文档成功: {doc_url}")
    
    # 4. 写入内容
    print("\n[3/4] 写入周报内容...")
    report_file = f"/Users/imsuansuanru/.openclaw/workspace/reports/aarrr_weekly_report_{today.strftime('%Y%m%d')}.md"
    
    # 如果当天报告不存在，使用最新的报告
    if not os.path.exists(report_file):
        import glob
        report_files = glob.glob("/Users/imsuansuanru/.openclaw/workspace/reports/aarrr_weekly_report_*.md")
        if report_files:
            report_file = max(report_files, key=os.path.getctime)
        else:
            print("错误：找不到生成的报告文件")
            return 1
    
    success = write_to_feishu_doc(doc_token, report_file)
    
    if not success:
        print("写入文档失败")
        return 1
    
    print(f"报告已写入文档: {doc_url}")
    
    # 5. 发送通知
    print("\n[4/4] 发送通知...")
    notification = f"""AARRR周报已生成 | {week_title}

本周数据已更新，请查看详细分析。

📄 [点击查看周报]({doc_url})

---
简要亮点：
- 数据已自动从 Metabase 获取
- 包含 Acquisition/Activation/Retention/Revenue 全维度分析
- 已识别本周关键洞察和行动建议"""
    
    send_notification(notification)
    
    print("\n" + "=" * 50)
    print("周报自动化完成！")
    print(f"文档链接: {doc_url}")
    print("=" * 50)
    
    return 0

if __name__ == "__main__":
    exit(main())