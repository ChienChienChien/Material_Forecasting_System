[繁體中文](architecture.md) | **English**

# Raw Material Inventory Forecasting | System Architecture

## End-to-End Architecture

```mermaid
flowchart TB
    subgraph Sources[Operational Data]
        A["MES: inventory, receipts, consumption, restrictions"]
        B["Procurement: purchase orders and inbound schedules"]
        C["BOM platform: material requirements"]
        D["Planning: weekly and monthly production plans"]
    end

    E["SQL extraction and source alignment"]
    F["Python processing: cleansing, material and date mapping"]
    G["Forecast engine: receipts, consumption, daily balances"]
    H["Forecast database: material-by-day results"]
    I["Power BI: trends, alerts, and daily detail"]
    J["Power Automate and Teams: tiered notifications"]

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

## Component Responsibilities

| Component | Responsibility |
|---|---|
| MES data | Provides on-hand inventory, receipts, actual consumption, and restricted stock |
| Procurement data | Provides purchase orders, expected delivery dates, and inbound arrangements |
| BOM platform | Converts production requirements into material demand |
| Production planning | Provides near-term schedules and medium-term weekly or monthly plans |
| SQL extraction | Retrieves source data and aligns identifiers across systems |
| Python processing | Cleanses fields and maps all records to material and date dimensions |
| Forecast engine | Calculates expected receipts, consumption, and daily inventory balances |
| Forecast database | Stores material-by-day results for reporting and alerting |
| Power BI and Teams | Presents risk and distributes tiered notifications |

## Forecasting Flow

```mermaid
stateDiagram-v2
    state "Load Current Inventory" as Inventory
    state "Add Expected Receipts" as Receipts
    state "Estimate Consumption" as Consumption
    state "Calculate Daily Balance" as Balance
    state "Evaluate Thresholds" as Risk
    state "Publish and Alert" as Publish

    [*] --> Inventory
    Inventory --> Receipts
    Receipts --> Consumption
    Consumption --> Balance
    Balance --> Risk
    Risk --> Publish
    Publish --> [*]
```

## Forecast Horizon

| Period | Primary demand input |
|---|---|
| Next week | BOM and actual production schedule |
| Remainder of current month | BOM, weekly production plan, and working days |
| Following months | BOM, monthly production plan, and working days |

This design combines detailed near-term scheduling with broader medium-term planning. All inputs are converted to a daily material-level time series before inventory balances are calculated.

## Decision Flow

```mermaid
flowchart LR
    A["Daily forecast"] --> B["Safety and shortage thresholds"]
    B --> C["Risk level and expected date"]
    C --> D["Power BI risk list"]
    C --> E["Teams alert"]
```

- Trend views show when projected inventory approaches a threshold.
- Alert lists prioritize materials by risk level and expected shortage date.
- Daily detail supports follow-up on receipts, consumption, and balance changes.

## Diagram Notes

- Solid arrows indicate the primary data and decision flow.
- Source and field names are de-identified.
- Proprietary planning parameters and complete calculation rules are excluded.
