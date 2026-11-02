import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    NAVY = RGBColor(15, 23, 42)
    BLUE_ACCENT = RGBColor(14, 116, 144)
    GOLD = RGBColor(217, 119, 6)
    WHITE = RGBColor(255, 255, 255)
    LIGHT_BG = RGBColor(248, 250, 252)
    CARD_BG = RGBColor(255, 255, 255)
    DARK_TEXT = RGBColor(15, 23, 42)
    MUTED_TEXT = RGBColor(100, 116, 139)
    BORDER_COLOR = RGBColor(226, 232, 240)

    def set_slide_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = LIGHT_BG
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text='NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM'):
        top_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(1.1))
        top_shape.fill.solid()
        top_shape.fill.fore_color.rgb = NAVY
        top_shape.line.fill.background()
        
        tf = top_shape.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.8)
        tf.margin_top = Inches(0.18)
        
        p0 = tf.paragraphs[0]
        p0.text = category_text.upper()
        p0.font.size = Pt(10)
        p0.font.bold = True
        p0.font.color.rgb = GOLD
        
        p1 = tf.add_paragraph()
        p1.text = title_text
        p1.font.size = Pt(22)
        p1.font.bold = True
        p1.font.color.rgb = WHITE

    def add_card(slide, left, top, width, height, title, items, badge=''):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = BORDER_COLOR
        card.line.width = Pt(1.5)
        
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.35)
        tf.margin_right = Inches(0.35)
        tf.margin_top = Inches(0.25)
        tf.margin_bottom = Inches(0.25)
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = NAVY
        
        if badge:
            pb = tf.add_paragraph()
            pb.text = badge.upper()
            pb.font.size = Pt(9)
            pb.font.bold = True
            pb.font.color.rgb = BLUE_ACCENT
            pb.space_before = Pt(2)
            pb.space_after = Pt(8)
        else:
            p.space_after = Pt(8)
            
        for item in items:
            p_item = tf.add_paragraph()
            p_item.text = f"•  {item}"
            p_item.font.size = Pt(12)
            p_item.font.color.rgb = DARK_TEXT
            p_item.space_before = Pt(4)

    blank_layout = prs.slide_layouts[6]

    # Slide 1: Cover
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY
    bg1.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.333), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = 'NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM'
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = WHITE

    p = tf.add_paragraph()
    p.text = 'Automated Fundamental Analysis, Cash Flow Intelligence, Clustering & Enterprise Reporting Engine'
    p.font.size = Pt(18)
    p.font.color.rgb = GOLD
    p.space_before = Pt(12)

    p = tf.add_paragraph()
    p.text = 'A scalable, institutional-grade equity research infrastructure for 92 Nifty 100 constituent corporations'
    p.font.size = Pt(14)
    p.font.color.rgb = LIGHT_BG
    p.space_before = Pt(8)

    p = tf.add_paragraph()
    p.text = 'Author: Shaikh Raheem  |  Track: Financial Systems & Quantitative Engineering  |  Bluestock Fintech Internship'
    p.font.size = Pt(13)
    p.font.color.rgb = MUTED_TEXT
    p.space_before = Pt(36)

    # Slide 2: Executive Summary
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s2)
    add_header(s2, 'Executive Summary: Mission & Problem Statement')
    add_card(s2, 0.8, 1.4, 5.6, 5.5, 'The Industry Challenge', [
        'Fundamental analysis across 100+ public equities is traditionally manual, siloed, and prone to accounting anomalies.',
        'Analysing 10-year audited disclosures requires standardising non-uniform line items across 11 diverse sectors.',
        'Institutional teams lack automated capital allocation pattern recognition and programmatic tearsheet generation.',
        'Disparate data models make cross-sectional screening and ML clustering cumbersome and time-consuming.',
        'Need: An automated, resilient pipeline from raw financial filings to interactive dashboards, REST APIs, and publication-ready PDF reports.'
    ], badge='Problem Statement')

    add_card(s2, 6.9, 1.4, 5.6, 5.5, 'The Intelligence Platform Solution', [
        'Complete Ingestion: Clean SQLite database storing 10 normalised financial statement tables across 92 companies over 10+ fiscal years.',
        'Comprehensive Ratio Engine: 1,155 company-years computed across 14 solvency, profitability, valuation, and liquidity KPIs.',
        'Cash Flow Intelligence: Mathematical classification of 8 capital allocation sign patterns and CFO quality distress triggers.',
        'Unsupervised ML Archetypes: 5 KMeans clusters classifying the investment universe into data-driven behavioural cohorts.',
        'Multi-Channel Distribution: 92 automated tearsheets, 8-page Streamlit portal, and 16-endpoint FastAPI REST backend.'
    ], badge='Core Value Proposition')

    # Slide 3: System Architecture
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s3)
    add_header(s3, 'System Architecture & Enterprise Technology Stack')
    add_card(s3, 0.8, 1.4, 3.6, 5.5, 'Data & Persistence Layer', [
        'SQLite 3 RDBMS with enforced foreign key integrity (PRAGMA foreign_keys = ON).',
        '10 Normalized Tables: companies, pnl, balance_sheet, cash_flow, ratios, capital allocation, peer rankings, clusters.',
        'Automated ETL Loader: Multi-sheet Excel parser with type coercion, null reconciliation, and deduplication.',
        'Zero Schema Drift: Strictly typed schemas with automated validation failure auditing (223 KB audit trail).'
    ], badge='Database & ETL')

    add_card(s3, 4.85, 1.4, 3.6, 5.5, 'Analytics & ML Core', [
        'NumPy & Pandas: Vectorized financial ratio calculation and multi-year CAGR compounding.',
        'Scikit-Learn: StandardScaler normalisation and KMeans clustering (k=5, random_state=42).',
        'NLP Regex Engine: Automated text parsing of disclosure notes with pattern divergence cross-validation.',
        'Pros/Cons Rule Engine: 24 rules (12 pros, 12 cons) generating automated thesis commentary with confidence scoring.'
    ], badge='Quantitative Engine')

    add_card(s3, 8.9, 1.4, 3.6, 5.5, 'Interface & Reporting', [
        'FastAPI Backend: High-performance asynchronous API serving 16 endpoints with Swagger UI & OpenAPI 3.0 spec.',
        'Streamlit Dashboard: 8-page interactive portal featuring dynamic screener, peer radar charts, and PDF viewer.',
        'ReportLab PDF Engine: 92 institutional 2-page tearsheets, 11 sector dossiers, and portfolio master report.',
        'Pytest Test Suite: 119 comprehensive unit & integration tests achieving 100% pass rate.'
    ], badge='Delivery & Interfaces')

    # Slide 4: Data Quality & KPI Engine
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s4)
    add_header(s4, 'Data Quality, Normalisation & KPI Engine (Sprints 1 & 2)')
    add_card(s4, 0.8, 1.4, 5.6, 5.5, 'Rigorous Data Quality Governance', [
        '92 Large-Cap Equities: Fully verified company registry covering 11 broad sectors and 23 sub-sectors.',
        '10+ Year Depth: Over 90% of companies possess complete 10-year P&L, Balance Sheet, and Cash Flow history.',
        'Strict Accounting Identities: Total Assets = Total Liabilities checked across 1,184 balance sheet filings.',
        'Audit Trail Logging: load_audit.csv tracks ingestion batch records; validation_failures.csv captures accounting anomalies with zero silent drops.',
        'Foreign Key Integrity: PRAGMA foreign_key_check returns 0 errors across all relational dependencies.'
    ], badge='Data Governance')

    add_card(s4, 6.9, 1.4, 5.6, 5.5, 'The 14-KPI Financial Ratio Engine', [
        '1,155 Company-Years: Standardized metrics computed without cross-year lookahead bias.',
        'Solvency & Risk: Debt-to-Equity, Net Debt/EBITDA, Interest Coverage Ratio (ICR).',
        'Profitability & Returns: Operating Profit Margin (OPM), Net Margin, ROE, ROCE, and ROIC.',
        'Cash Quality & Efficiency: Free Cash Flow (CFO - CapEx), CFO/PAT ratio, Asset Turnover, Working Capital Days.',
        'Valuation & Growth: Historical P/E, P/B, EV/EBITDA, and 3/5/10-year compound revenue/profit CAGRs.'
    ], badge='Quantitative Metrics')

    # Slide 5: Cash Flow Intelligence
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s5)
    add_header(s5, 'Cash Flow Intelligence & Capital Allocation Patterns (Sprints 3 & 5)')
    add_card(s5, 0.8, 1.4, 5.6, 5.5, '8 Mathematical Cash Flow Patterns', [
        'Sign Classification: Dynamic mapping of (+/-) signs across CFO, CFI, and CFF over all historical periods.',
        'Pattern 1 (+, -, -): Organic Compounder - CFO covers all investments and returns capital to shareholders.',
        'Pattern 2 (+, -, +): Debt/Equity Funded Growth - aggressive CapEx funded by external financing and cash flow.',
        'Pattern 4 (-, -, +): Early Stage / Stressed Expansion - negative operating cash flow requiring capital injections.',
        'Pattern 7 (+, +, -): Asset Divestiture / Deleveraging - proceeds from asset sales used to pay down leverage.',
        'Historical Migration Tracking: Identifies inflection years where capital allocation strategies fundamentally pivoted.'
    ], badge='Capital Allocation Matrix')

    add_card(s5, 6.9, 1.4, 5.6, 5.5, 'CFO Quality & Early Warning Indicators', [
        'Cash Conversion Quality: Flags divergence between accounting net profit (PAT) and real operating cash (CFO/PAT < 0.8).',
        'CapEx Intensity Profiling: Segregates Maintenance CapEx from Expansionary CapEx across cyclical and asset-light sectors.',
        'FCF Yield & Burn Monitoring: Real-time detection of sustained negative FCF runs across high-growth candidates.',
        'Financial Distress Triggers: Triple-check alarm firing when ICR < 1.5, D/E > 2.5 (non-financials), and negative CFO coincide.',
        'Outputs Generated: Comprehensive cashflow_intelligence.xlsx and distress_alerts.csv.'
    ], badge='Risk Surveillance')

    # Slide 6: KMeans Clustering
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s6)
    add_header(s6, 'Machine Learning Archetypes: KMeans Clustering (Sprint 6)')
    add_card(s6, 0.8, 1.4, 5.6, 5.5, 'Clustering Methodology & Validation', [
        '5 Dimensional Feature Space: ROE (%), Debt-to-Equity, 5-Year Revenue CAGR, 5-Year FCF CAGR, and Operating Profit Margin (%).',
        'Sector Median Imputation: Handles structural reporting differences before model training.',
        'StandardScaler Normalisation: Ensures zero mean and unit variance across all metrics to eliminate feature scale dominance.',
        'Elbow Method Verification: Inertia curve tested from k=2 to k=10; confirmed optimal inflection at k=5 (elbow_plot.png).',
        'Centroid Distance Metrics: Quantifies how archetypal or atypical each company is within its respective cluster.'
    ], badge='Unsupervised ML')

    add_card(s6, 6.9, 1.4, 5.6, 5.5, 'The 5 Discovered Market Archetypes', [
        'Cluster 0: High-Quality Compounders - High ROE (>22%), robust FCF, low debt, premium pricing power (e.g. TCS, Titan).',
        'Cluster 1: Defensive Dividend Payers - Moderate growth, low leverage, strong cash yields (e.g. ITC, FMCG majors).',
        'Cluster 2: Capital-Intensive Growth - High CapEx, moderate debt, expanding asset base (e.g. Infrastructure, Telecom).',
        'Cluster 3: Value Cyclicals - Commodity/heavy manufacturing with cyclical margin fluctuations (e.g. Metals, Auto).',
        'Cluster 4: Turnaround / Highly Leveraged - High D/E, depressed ROE, negative FCF requiring restructuring.',
        'Cluster Deliverable: Fully annotated cluster_labels.csv and portfolio_stats.csv.'
    ], badge='Investor Cohorts')

    # Slide 7: NLP & Pros/Cons Engine
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s7)
    add_header(s7, 'NLP Text Parsing & 24 Automated Pros/Cons Rules (Sprint 5)')
    add_card(s7, 0.8, 1.4, 5.6, 5.5, 'Automated Disclosure Parser', [
        'Regex Engine: Scans unstructured analysis commentary to extract historical compounded CAGR metrics.',
        'Target Metrics: Compounded Sales Growth, Compounded Profit Growth, Stock Price CAGR, and Return on Equity.',
        'Pattern Matching: Robust regex handles variable year spans and percentage formatting (e.g. 10 Years: 21%).',
        'Cross-Validation Guardrail: Reconciles parsed disclosure CAGRs against internally computed ratio engine numbers; flags discrepancies >5%.',
        'Outputs: analysis_parsed.csv and parse_failures.csv.'
    ], badge='Regex Parser')

    add_card(s7, 6.9, 1.4, 5.6, 5.5, 'The 24-Rule Automated Thesis Engine', [
        '12 Pro Rules: Recognizes sustained ROE >20%, debt-free balance sheets, FCF positive for 5+ years, margin expansion, and high ICR.',
        '12 Con Rules: Flags elevated leverage (D/E > 2.0), persistent negative FCF, promoter pledge stress, CFO/PAT divergence, and margin decay.',
        'Confidence Scoring: Each insight receives an algorithmically calibrated confidence score (60% to 95%).',
        'Universal Coverage: 100% of the 92 companies received at least 1 validated Pro and 1 Con.',
        'Generated Output: 62 KB database in pros_cons_generated.csv.'
    ], badge='Rule Engine')

    # Slide 8: Enterprise Reporting Infrastructure
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s8)
    add_header(s8, 'Institutional PDF Generation & Visual Reporting (Sprints 4 & 5)')
    add_card(s8, 0.8, 1.4, 5.6, 5.5, '92 Two-Page Company Tearsheets', [
        'ReportLab Vector Canvas: Institutional equity research layout designed to international sell-side standards.',
        'Page 1 Architecture: Corporate identity, latest price/valuation, 10-year P&L / BS / Cash Flow summary tables, and solvency ratios.',
        'Page 2 Architecture: 5-axis Peer Radar Chart, historical Free Cash Flow trend charts, automated Pros/Cons commentary, and cluster classification.',
        '100% Automated Batch Execution: Generated all 92 tearsheets in 17.8 seconds with zero text overflow or layout overlap errors.',
        'Deliverable Path: reports/tearsheets/*.pdf (each 50 KB - 150 KB).'
    ], badge='Company Tearsheets')

    add_card(s8, 6.9, 1.4, 5.6, 5.5, 'Sector Dossiers & Portfolio Master Book', [
        '11 Sector Comparative Books: Comprehensive deep-dives across IT, Banking, FMCG, Pharma, Auto, Energy, Metals, etc.',
        'Sector Aggregates: Median ROE, average leverage, median margin, and top quartile valuation benchmarks.',
        'Portfolio Master Summary: Single consolidated 92-page PDF publication (reports/portfolio/portfolio_summary.pdf).',
        'Peer Comparison Matrix: 11-sheet multi-tab Excel workbook with percentile color formatting across 20 KPIs (peer_comparison.xlsx).',
        'Visual Artifacts: 92 custom radar charts, correlation heatmaps, and KMeans elbow curves.'
    ], badge='Sector & Portfolio Books')

    # Slide 9: User Interfaces & REST API
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s9)
    add_header(s9, 'User Interfaces: Streamlit Dashboard & FastAPI Backend (Sprints 4 & 6)')
    add_card(s9, 0.8, 1.4, 5.6, 5.5, '8-Page Streamlit Financial Portal', [
        'Home / Overview: Market-wide telemetry, sector breakdown, and macro portfolio statistics.',
        'Stock Screener: Multi-parameter filtering with 6 pre-built institutional presets (Compounders, Value, Dividend, etc.).',
        'Peer Analysis: Cross-sectional comparisons, 5-metric radar charts, and ranking percentiles.',
        'Valuation & DCF Workbench: Historical multiples, EV/EBITDA bands, and discount-to-historical analysis.',
        'Cash Flow & Capital Allocation: Visual waterfall charts, 8 sign patterns, and distress flags.',
        'Cluster Explorer: Interactive 2D PCA projection of the 5 KMeans archetypes.',
        'Tearsheet Viewer & DQ Audit: Instant PDF preview and data quality error log inspector.'
    ], badge='Streamlit UI')

    add_card(s9, 6.9, 1.4, 5.6, 5.5, 'FastAPI Enterprise REST Suite (16 Endpoints)', [
        'High-Throughput Asynchronous Server: FastAPI running on Uvicorn with CORS middleware and latency logging.',
        'Core Endpoint Groups: Companies, Screener, Peers, Valuation, Cash Flow, Clustering, and Health Check.',
        'Documentation & Standards: Automatic OpenAPI 3.0 schema generation (docs/openapi.json) and Postman collection (docs/postman_collection.json).',
        'Health Monitoring: /api/v1/health returning live table row counts, uptime, and database integrity status.',
        'Sub-30ms Response Latency: Highly optimized SQL queries with parameterized statement caching.'
    ], badge='FastAPI Backend')

    # Slide 10: Quality Assurance & Sign-Off
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s10)
    add_header(s10, 'Quality Assurance, Verification & Project Sign-Off (Sprint 6)')
    add_card(s10, 0.8, 1.4, 5.6, 5.5, '100% Green Automated Test Suite', [
        '119 Comprehensive Tests: 0 failures, 0 errors, 100% passing across all functional domains.',
        'Test Domain Breakdown:',
        '  - Database & ETL Loader: 28 tests (schema, foreign keys, row counts)',
        '  - Financial Ratio Engine: 23 tests (solvency, CAGR, zero divisions)',
        '  - Screener & Valuation: 17 tests (filters, scoring, boundary cases)',
        '  - Cash Flow Intelligence: 14 tests (sign patterns, CFO quality)',
        '  - Machine Learning: 11 tests (KMeans k=5, scaling, imputation)',
        '  - REST API: 16 tests (all endpoints, status 200, schema validation)',
        '  - Report Generation: 10 tests (PDF formatting, radar charts)',
        'Execution Time: 35.5 seconds (reports/pytest_report.html).'
    ], badge='Test Suite')

    add_card(s10, 6.9, 1.4, 5.6, 5.5, 'Formal 20-Gate Acceptance Verification', [
        'All 20 Non-Negotiable Acceptance Gates Verified & Passed (AC-01 through AC-20).',
        'Key Milestones Verified:',
        '  - Exactly 92 companies ingested; 1,155 ratio years computed.',
        '  - PRAGMA foreign_key_check returns 0 errors.',
        '  - 92/92 company tearsheets generated without text overflow.',
        '  - Screener presets successfully populate 38 Quality Compounders.',
        '  - All 16 FastAPI endpoints live and verified via automated tests.',
        'Signed Documentation Delivered:',
        '  - 12-Page Analyst & Architecture Guide (docs/analyst_guide.pdf)',
        '  - Formal Acceptance Sign-Off Certificate (docs/acceptance_checklist.pdf)'
    ], badge='Project Sign-Off')

    out_path = r'C:\Users\shaikh raheem\OneDrive\Desktop\N100 FINANCIAL INTELLIGENCE PLATFORM\nifty100_platform\docs\Nifty100_Presentation_Deck.pptx'
    prs.save(out_path)
    print(f'Successfully generated {out_path}')

if __name__ == '__main__':
    build_presentation()
