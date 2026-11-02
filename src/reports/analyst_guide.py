import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from pypdf import PdfReader

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#718096'))
        
        # Suppress headers/footers on cover page
        if self._pageNumber > 1:
            # Header
            self.drawString(36, A4[1] - 28, "Nifty 100 Financial Intelligence Platform — Analyst User Guide & Technical Manual")
            self.drawRightString(A4[0] - 36, A4[1] - 28, "CONFIDENTIAL · INTERNAL USE ONLY")
            self.setStrokeColor(colors.HexColor('#E2E8F0'))
            self.setLineWidth(0.6)
            self.line(36, A4[1] - 34, A4[0] - 36, A4[1] - 34)
            
            # Footer
            self.setStrokeColor(colors.HexColor('#E2E8F0'))
            self.setLineWidth(0.6)
            self.line(36, 34, A4[0] - 36, 34)
            self.drawString(36, 22, "Data Analytics Division  |  Version 1.0  |  Project ID: DAD-PROJ-001")
            self.drawRightString(A4[0] - 36, 22, f"Page {self._pageNumber} of {page_count}")
            
        self.restoreState()


def build_analyst_guide(output_pdf_path: str) -> int:
    """Generates the official 10+ page Analyst Guide PDF using ReportLab."""
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=colors.HexColor('#1A365D'),
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4A5568'),
        alignment=0
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#2B6CB0'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    table_header = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_body = ParagraphStyle(
        'TB',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#2D3748')
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#2D3748')
    )

    story = []

    # =========================================================================
    # PAGE 1: COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("DATA ANALYTICS DIVISION · INTERNAL TECHNICAL PUBLICATION", ParagraphStyle('TopTag', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#718096'), leading=12)))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Nifty 100 Financial<br/>Intelligence Platform", title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Comprehensive Analyst User Guide & System Architecture Specification</b>", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor('#2B6CB0'), spaceBefore=5, spaceAfter=25))
    
    meta_data = [
        [Paragraph("<b>Document Identifier:</b>", table_body), Paragraph("DAD-PROJ-001-UG (Version 1.0)", table_body)],
        [Paragraph("<b>Security Classification:</b>", table_body), Paragraph("CONFIDENTIAL — Internal Use Only", table_body)],
        [Paragraph("<b>Effective Date:</b>", table_body), Paragraph("November 2026", table_body)],
        [Paragraph("<b>Target Audience:</b>", table_body), Paragraph("Equity Research Analysts, Portfolio Managers, Risk Auditors", table_body)],
        [Paragraph("<b>Coverage Universe:</b>", table_body), Paragraph("92 Nifty 100 Index Constituents (10–14 Year Historical Time Series)", table_body)],
        [Paragraph("<b>Primary Engine Modules:</b>", table_body), Paragraph("ETL Lake, 50+ KPI Engine, 6 Screeners, ML Clustering, FastAPI, Streamlit", table_body)],
        [Paragraph("<b>Technical Platform:</b>", table_body), Paragraph("Python 3.10, SQLite 3, FastAPI, Streamlit, Plotly, ReportLab", table_body)],
    ]
    t_meta = Table(meta_data, colWidths=[150, 370])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 35))
    
    exec_notice = (
        "<b>Executive Notice:</b> This technical manual serves as the standard operating reference for the "
        "Nifty 100 Financial Intelligence Platform. All data transformations, financial ratios, valuation indicators, "
        "and machine learning clustering models described herein adhere strictly to reproducible quantitative accounting standards. "
        "Unauthorized redistribution is strictly prohibited."
    )
    story.append(Paragraph(exec_notice, body_style))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: TABLE OF CONTENTS & ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("1. Table of Contents & System Architecture", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    
    toc_data = [
        [Paragraph("<b>Section 1</b>", table_body), Paragraph("Table of Contents & System Architecture Overview", table_body), Paragraph("Page 2", table_body)],
        [Paragraph("<b>Section 2</b>", table_body), Paragraph("Dataset Catalogue & Master Entity Data Model", table_body), Paragraph("Page 3", table_body)],
        [Paragraph("<b>Section 3</b>", table_body), Paragraph("Financial Ratio Engine: 50+ KPIs & Edge-Case Handling", table_body), Paragraph("Page 4", table_body)],
        [Paragraph("<b>Section 4</b>", table_body), Paragraph("Quantitative Investment Screener & Presets Reference", table_body), Paragraph("Page 5", table_body)],
        [Paragraph("<b>Section 5</b>", table_body), Paragraph("Financial Health & Sector-Relative Composite Scoring", table_body), Paragraph("Page 6", table_body)],
        [Paragraph("<b>Section 6</b>", table_body), Paragraph("Peer Comparison Engine & 8-Axis Radar Benchmarking", table_body), Paragraph("Page 7", table_body)],
        [Paragraph("<b>Section 7</b>", table_body), Paragraph("Cash Flow Intelligence & 8-Pattern Capital Allocation Matrix", table_body), Paragraph("Page 8", table_body)],
        [Paragraph("<b>Section 8</b>", table_body), Paragraph("Statistical Clustering & Machine Learning Financial Archetypes", table_body), Paragraph("Page 9", table_body)],
        [Paragraph("<b>Section 9</b>", table_body), Paragraph("Interactive Streamlit Dashboard: 8-Screen User Guide", table_body), Paragraph("Page 10", table_body)],
        [Paragraph("<b>Section 10</b>", table_body), Paragraph("REST API Specification & Programmatic Query Guide", table_body), Paragraph("Page 11", table_body)],
        [Paragraph("<b>Section 11</b>", table_body), Paragraph("Data Quality Rules (DQ-01 to DQ-16) & Production Runbook", table_body), Paragraph("Page 12", table_body)],
    ]
    t_toc = Table(toc_data, colWidths=[70, 390, 60])
    t_toc.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_toc)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Platform 7-Layer Architecture", h2_style))
    story.append(Paragraph(
        "The platform is engineered as a robust, single-file serverless relational stack decoupled into seven logical layers, "
        "guaranteeing complete reproducibility and sub-second analytical querying.", body_style
    ))
    
    arch_data = [
        [Paragraph("<b>Layer</b>", table_header), Paragraph("<b>Layer Name</b>", table_header), Paragraph("<b>Components & Primary Technologies</b>", table_header)],
        [Paragraph("<b>L1</b>", table_body), Paragraph("Raw Ingestion", table_body), Paragraph("openpyxl, Excel headers normalization, requests URL validator", table_body)],
        [Paragraph("<b>L2</b>", table_body), Paragraph("ETL & Validation", table_body), Paragraph("Ticker normaliser, YYYY-MM year converter, 16 DQ validation rules", table_body)],
        [Paragraph("<b>L3</b>", table_body), Paragraph("Persistent Storage", table_body), Paragraph("SQLite 3.x (data/nifty100.db), foreign key constraint enforcement", table_body)],
        [Paragraph("<b>L4</b>", table_body), Paragraph("Analytics Core", table_body), Paragraph("Vectorized KPI engine, turnaround CAGR logic, leverage & cash flow", table_body)],
        [Paragraph("<b>L5</b>", table_body), Paragraph("Intelligence & ML", table_body), Paragraph("KMeans k=5 clustering, StandardScaler, NLP rule engine (pros/cons)", table_body)],
        [Paragraph("<b>L6</b>", table_body), Paragraph("Reporting Layer", table_body), Paragraph("ReportLab Platypus tearsheets (92 PDFs), sector summaries, Excel", table_body)],
        [Paragraph("<b>L7</b>", table_body), Paragraph("User Interfaces", table_body), Paragraph("Streamlit multi-page dashboard (8 screens), FastAPI (16 endpoints)", table_body)],
    ]
    t_arch = Table(arch_data, colWidths=[40, 110, 370])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_arch)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: DATASET CATALOGUE & DATA MODEL
    # =========================================================================
    story.append(Paragraph("2. Dataset Catalogue & Master Entity Data Model", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    story.append(Paragraph(
        "The data warehouse unifies 7 core datasets extracted from statutory filings and 5 curated supplementary reference datasets. "
        "The primary entity key is the National Stock Exchange (NSE) trading ticker (e.g., <code>TCS</code>, <code>HDFCBANK</code>).", body_style
    ))
    
    ds_data = [
        [Paragraph("<b>Dataset File</b>", table_header), Paragraph("<b>Target DB Table</b>", table_header), Paragraph("<b>Row Count</b>", table_header), Paragraph("<b>Coverage & Nature</b>", table_header)],
        [Paragraph("companies.xlsx", table_body), Paragraph("companies", table_body), Paragraph("92", table_body), Paragraph("Master entity reference, ISIN, corporate description, profile URLs", table_body)],
        [Paragraph("profitandloss.xlsx", table_body), Paragraph("profitandloss", table_body), Paragraph("1,070", table_body), Paragraph("Annual P&L history (FY10–FY24), Revenue, EBITDA, PAT, EPS", table_body)],
        [Paragraph("balancesheet.xlsx", table_body), Paragraph("balancesheet", table_body), Paragraph("1,140", table_body), Paragraph("Annual Balance Sheet, Equity, Borrowings, Net Worth, Total Assets", table_body)],
        [Paragraph("cashflow.xlsx", table_body), Paragraph("cashflow", table_body), Paragraph("1,056", table_body), Paragraph("Statutory Cash Flow statements: Operating (CFO), Investing (CFI), Financing (CFF)", table_body)],
        [Paragraph("documents.xlsx", table_body), Paragraph("documents", table_body), Paragraph("1,456", table_body), Paragraph("BSE India official annual report direct PDF repository URLs", table_body)],
        [Paragraph("prosandcons.xlsx", table_body), Paragraph("prosandcons", table_body), Paragraph("14", table_body), Paragraph("Qualitative investment commentary & corporate highlights", table_body)],
        [Paragraph("sectors.xlsx", table_body), Paragraph("sectors", table_body), Paragraph("92", table_body), Paragraph("11 Macro sectors & 33 granular sub-industry taxonomy mappings", table_body)],
        [Paragraph("stock_prices.xlsx", table_body), Paragraph("stock_prices", table_body), Paragraph("5,520", table_body), Paragraph("60-month historical OHLCV price series (Jan 2020 – Dec 2024)", table_body)],
        [Paragraph("market_cap.xlsx", table_body), Paragraph("market_cap", table_body), Paragraph("552", table_body), Paragraph("Annual valuation multiples (P/E, P/B, EV/EBITDA, Dividend Yield)", table_body)],
        [Paragraph("peer_groups.xlsx", table_body), Paragraph("peer_groups", table_body), Paragraph("56", table_body), Paragraph("11 dedicated peer clusters with benchmark anchor designations", table_body)],
        [Paragraph("financial_ratios.xlsx", table_body), Paragraph("financial_ratios", table_body), Paragraph("1,155", table_body), Paragraph("Computed analytical ratios, CAGR growth rates, and health metrics", table_body)],
    ]
    t_ds = Table(ds_data, colWidths=[105, 90, 50, 275])
    t_ds.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_ds)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Relational Integrity & Join Standards", h2_style))
    story.append(Paragraph(
        "<b>Primary Foreign Key Rules:</b> All subsidiary tables enforce strict foreign key constraints referencing <code>companies.id</code>. "
        "Composite natural keys <code>(company_id, year)</code> are utilized for all longitudinal financial statement tables. "
        "All queries combine statements via <code>USING (company_id, year)</code>.", body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: RATIO ENGINE & MATHEMATICAL LOGIC
    # =========================================================================
    story.append(Paragraph("3. Financial Ratio Engine: 50+ KPIs & Edge Cases", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    story.append(Paragraph(
        "The Ratio Engine (<code>src/analytics/ratio_engine.py</code>) computes core profitability, return, leverage, "
        "efficiency, cash quality, and growth metrics. It rigorously handles accounting boundary conditions and edge cases:", body_style
    ))
    
    kpi_spec = [
        [Paragraph("<b>Metric Name</b>", table_header), Paragraph("<b>Mathematical Formula</b>", table_header), Paragraph("<b>Institutional Benchmark</b>", table_header), Paragraph("<b>Edge-Case Execution Rule</b>", table_header)],
        [Paragraph("<b>Net Profit Margin</b>", table_body), Paragraph("PAT / Revenue × 100", table_body), Paragraph("&gt; 15% (Healthy)", table_body), Paragraph("Returns None if Revenue = 0; allows negative margins.", table_body)],
        [Paragraph("<b>Operating Margin (OPM)</b>", table_body), Paragraph("Operating Profit / Revenue × 100", table_body), Paragraph("&gt; 20% (Strong)", table_body), Paragraph("Cross-validated against source opm_percentage within ±1%.", table_body)],
        [Paragraph("<b>Return on Equity (ROE)</b>", table_body), Paragraph("PAT / (Equity + Reserves) × 100", table_body), Paragraph("&gt; 15% (Compounding)", table_body), Paragraph("<b>CRITICAL:</b> Returns None if Total Equity ≤ 0 (avoids inverted signs).", table_body)],
        [Paragraph("<b>Return on Capital (ROCE)</b>", table_body), Paragraph("EBIT / (Net Worth + Borrowings) × 100", table_body), Paragraph("&gt; 18% (Superior)", table_body), Paragraph("Banks/NBFCs evaluated via sector-relative benchmark.", table_body)],
        [Paragraph("<b>Debt-to-Equity (D/E)</b>", table_body), Paragraph("Borrowings / Total Equity", table_body), Paragraph("&lt; 1.0x (&lt; 0.5x Conservative)", table_body), Paragraph("0.0 for debt-free companies; Financials carved out in screener.", table_body)],
        [Paragraph("<b>Interest Coverage (ICR)</b>", table_body), Paragraph("(Operating Profit + Other Inc) / Interest", table_body), Paragraph("&gt; 3.0x (Safe)", table_body), Paragraph("If Interest = 0, returns None and displays 'Debt Free' (not Inf).", table_body)],
        [Paragraph("<b>Free Cash Flow (FCF)</b>", table_body), Paragraph("CFO + CFI", table_body), Paragraph("&gt; 0 (Self-funding)", table_body), Paragraph("Negative allowed; 3 consecutive negative years triggers distress alert.", table_body)],
        [Paragraph("<b>CFO / PAT Quality Ratio</b>", table_body), Paragraph("Operating Cash Flow / PAT", table_body), Paragraph("&gt; 1.0x (Cash-backed)", table_body), Paragraph("&lt; 0.5x flags 'Accrual Risk'; None if PAT = 0.", table_body)],
        [Paragraph("<b>CapEx Intensity</b>", table_body), Paragraph("abs(CFI) / Sales × 100", table_body), Paragraph("&lt; 3% Light, &gt; 8% Heavy", table_body), Paragraph("Proxy using net investing cash outflows.", table_body)],
        [Paragraph("<b>Asset Turnover</b>", table_body), Paragraph("Sales / Total Assets", table_body), Paragraph("&gt; 1.0x (Capital efficient)", table_body), Paragraph("Returns None if Total Assets = 0.", table_body)],
    ]
    t_kpi = Table(kpi_spec, colWidths=[100, 140, 110, 170])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))

    story.append(Paragraph("CAGR Boundary Decision Matrix", h2_style))
    story.append(Paragraph(
        "Compound Annual Growth Rates (3Y, 5Y, 10Y) for Sales, PAT, and EPS strictly adhere to Section 23.1 rules: "
        "If base year is negative and final year is positive, the engine sets CAGR = None and assigns the <b>TURNAROUND</b> flag. "
        "If base year is positive and final year is negative, it returns <b>DECLINE_TO_LOSS</b>. "
        "If base year is zero, it returns <b>ZERO_BASE</b>. Under no circumstances are imaginary roots generated.", body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: INVESTMENT SCREENER & PRESETS
    # =========================================================================
    story.append(Paragraph("4. Quantitative Investment Screener & Presets Reference", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    story.append(Paragraph(
        "The Screener Engine (<code>src/screener/engine.py</code>) exposes 15+ interactive filters and 6 institutional preset screening strategies. "
        "All filtering thresholds are externalized in <code>config/screener_config.yaml</code>.", body_style
    ))
    
    screen_spec = [
        [Paragraph("<b>Preset Strategy</b>", table_header), Paragraph("<b>Screening Filter Logic</b>", table_header), Paragraph("<b>Ranking KPI</b>", table_header), Paragraph("<b>Expected Count</b>", table_header)],
        [Paragraph("<b>Quality Compounder</b>", table_body), Paragraph("ROE &gt; 15%, D/E &lt; 1.0, FCF &gt; 0, Sales CAGR 5Y &gt; 10%", table_body), Paragraph("Composite Score (Desc)", table_body), Paragraph("15 – 35 Cos (38 Actual)", table_body)],
        [Paragraph("<b>Value Pick</b>", table_body), Paragraph("P/E &lt; 20x, P/B &lt; 3.0x, D/E &lt; 2.0x, Dividend Yield &gt; 1.0%", table_body), Paragraph("FCF Yield (Desc)", table_body), Paragraph("10 – 25 Companies", table_body)],
        [Paragraph("<b>Growth Accelerator</b>", table_body), Paragraph("PAT CAGR 5Y &gt; 20%, Sales CAGR 5Y &gt; 15%, D/E &lt; 2.0x", table_body), Paragraph("PAT CAGR 5Y (Desc)", table_body), Paragraph("8 – 20 Companies", table_body)],
        [Paragraph("<b>Dividend Champion</b>", table_body), Paragraph("Dividend Yield &gt; 2.0%, Dividend Payout &lt; 80%, FCF &gt; 0", table_body), Paragraph("Dividend Yield (Desc)", table_body), Paragraph("10 – 20 Companies", table_body)],
        [Paragraph("<b>Debt-Free Blue Chip</b>", table_body), Paragraph("Borrowings = 0 (or D/E = 0), ROE &gt; 12%, Revenue &gt; ₹5,000 Cr", table_body), Paragraph("ROE (Desc)", table_body), Paragraph("15 – 30 Companies", table_body)],
        [Paragraph("<b>Turnaround Watch</b>", table_body), Paragraph("Sales CAGR 3Y &gt; 10%, FCF positive in latest year, D/E declining", table_body), Paragraph("Sales CAGR 3Y (Desc)", table_body), Paragraph("5 – 15 Companies", table_body)],
    ]
    t_screen = Table(screen_spec, colWidths=[105, 230, 115, 70])
    t_screen.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_screen)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Screener Workflow & Operational Instructions", h2_style))
    story.append(Paragraph("<b>1. Web Interface Execution:</b> Navigate to Screen 03 (<code>pages/03_screener.py</code>) on localhost:8501. Click any preset button to instantly configure the multi-slider filters. The live results table re-computes dynamically.", bullet_style))
    story.append(Paragraph("<b>2. Export Capability:</b> Click the <code>Download CSV</code> button below the filtered table to export a standardized CSV containing all 14 core metrics for offline modeling.", bullet_style))
    story.append(Paragraph("<b>3. Programmatic API Querying:</b> Execute HTTP GET requests to <code>/api/v1/screener?min_roe=15&max_de=1.0</code> for real-time JSON result arrays.", bullet_style))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: FINANCIAL HEALTH & COMPOSITE SCORING
    # =========================================================================
    story.append(Paragraph("5. Financial Health & Composite Scoring Model", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    story.append(Paragraph(
        "To enable equitable cross-sector comparisons, the platform implements a <b>Sector-Relative Winsorised Scoring Model</b>. "
        "Raw metrics are grouped by macro-sector, winsorised at the 10th and 90th percentiles to neutralize extreme outliers, "
        "and scaled into a standard 0 to 100 distribution.", body_style
    ))
    
    weights_data = [
        [Paragraph("<b>Analytical Dimension</b>", table_header), Paragraph("<b>Weight</b>", table_header), Paragraph("<b>Sub-KPI Breakdown</b>", table_header), Paragraph("<b>Mathematical Normalisation</b>", table_header)],
        [Paragraph("<b>Profitability & Efficiency</b>", table_body), Paragraph("<b>50%</b>", table_body), Paragraph("ROE (33.3%), ROCE (33.3%), Net Profit Margin (33.4%)", table_body), Paragraph("Higher is better. Winsorised at P10/P90 within sector.", table_body)],
        [Paragraph("<b>Growth Momentum</b>", table_body), Paragraph("<b>30%</b>", table_body), Paragraph("Revenue CAGR 5Y (50%), PAT CAGR 5Y (50%)", table_body), Paragraph("Higher is better. Turnaround or loss flags assigned score = 0.", table_body)],
        [Paragraph("<b>Valuation Attractiveness</b>", table_body), Paragraph("<b>20%</b>", table_body), Paragraph("Price-to-Earnings (50%), Price-to-Book (50%)", table_body), Paragraph("Lower is better (inverse scaling: (P90 - val) / (P90 - P10) × 100).", table_body)],
    ]
    t_weights = Table(weights_data, colWidths=[120, 50, 180, 170])
    t_weights.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_weights)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Composite Quality Score Triage Bands", h2_style))
    story.append(Paragraph(
        "The resulting Composite Quality Score (0–100) provides instantaneous portfolio triage: "
        "<br/>• <b>Tier 1: Elite Compounders (Score &ge; 75):</b> High capital returns backed by secular growth and disciplined balance sheets. "
        "<br/>• <b>Tier 2: Quality Core (60 &le; Score &lt; 75):</b> Robust businesses with steady profitability and moderate leverage. "
        "<br/>• <b>Tier 3: Moderate / Neutral (45 &le; Score &lt; 60):</b> Cyclical or capital-intensive operations sensitive to macro trends. "
        "<br/>• <b>Tier 4: Watchlist / Stressed (Score &lt; 45):</b> Low return on capital, declining growth trajectories, or elevated balance sheet gearing.", body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 7: PEER ENGINE & RADAR BENCHMARKING
    # =========================================================================
    story.append(Paragraph("6. Peer Comparison Engine & Radar Benchmarking", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    story.append(Paragraph(
        "The Peer Engine (<code>src/analytics/peer.py</code>) groups companies into 11 competitive sub-industry peer groups "
        "designated in <code>data/supporting/peer_groups.xlsx</code>. For every company and financial metric, it computes intra-peer "
        "percentile ranks via <code>PERCENT_RANK() OVER (PARTITION BY peer_group ORDER BY metric)</code>.", body_style
    ))
    
    peer_data = [
        [Paragraph("<b>Peer Group Cluster</b>", table_header), Paragraph("<b>Constituent Member Companies</b>", table_header), Paragraph("<b>Anchor Benchmark</b>", table_header)],
        [Paragraph("<b>Private Banks</b>", table_body), Paragraph("HDFCBANK, ICICIBANK, AXISBANK, KOTAKBANK, INDUSINDBK", table_body), Paragraph("HDFCBANK", table_body)],
        [Paragraph("<b>Public Banks</b>", table_body), Paragraph("SBIN, BANKBARODA, CANBK, PNB", table_body), Paragraph("SBIN", table_body)],
        [Paragraph("<b>IT Services</b>", table_body), Paragraph("TCS, INFY, HCLTECH, TECHM, LTIM", table_body), Paragraph("TCS", table_body)],
        [Paragraph("<b>Pharmaceuticals</b>", table_body), Paragraph("SUNPHARMA, CIPLA, DRREDDY, DIVISLAB, TORNTPHARM", table_body), Paragraph("SUNPHARMA", table_body)],
        [Paragraph("<b>Automobiles</b>", table_body), Paragraph("MARUTI, TATAMOTORS, M&M, BAJAJ-AUTO, EICHERMOT, HEROMOTOCO, TVSMOTOR", table_body), Paragraph("MARUTI", table_body)],
        [Paragraph("<b>Life Insurance</b>", table_body), Paragraph("LICI, HDFCLIFE, SBILIFE, ICICIPRULI", table_body), Paragraph("LICI", table_body)],
        [Paragraph("<b>Oil & Gas</b>", table_body), Paragraph("RELIANCE, ONGC, BPCL, IOC, GAIL", table_body), Paragraph("RELIANCE", table_body)],
        [Paragraph("<b>Power & Utilities</b>", table_body), Paragraph("NTPC, POWERGRID, TATAPOWER, ADANIPOWER, NHPC, JSWENERGY, ADANIGREEN", table_body), Paragraph("NTPC", table_body)],
        [Paragraph("<b>Steel & Metals</b>", table_body), Paragraph("TATASTEEL, JSWSTEEL, JINDALSTEL, HINDALCO", table_body), Paragraph("TATASTEEL", table_body)],
        [Paragraph("<b>FMCG / Staples</b>", table_body), Paragraph("HINDUNILVR, ITC, BRITANNIA, DABUR, NESTLEIND, GODREJCP, TATACONSUM", table_body), Paragraph("HINDUNILVR", table_body)],
        [Paragraph("<b>Consumer Finance</b>", table_body), Paragraph("BAJFINANCE, CHOLAFIN, SHRIRAMFIN", table_body), Paragraph("BAJFINANCE", table_body)],
    ]
    t_peer = Table(peer_data, colWidths=[110, 310, 100])
    t_peer.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_peer)
    story.append(Spacer(1, 10))

    story.append(Paragraph("8-Axis Radar Chart Interpretation", h2_style))
    story.append(Paragraph(
        "Radar charts (saved in <code>reports/radar_charts/</code> and accessible on Dashboard Screen 04) evaluate: "
        "<b>ROE, ROCE, NPM, D/E (inverted), FCF, PAT CAGR 5Y, Revenue CAGR 5Y, and EPS CAGR 5Y</b>. "
        "A polygon expanding toward the outer perimeter indicates superior competitive performance against the peer group average (dashed benchmark circle).", body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 8: CASH FLOW INTELLIGENCE & CAPITAL ALLOCATION
    # =========================================================================
    story.append(Paragraph("7. Cash Flow Intelligence & Capital Allocation", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    story.append(Paragraph(
        "Accounting profits can be distorted by non-cash accruals. The Cash Flow Intelligence module (<code>src/analytics/cashflow_kpis.py</code>) "
        "dissects core cash generation and classifies every company into one of 8 capital allocation sign patterns.", body_style
    ))
    
    cap_data = [
        [Paragraph("<b>Sign Pattern (CFO, CFI, CFF)</b>", table_header), Paragraph("<b>Classification Label</b>", table_header), Paragraph("<b>Economic Rationale & Business Meaning</b>", table_header)],
        [Paragraph("<b>( + , − , − )</b>", table_body), Paragraph("Reinvestor / Debt Repayer", table_body), Paragraph("Ideal compounding profile: Organic operations fund both CapEx and debt retirement / dividends.", table_body)],
        [Paragraph("<b>( + , + , − )</b>", table_body), Paragraph("Asset Seller / Debt Repayer", table_body), Paragraph("Downsizing or non-core asset divestment utilized to repay borrowings.", table_body)],
        [Paragraph("<b>( + , − , + )</b>", table_body), Paragraph("Reinvestor / Raising Capital", table_body), Paragraph("Aggressive capacity expansion: Operating cash supplemented with external debt/equity.", table_body)],
        [Paragraph("<b>( + , + , + )</b>", table_body), Paragraph("Asset Seller / Raising Cap", table_body), Paragraph("Cash hoarding / strategic liquidity buildup across all financing channels.", table_body)],
        [Paragraph("<b>( − , − , − )</b>", table_body), Paragraph("Distress Burning Cash", table_body), Paragraph("High risk: Cash reserves rapidly depleting across all operational and investing fronts.", table_body)],
        [Paragraph("<b>( − , + , − )</b>", table_body), Paragraph("Distress Asset Seller", table_body), Paragraph("Operational losses covered by divesting productive fixed assets to service liabilities.", table_body)],
        [Paragraph("<b>( − , − , + )</b>", table_body), Paragraph("Distress Raising Capital", table_body), Paragraph("External borrowing or dilution strictly to fund ongoing operational losses (Red Flag).", table_body)],
        [Paragraph("<b>( − , + , + )</b>", table_body), Paragraph("Distress Raising / Selling", table_body), Paragraph("Severe cash burn requiring emergency asset sales and debt capital infusions.", table_body)],
    ]
    t_cap = Table(cap_data, colWidths=[130, 130, 260])
    t_cap.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_cap)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Early Distress Warning Signals", h2_style))
    story.append(Paragraph(
        "The system triggers an automated distress alert in <code>output/distress_alerts.csv</code> whenever a company demonstrates: "
        "<br/>1. <b>Operating Cash Burn:</b> CFO &lt; 0 in conjunction with positive financing flows (CFF &gt; 0). "
        "<br/>2. <b>Sustained Negative Free Cash Flow:</b> FCF negative for 3 consecutive financial years. "
        "<br/>3. <b>Accrual Divergence:</b> CFO / PAT ratio &lt; 0.50x over a 3-year average, signaling aggressive revenue recognition.", body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 9: MACHINE LEARNING & STATISTICAL CLUSTERING
    # =========================================================================
    story.append(Paragraph("8. Statistical Clustering & ML Financial Archetypes", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    story.append(Paragraph(
        "To discover hidden structures and groupings across the Nifty 100 universe, <code>src/analytics/clustering.py</code> "
        "applies unsupervised <b>K-Means Clustering ($k=5$)</b> on normalized multi-dimensional financial features.", body_style
    ))
    
    cluster_data = [
        [Paragraph("<b>Cluster ID & Name</b>", table_header), Paragraph("<b>Constituent Count</b>", table_header), Paragraph("<b>Defining Financial Signature & Profile</b>", table_header)],
        [Paragraph("<b>0: High-Quality Compounders</b>", table_body), Paragraph("2 Companies", table_body), Paragraph("Exceptional ROE (&gt;35%), negligible leverage (D/E &lt; 0.1), strong pricing power and high FCF yields.", table_body)],
        [Paragraph("<b>1: Defensive Dividend Payers</b>", table_body), Paragraph("58 Companies", table_body), Paragraph("Mature market leaders, stable cash flows, consistent dividend yields, conservative balance sheets.", table_body)],
        [Paragraph("<b>2: Value Cyclicals</b>", table_body), Paragraph("2 Companies", table_body), Paragraph("Capital-intensive, commodity or credit cyclical exposure, low valuation multiples, volatile OPM.", table_body)],
        [Paragraph("<b>3: Distressed / Turnaround</b>", table_body), Paragraph("14 Companies", table_body), Paragraph("Depressed ROE, elevated gearing ratios (D/E &gt; 2.0x), negative or highly volatile free cash flow.", table_body)],
        [Paragraph("<b>4: Emerging Growth</b>", table_body), Paragraph("16 Companies", table_body), Paragraph("Rapid top-line expansion (Revenue CAGR &gt; 18%), aggressive CapEx reinvestment, moderate margins.", table_body)],
    ]
    t_cluster = Table(cluster_data, colWidths=[140, 75, 305])
    t_cluster.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_cluster)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Mathematical Methodology & Normalisation", h2_style))
    story.append(Paragraph(
        "<b>Feature Imputation & Scaling:</b> Missing metrics are imputed using sector medians. All five input features "
        "(ROE %, Debt-to-Equity, Revenue CAGR 5Y, FCF CAGR 5Y, and OPM %) are scaled to zero mean and unit variance via <code>StandardScaler</code>. "
        "The optimal number of clusters ($k=5$) was confirmed using the inertia elbow plot (<code>reports/elbow_plot.png</code>).", body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 10: STREAMLIT DASHBOARD USER MANUAL
    # =========================================================================
    story.append(Paragraph("9. Streamlit Dashboard: 8-Screen User Manual", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    story.append(Paragraph(
        "The interactive web dashboard is launched via <code>streamlit run src/dashboard/app.py</code> and runs on <code>http://localhost:8501</code>. "
        "The sidebar allows zero-latency navigation across all 8 specialized analytical screens:", body_style
    ))
    
    screen_guide = [
        [Paragraph("<b>Screen ID & Name</b>", table_header), Paragraph("<b>Key Visual Widgets & Functionality</b>", table_header), Paragraph("<b>Data Source & Interactivity</b>", table_header)],
        [Paragraph("<b>01 - Home</b>", table_body), Paragraph("Market summary tiles (Avg ROE, Med P/E, Med D/E), Plotly sector donut, Top 5 quality compounders.", table_body), Paragraph("Global year selector (2019 to 2024); instant recalculation.", table_body)],
        [Paragraph("<b>02 - Company Profile</b>", table_body), Paragraph("Company card, 6 KPI cards, 10Y Revenue/PAT dual bars, ROE/ROCE lines, automated NLP pros/cons badges.", table_body), Paragraph("Instant autocomplete search dropdown by Ticker or Name.", table_body)],
        [Paragraph("<b>03 - Screener</b>", table_body), Paragraph("10 metric sidebar sliders, 6 one-click preset buttons, live-updating filtered table, CSV download button.", table_body), Paragraph("Filters applied in-memory across 92 companies with instant response.", table_body)],
        [Paragraph("<b>04 - Peer Comparison</b>", table_body), Paragraph("Interactive 8-axis Plotly radar polygon overlaying company vs peer group average, side-by-side KPI table.", table_body), Paragraph("Dropdowns for 11 Peer Groups and constituent ticker selection.", table_body)],
        [Paragraph("<b>05 - Trend Analysis</b>", table_body), Paragraph("10-year time-series trend line charts with YoY growth rate percentage labels.", table_body), Paragraph("Multi-metric overlay: select up to 3 financial KPIs simultaneously.", table_body)],
        [Paragraph("<b>06 - Sector Analysis</b>", table_body), Paragraph("Scatter bubble chart (X=Revenue, Y=ROE, Bubble Size=Market Cap, Color=Sub-Sector), median KPI bar chart.", table_body), Paragraph("Macro sector selector (11 sectors) with sub-sector coloring.", table_body)],
        [Paragraph("<b>07 - Capital Allocation</b>", table_body), Paragraph("Interactive Plotly Treemap mapping 92 companies across the 8 cash flow allocation regimes.", table_body), Paragraph("Interactive zoom/drill-down into constituent companies.", table_body)],
        [Paragraph("<b>08 - Annual Reports</b>", table_body), Paragraph("Repository of direct BSE India annual report filing URLs with automated 404 validity checking.", table_body), Paragraph("Company search box with status badges (📄 Available, 🚨 404).", table_body)],
    ]
    t_sg = Table(screen_guide, colWidths=[110, 230, 180])
    t_sg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_sg)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 11: REST API DEVELOPER REFERENCE
    # =========================================================================
    story.append(Paragraph("10. REST API Specification & Integration Guide", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    story.append(Paragraph(
        "The REST API is built on FastAPI and Uvicorn, serving 16 endpoints prefixed with <code>/api/v1</code>. "
        "Interactive Swagger documentation is available at <code>http://localhost:8000/docs</code>.", body_style
    ))
    
    api_guide = [
        [Paragraph("<b>HTTP Method & Route</b>", table_header), Paragraph("<b>Parameters & Filtering</b>", table_header), Paragraph("<b>Response Payload Description</b>", table_header)],
        [Paragraph("<b>GET</b> /api/v1/health", table_body), Paragraph("None", table_body), Paragraph("Status 'ok', uptime_seconds, and exact row counts for all 10 SQLite tables.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/companies", table_body), Paragraph("?sector=&market_cap_category=&search=", table_body), Paragraph("Array of 92 companies with metadata, latest ROE, and ROCE metrics.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/companies/{ticker}", table_body), Paragraph("Path: ticker (e.g. TCS)", table_body), Paragraph("Full profile object: description, sector, latest ratios, and pros/cons.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/companies/{ticker}/pl", table_body), Paragraph("?from_year=&to_year=", table_body), Paragraph("Longitudinal P&L history: sales, operating_profit, net_profit, EPS.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/companies/{ticker}/bs", table_body), Paragraph("?from_year=&to_year=", table_body), Paragraph("Balance Sheet series: equity, reserves, borrowings, total_assets.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/companies/{ticker}/cashflow", table_body), Paragraph("?from_year=&to_year=", table_body), Paragraph("Statutory cash flow series: CFO, CFI, CFF, net_cash_flow.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/companies/{ticker}/ratios", table_body), Paragraph("?year=", table_body), Paragraph("Array of 14 computed KPIs per year including CAGRs and margins.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/companies/{ticker}/tearsheet", table_body), Paragraph("Path: ticker", table_body), Paragraph("Direct binary PDF stream download of 2-page company tearsheet.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/screener", table_body), Paragraph("?min_roe=&max_de=&sector=&min_rev_cagr_5yr=", table_body), Paragraph("Filtered, ranked JSON array of matching companies with composite score.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/sectors", table_body), Paragraph("None", table_body), Paragraph("Summary of 11 macro sectors with median ROE, P/E, and D/E benchmarks.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/peers/{group_name}", table_body), Paragraph("Path: group_name (e.g. IT Services)", table_body), Paragraph("Percentile rank table across 8 axes for all member companies.", table_body)],
        [Paragraph("<b>GET</b> /api/v1/portfolio/stats", table_body), Paragraph("None", table_body), Paragraph("Portfolio distribution: P10, P25, P50, P75, P90, Mean, Std for 10 KPIs.", table_body)],
    ]
    t_api = Table(api_guide, colWidths=[130, 160, 230])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_api)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Sample cURL Invocation", h2_style))
    sample_curl = "curl -X GET 'http://localhost:8000/api/v1/screener?min_roe=15&max_de=1.0' -H 'Accept: application/json'"
    story.append(Paragraph(f"<code>{sample_curl}</code>", code_style))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 12: DATA QUALITY & PRODUCTION RUNBOOK
    # =========================================================================
    story.append(Paragraph("11. Data Quality Rules & Production Runbook", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=2, spaceAfter=10))
    story.append(Paragraph(
        "The platform implements 16 automated Data Quality (DQ) validation rules executed during raw data ingestion. "
        "Violations are triaged and logged to <code>output/validation_failures.csv</code>:", body_style
    ))
    
    dq_summary = [
        [Paragraph("<b>Rule ID & Name</b>", table_header), Paragraph("<b>Validation Condition</b>", table_header), Paragraph("<b>Severity</b>", table_header), Paragraph("<b>Pipeline Enforcement Action</b>", table_header)],
        [Paragraph("<b>DQ-01: Company PK</b>", table_body), Paragraph("companies.id unique (92 unique)", table_body), Paragraph("CRITICAL", table_body), Paragraph("Halt pipeline immediately on duplicate.", table_body)],
        [Paragraph("<b>DQ-02: Annual PK</b>", table_body), Paragraph("Unique (company_id, year) pair", table_body), Paragraph("CRITICAL", table_body), Paragraph("Deduplicate: keep latest occurrence.", table_body)],
        [Paragraph("<b>DQ-03: FK Integrity</b>", table_body), Paragraph("child.company_id in companies.id", table_body), Paragraph("CRITICAL", table_body), Paragraph("Reject orphan rows; log to CSV.", table_body)],
        [Paragraph("<b>DQ-04: BS Match</b>", table_body), Paragraph("|Assets - Liabilities| / Assets &lt; 0.01", table_body), Paragraph("WARNING", table_body), Paragraph("Flag row for analyst review.", table_body)],
        [Paragraph("<b>DQ-05: OPM Check</b>", table_body), Paragraph("|OPM_calc - OPM_source| &lt; 1.0%", table_body), Paragraph("WARNING", table_body), Paragraph("Use computed OPM; keep source for display.", table_body)],
        [Paragraph("<b>DQ-06: Non-Zero Sales</b>", table_body), Paragraph("Sales &gt; 0 for non-banks", table_body), Paragraph("WARNING", table_body), Paragraph("Exclude zero sales rows from CAGR growth.", table_body)],
        [Paragraph("<b>DQ-07: Year Format</b>", table_body), Paragraph("Normalized matches r'^\\d{4}-\\d{2}$'", table_body), Paragraph("CRITICAL", table_body), Paragraph("Reject unparseable dates (e.g. TTM).", table_body)],
        [Paragraph("<b>DQ-08: Ticker Format</b>", table_body), Paragraph("2 &le; length(ticker) &le; 12, uppercase", table_body), Paragraph("CRITICAL", table_body), Paragraph("Normalize whitespace; reject out-of-range.", table_body)],
        [Paragraph("<b>DQ-09: Cash Integrity</b>", table_body), Paragraph("|NCF - (CFO+CFI+CFF)| &le; 10 Cr", table_body), Paragraph("WARNING", table_body), Paragraph("Recompute NCF from components.", table_body)],
        [Paragraph("<b>DQ-10: Fixed Assets</b>", table_body), Paragraph("Fixed Assets &ge; 0", table_body), Paragraph("WARNING", table_body), Paragraph("Coerce negative values to 0.", table_body)],
        [Paragraph("<b>DQ-11: Tax Rate Range</b>", table_body), Paragraph("0% &le; Tax Rate &le; 60%", table_body), Paragraph("WARNING", table_body), Paragraph("Flag out-of-range tax reversals.", table_body)],
        [Paragraph("<b>DQ-12: Payout Cap</b>", table_body), Paragraph("Dividend Payout &le; 200%", table_body), Paragraph("WARNING", table_body), Paragraph("Flag probable data-entry error.", table_body)],
        [Paragraph("<b>DQ-13: URL Check</b>", table_body), Paragraph("requests.head() status == 200", table_body), Paragraph("WARNING", table_body), Paragraph("Log 404 URLs without rejecting row.", table_body)],
        [Paragraph("<b>DQ-14: EPS Sign</b>", table_body), Paragraph("EPS &gt; 0 if PAT &gt; 0", table_body), Paragraph("WARNING", table_body), Paragraph("Flag dilution / accounting adjustment.", table_body)],
        [Paragraph("<b>DQ-16: History Check</b>", table_body), Paragraph("Company records &ge; 5 years", table_body), Paragraph("WARNING", table_body), Paragraph("Flag short tenure; exclude from CAGR.", table_body)],
    ]
    t_dq = Table(dq_summary, colWidths=[100, 150, 60, 210])
    t_dq.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_dq)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Production Quick-Start Execution Sequence", h2_style))
    story.append(Paragraph("<code># 1. Build SQLite Data Warehouse:  python src/etl/loader.py</code>", code_style))
    story.append(Paragraph("<code># 2. Compute 50+ Financial KPIs:   python -m src.analytics.ratio_engine</code>", code_style))
    story.append(Paragraph("<code># 3. Generate Screener & Scored:   python -m src.screener.engine</code>", code_style))
    story.append(Paragraph("<code># 4. Generate All 92 Tearsheets:   python -m src.reports.tearsheet</code>", code_style))
    story.append(Paragraph("<code># 5. Launch Web Dashboard:         streamlit run src/dashboard/app.py</code>", code_style))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    
    # Verify page count
    reader = PdfReader(output_pdf_path)
    return len(reader.pages)

if __name__ == '__main__':
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    out_pdf = os.path.join(base_dir, 'docs', 'analyst_guide.pdf')
    pages = build_analyst_guide(out_pdf)
    print(f"Analyst Guide PDF successfully generated at {out_pdf} with {pages} pages.")
