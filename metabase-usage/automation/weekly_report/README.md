# AARRR 周报自动化

基于 Metabase 数据的 AARRR 周报自动生成。

## 脚本说明

| 文件 | 功能 |
|------|------|
| `generate_aarrr_report.py` | 从 Metabase 获取数据，生成周报 |
| `weekly_auto_run.py` | 完整自动化流程 |

## 依赖

- Metabase API (数据源)
- 飞书 API (可选，用于推送)

## 配置

在 `docs/datasource/DATA_SOURCES.md` 中配置 Question ID。
