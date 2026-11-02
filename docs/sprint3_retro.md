# Sprint 3 Retrospective - Screener & Peer Engine

## Sprint Objective
Build a configurable financial screener with 6 official presets, custom thresholds, composite quality score, and sector-relative ranking. In addition, develop a peer engine for percentile ranking across 11 peer groups, generating 92 radar charts and Excel reporting (`screener_output.xlsx` and `peer_comparison.xlsx`).

## Execution Results

### D15 Result: Screener Core
- **PASS**: Configurable `ScreenerEngine` established. Custom filtering supports all 15 specified metrics. Financials are correctly carved out of `de_max` filters. ICR handles debt-free nulls dynamically.

### D16 Result: Six Presets
- **PASS**: Quality, Value, Growth, Dividend, Momentum, and Debt-Free presets implemented and mapped in `config/screener_config.yaml`. Result ranges vary (2 to 38) indicating realistic index composition filtering rather than artificial target-forcing.

### D17 Result: Composite Score + Excel
- **PASS**: 0-100 composite score implemented using 50% Profitability, 30% Growth, and 20% Valuation metrics. P10/P90 winsorization successfully handles extreme outliers. Sector-relative ranks and percentiles generated in the 6-sheet `screener_output.xlsx` with conditional formatting.

### D18 Result: Peer Engine
- **PASS**: 11 peer groups loaded from `peer_groups.xlsx`. Computed `PERCENT_RANK` exactly matching SQL semantics (using min/max tiebreakers appropriately). `D/E` inversely ranked properly. Unassigned companies safely omitted. SQLite table `peer_percentiles` populated accurately. 

### D19 Result: Radar Charts
- **PASS**: Generated 92 PNG radar charts under `reports/radar_charts/`. Each features an 8-axis comparative polygon against a dashed peer-average overlay. 'No peer group assigned' fallbacks clearly labelled.

### D20 Result: Peer Workbook
- **PASS**: `peer_comparison.xlsx` created with exactly 11 sheets. Automatically applies quartile conditional formatting (Green >= 75th, Yellow 25th-75th, Red <= 25th). Includes `best_in_class` and `watch_list` columns based on multi-metric quartile thresholds.

### D21 Result: QA and Tests
- **PASS**: Added `tests/screener/test_engine.py` and `tests/analytics/test_peer.py`. The full suite (36 tests) across Sprint 1, Sprint 2, and Sprint 3 passed. Idempotency verified through pipeline re-execution.

---

## Metrics & Coverage

- **Companies Screened**: 92
- **Preset Results**: Quality (38), Value (2), Growth (19), Dividend (30), Momentum (31), Debt-Free (2)
- **Composite Score**: Min = 7.43, Max = 73.22, Average = 42.36
- **Peer Groups**: 11
- **Peer Percentile Rows**: 56 companies * 10 metrics = 560
- **Best-in-Class**: 9
- **Watch List**: 10
- **Radar Charts**: 92 / 92
- **Excel Output**: `screener_output.xlsx` (6 sheets), `peer_comparison.xlsx` (11 sheets)

---

## Known Issues
- `Value` and `Debt-Free` presets yielded lower counts (2 each) than the target "5 to 50" requested in the detailed schedule. Per requirements, thresholds were NOT manipulated to artificially increase the counts. The results reflect the actual Nifty 100 fundamentals as of the latest year against the strict Value and Debt-Free definitions.

## Specification Ambiguities
- **Filter Count Discrepancy**: The spec mentioned 18 platform filters, but the detailed Sprint 3 deliverable explicitly defined 15. The 15 defined thresholds were implemented to prevent inventing unspecified logic.
- **Sprint Scope**: Overview described Sprint 3 as "Screener + Score + Sector Analytics", but detailed D15-D21 explicitly requested "Screener + Peer Comparison". Implementation followed the detailed D15-D21 schedule.
- **Composite Score Weighting**: Two conflicting structures were presented (35/30/20/15 vs 50/30/20). The implementation strictly followed the bolded "IMPORTANT: Use the project's specified composite-score model... 50% Profitability, 30% Growth, 20% Valuation" directive.
- **Benchmark Company Determination**: The spec lacked a purely deterministic rule to highlight the benchmark row. A deterministic fallback was chosen for visual overlay in charts, but without an explicit definition, explicit highlighting of a single arbitrary row in Excel was treated as a secondary UI concern compared to robust peer medians.

## Sprint 4 Readiness
- **YES**. The Screener and Peer Engine layer is finalized, tested, and idempotent. Ready for Sprint 4.
