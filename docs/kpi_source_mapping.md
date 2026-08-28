# KPI Source Mapping

| KPI | Formula | Source Table(s) | Source Column(s) | Units | Null/Zero Handling & Special Flags |
|---|---|---|---|---|---|
| NPM | Net Profit / Sales × 100 | profitandloss | net_profit, sales | % | Sales = 0 → None |
| OPM | Operating Profit / Sales × 100 | profitandloss | operating_profit, sales | % | Sales = 0 → None. Cross-check against opm_percentage |
| ROE | Net Profit / (Equity Capital + Reserves) × 100 | profitandloss, balancesheet | net_profit, equity_capital, reserves | % | Equity ≤ 0 → None |
| ROCE | (Operating Profit - Depreciation) / (Equity Capital + Reserves + Borrowings) × 100 | profitandloss, balancesheet | operating_profit, depreciation, equity_capital, reserves, borrowings | % | Bank/NBFC carve-out via sector-relative benchmark |
| D/E | Borrowings / (Equity Capital + Reserves) | balancesheet | borrowings, equity_capital, reserves | Ratio | Equity ≤ 0 handling, 0 = debt-free, non-financials flag > 5 |
| ICR | (Operating Profit + Other Income) / Interest | profitandloss | operating_profit, other_income, interest | Ratio | Interest = 0 → None, display 'Debt Free' logic downstream |
| Asset Turnover | Sales / Total Assets | profitandloss, balancesheet | sales, total_assets | Ratio | Total Assets = 0 → None |
| Revenue CAGR | (Sales_end / Sales_start)^(1/n) - 1 × 100 | profitandloss | sales | % | base=0→ZERO_BASE, base<0 & end>0→TURNAROUND, base<0 & end<0→BOTH_NEGATIVE, base>0 & end<0→DECLINE_TO_LOSS |
| PAT CAGR | (Net_Profit_end / Net_Profit_start)^(1/n) - 1 × 100 | profitandloss | net_profit | % | Same edge cases as above |
| EPS CAGR | (EPS_end / EPS_start)^(1/n) - 1 × 100 | profitandloss | eps | % | Same edge cases as above |
| FCF | Operating Activity + Investing Activity | cashflow | operating_activity, investing_activity | ■ Crore | Negative allowed |
| CFO Quality | Operating Activity / Net Profit | cashflow, profitandloss | operating_activity, net_profit | Ratio | Net Profit = 0 → None |
| CapEx Intensity | abs(Investing Activity) / Sales × 100 | cashflow, profitandloss | investing_activity, sales | % | Sales = 0 → None |
| FCF Conversion | FCF / Operating Profit × 100 | computed, profitandloss | FCF, operating_profit | % | Operating Profit = 0 → None |
| Capital Allocation Pattern | Pattern based on signs of CFO, CFI, CFF | cashflow | operating_activity, investing_activity, financing_activity | String | Deterministic 8 patterns |
