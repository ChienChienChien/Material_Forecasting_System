**繁體中文** | [English](architecture_en.md)

# 原料進耗存預測與庫存告警系統｜系統架構

## 整體架構

```mermaid
flowchart TB
    subgraph Sources[營運資料來源]
        A["MES：庫存、進貨、耗用、管制庫存"]
        B["採購系統：採購單與進貨安排"]
        C["BOM 平台：原料需求"]
        D["生產規劃：週計畫與月計畫"]
    end

    E["SQL 資料擷取與來源對應"]
    F["Python 資料處理：清理、原料與日期對應"]
    G["預測引擎：進貨、耗用、每日庫存"]
    H["預測資料庫：原料日別結果"]
    I["Power BI：趨勢、告警與日別明細"]
    J["Power Automate／Teams：分級通知"]

    A --> E
    B --> E
    C --> E
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
```

## 各層職責

| 元件 | 主要職責 |
|---|---|
| MES 資料 | 提供現有庫存、進貨、實際耗用及管制庫存 |
| 採購資料 | 提供採購單、預計交期與進貨安排 |
| BOM 平台 | 將生產需求轉換為各項原料需求 |
| 生產規劃 | 提供近期排程及中期週、月生產計畫 |
| SQL 資料擷取 | 讀取來源資料並對應跨系統識別欄位 |
| Python 資料處理 | 清理欄位，將資料統一至原料與日期維度 |
| 預測引擎 | 計算預計進貨、耗用及每日庫存餘額 |
| 預測資料庫 | 保存原料日別結果，供報表與告警使用 |
| Power BI／Teams | 呈現庫存風險並推送分級通知 |

## 預測流程

```mermaid
stateDiagram-v2
    state "載入目前庫存" as Inventory
    state "加入預計進貨" as Receipts
    state "推估原料耗用" as Consumption
    state "計算每日庫存" as Balance
    state "判斷風險門檻" as Risk
    state "發布報表與告警" as Publish

    [*] --> Inventory
    Inventory --> Receipts
    Receipts --> Consumption
    Consumption --> Balance
    Balance --> Risk
    Risk --> Publish
    Publish --> [*]
```

## 預測期間與資料依據

| 預測期間 | 主要耗用依據 |
|---|---|
| 近一週 | BOM 與實際生產排程 |
| 當月後續期間 | BOM、週生產計畫及工作天數 |
| 次月起 | BOM、月生產計畫及工作天數 |

此設計以近期排程提高短期預測精度，並以週、月計畫支援中期規劃。所有資料在計算前皆轉換為原料日別時間序列。

## 告警決策流程

```mermaid
flowchart LR
    A["每日庫存預測"] --> B["安全水位與缺料門檻"]
    B --> C["風險等級與預計日期"]
    C --> D["Power BI 風險清單"]
    C --> E["Teams 告警"]
```

- 趨勢圖呈現預估庫存接近警戒水位的時間點。
- 告警清單依風險等級及預計缺料日期排序。
- 日別明細提供進貨、耗用與庫存變化的追查依據。

## 圖示說明

- 實線箭頭代表主要資料與決策流程。
- 資料來源及欄位名稱均已去識別化。
- 未揭露公司專用規劃參數及完整計算規則。
