# Scripts

This folder contains a simplified and sanitized version of the production pipeline structure.

The code is provided for portfolio review only. It illustrates how the project was organized into configuration, data extraction, forecasting logic, and output steps.

Because the production version depends on internal databases, private libraries, scheduled jobs, and notification services, this public version is not designed to be executed directly.

## Module Overview

| File | Purpose |
|---|---|
| `config.py` | 管理環境設定與資料庫連線設定。 |
| `data.py` | 負責來源資料擷取、清理與整理，包含庫存、採購與耗用資料。 |
| `model.py` | 建立每日進耗存推移邏輯，計算未來每日庫存與風險狀態。 |
| `main.py` | Pipeline 入口，串接資料載入、模型計算與結果輸出。 |
| `utils.py` | 放置共用工具函式。 |