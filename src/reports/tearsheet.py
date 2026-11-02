import os
import io
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

# NumberedCanvas to draw exact page numbers "Page X of 2"
class NumberedCanvas(canvas.Canvas):
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
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 24, 15, page_text)
        self.drawString(24, 15, "Nifty 100 Financial Intelligence Platform  |  Confidential & Proprietary")
        self.restoreState()


def render_revenue_profit_chart(pl_df):
    plt.close('all')
    fig, ax = plt.subplots(figsize=(7.2, 2.3), dpi=200)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#F7FAFC')

    years = pl_df['year'].astype(str).str[:4].tolist()
    sales = (pl_df['sales'] / 1000.0).tolist() if 'sales' in pl_df else [0]*len(years)
    net_profit = (pl_df['net_profit'] / 1000.0).tolist() if 'net_profit' in pl_df else [0]*len(years)

    x = np.arange(len(years))
    width = 0.38

    ax.bar(x - width/2, sales, width, label='Revenue (₹k Cr)', color='#2B6CB0', edgecolor='none')
    ax.bar(x + width/2, net_profit, width, label='Net Profit (₹k Cr)', color='#38A169', edgecolor='none')

    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=7.5, rotation=0)
    ax.set_ylabel('₹ Thousand Cr', fontsize=7.5, color='#4A5568')
    ax.tick_params(axis='both', which='major', labelsize=7)
    ax.grid(axis='y', linestyle='--', alpha=0.5, color='#CBD5E0')
    ax.legend(loc='upper left', fontsize=7, frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0')
    ax.set_title('10-Year Revenue & Net Profit Trajectory', fontsize=8.5, fontweight='bold', color='#1A365D', pad=4)

    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def render_roe_roce_chart(ratios_df):
    plt.close('all')
    fig, ax1 = plt.subplots(figsize=(7.2, 2.3), dpi=200)
    fig.patch.set_facecolor('#FFFFFF')
    ax1.set_facecolor('#F7FAFC')

    years = ratios_df['year'].astype(str).str[:4].tolist()
    roe = ratios_df['return_on_equity_pct'].tolist()
    roce = ratios_df['return_on_capital_pct'].tolist()

    x = np.arange(len(years))

    ax1.plot(x, roe, marker='o', linewidth=2, color='#D69E2E', label='ROE (%)', markersize=4)
    ax1.plot(x, roce, marker='s', linewidth=2, color='#3182CE', label='ROCE (%)', markersize=4)

    ax1.set_xticks(x)
    ax1.set_xticklabels(years, fontsize=7.5, rotation=0)
    ax1.set_ylabel('Return (%)', fontsize=7.5, color='#4A5568')
    ax1.tick_params(axis='both', which='major', labelsize=7)
    ax1.grid(axis='y', linestyle='--', alpha=0.5, color='#CBD5E0')
    ax1.legend(loc='upper right', fontsize=7, frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0')
    ax1.set_title('Capital Efficiency: ROE vs ROCE Dual-Axis Trend', fontsize=8.5, fontweight='bold', color='#1A365D', pad=4)

    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def render_balance_sheet_chart(bs_df):
    plt.close('all')
    fig, ax = plt.subplots(figsize=(3.5, 2.1), dpi=200)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#F7FAFC')

    years = bs_df['year'].astype(str).str[:4].tolist()[-6:]
    bs_tail = bs_df.tail(6)

    equity = (bs_tail['equity_capital'] + bs_tail['reserves']) / 1000.0
    borrowings = bs_tail['borrowings'] / 1000.0
    other = bs_tail['other_liabilities'] / 1000.0

    x = np.arange(len(years))
    width = 0.55

    ax.bar(x, equity, width, label='Net Worth', color='#2B6CB0')
    ax.bar(x, borrowings, width, bottom=equity, label='Borrowings', color='#E53E3E')
    ax.bar(x, other, width, bottom=equity + borrowings, label='Other Liab', color='#A0AEC0')

    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=6.5)
    ax.set_ylabel('₹k Cr', fontsize=6.5, color='#4A5568')
    ax.tick_params(axis='both', which='major', labelsize=6.5)
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#CBD5E0')
    ax.legend(loc='upper left', fontsize=5.5, frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0')
    ax.set_title('Balance Sheet Composition', fontsize=7.5, fontweight='bold', color='#1A365D', pad=3)

    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def render_cash_flow_waterfall(cf_df):
    plt.close('all')
    fig, ax = plt.subplots(figsize=(3.5, 2.1), dpi=200)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#F7FAFC')

    if not cf_df.empty:
        lat = cf_df.iloc[-1]
        cfo = (lat.get('operating_activity', 0) or 0) / 1000.0
        cfi = (lat.get('investing_activity', 0) or 0) / 1000.0
        cff = (lat.get('financing_activity', 0) or 0) / 1000.0
        net = (lat.get('net_cash_flow', 0) or 0) / 1000.0
    else:
        cfo, cfi, cff, net = 0, 0, 0, 0

    categories = ['CFO', 'CFI', 'CFF', 'Net CF']
    vals = [cfo, cfi, cff, net]
    colors_list = ['#38A169' if v >= 0 else '#E53E3E' for v in vals]

    x = np.arange(len(categories))
    width = 0.55

    bars = ax.bar(x, vals, width, color=colors_list)
    ax.axhline(0, color='#718096', linewidth=0.8, linestyle='--')

    for bar, val in zip(bars, vals):
        height = bar.get_height()
        va = 'bottom' if height >= 0 else 'top'
        ax.annotate(f"{val:.1f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 2 if height >= 0 else -6),
                    textcoords="offset points",
                    ha='center', va=va, fontsize=6, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=6.5)
    ax.set_ylabel('₹k Cr', fontsize=6.5, color='#4A5568')
    ax.tick_params(axis='both', which='major', labelsize=6.5)
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#CBD5E0')
    ax.set_title('Latest Cash Flow Breakdown (₹k Cr)', fontsize=7.5, fontweight='bold', color='#1A365D', pad=3)

    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_company_tearsheet(ticker: str, db_path: str, output_pdf: str, pros_cons_df=None, cap_alloc_df=None) -> tuple[bool, str]:
    """Generate professional 2-page company tearsheet PDF."""
    with sqlite3.connect(db_path) as conn:
        comp_df = pd.read_sql('SELECT * FROM companies WHERE id = ?', conn, params=[ticker])
        ratios_df = pd.read_sql('SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year', conn, params=[ticker])
        pl_df = pd.read_sql('SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year', conn, params=[ticker])
        bs_df = pd.read_sql('SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year', conn, params=[ticker])
        cf_df = pd.read_sql('SELECT * FROM cashflow WHERE company_id = ? ORDER BY year', conn, params=[ticker])
        mc_df = pd.read_sql('SELECT * FROM market_cap WHERE company_id = ? ORDER BY year', conn, params=[ticker])
        sec_df = pd.read_sql('SELECT * FROM sectors WHERE company_id = ?', conn, params=[ticker])

    if comp_df.empty:
        raise ValueError(f"Company {ticker} not found in database.")

    comp_name = comp_df.iloc[0]['company_name']
    sector = sec_df.iloc[0]['broad_sector'] if not sec_df.empty else "N/A"
    sub_sector = sec_df.iloc[0]['sub_sector'] if not sec_df.empty else "N/A"

    # Require at least 1 year of financial data
    if len(pl_df) < 1:
        return False, "No financial statement data available"

    # Latest KPIs
    lat_r = ratios_df.iloc[-1] if not ratios_df.empty else {}
    lat_mc = mc_df.iloc[-1] if not mc_df.empty else {}

    market_cap_val = lat_mc.get('market_cap_crore')
    market_cap_str = f"₹{market_cap_val:,.0f} Cr" if pd.notna(market_cap_val) else "N/A"

    pe_val = lat_mc.get('pe_ratio')
    pe_str = f"{pe_val:.1f}x" if pd.notna(pe_val) else "N/A"

    roe_val = lat_r.get('return_on_equity_pct')
    roe_str = f"{roe_val:.1f}%" if pd.notna(roe_val) else "N/A"

    roce_val = lat_r.get('return_on_capital_pct')
    roce_str = f"{roce_val:.1f}%" if pd.notna(roce_val) else "N/A"

    de_val = lat_r.get('debt_to_equity')
    de_str = f"{de_val:.2f}x" if pd.notna(de_val) else "N/A"

    cagr_val = lat_r.get('revenue_cagr_5yr')
    cagr_str = f"{cagr_val:.1f}%" if pd.notna(cagr_val) else "N/A"

    # Setup ReportLab Document
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=24,
        rightMargin=24,
        topMargin=20,
        bottomMargin=24
    )

    styles = getSampleStyleSheet()

    header_title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.white
    )

    header_sub_style = ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#E2E8F0')
    )

    tile_label_style = ParagraphStyle(
        'TileLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#718096')
    )

    tile_val_style = ParagraphStyle(
        'TileVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=13,
        textColor=colors.HexColor('#1A365D')
    )

    sec_header_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1A365D')
    )

    bullet_pro_style = ParagraphStyle(
        'BulletPro',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#22543D')
    )

    bullet_con_style = ParagraphStyle(
        'BulletCon',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#742A2A')
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1A365D'),
        alignment=1 # Center
    )

    story = []

    # ================= PAGE 1 =================
    # Top Navy Header Banner
    header_content = [
        [
            Paragraph(f"<b>{comp_name}</b> ({ticker})", header_title_style),
            Paragraph(f"Sector: <b>{sector}</b>  |  Sub-Sector: <b>{sub_sector}</b>  |  Nifty 100", header_sub_style)
        ]
    ]
    header_table = Table(header_content, colWidths=[260, 287])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1A365D')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # 6 KPI Tiles in 2 rows of 3
    kpi_data = [
        [
            [Paragraph("MARKET CAP", tile_label_style), Paragraph(market_cap_str, tile_val_style)],
            [Paragraph("P/E RATIO", tile_label_style), Paragraph(pe_str, tile_val_style)],
            [Paragraph("RETURN ON EQUITY", tile_label_style), Paragraph(roe_str, tile_val_style)],
        ],
        [
            [Paragraph("ROCE", tile_label_style), Paragraph(roce_str, tile_val_style)],
            [Paragraph("DEBT TO EQUITY", tile_label_style), Paragraph(de_str, tile_val_style)],
            [Paragraph("5Y REVENUE CAGR", tile_label_style), Paragraph(cagr_str, tile_val_style)],
        ]
    ]

    tile_table = Table(kpi_data, colWidths=[182, 182, 183], rowHeights=[26, 26])
    tile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EDF2F7')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(tile_table)
    story.append(Spacer(1, 10))

    # Chart 1: Revenue & Net Profit
    chart1_buf = render_revenue_profit_chart(pl_df)
    story.append(Image(chart1_buf, width=547, height=175))
    story.append(Spacer(1, 10))

    # Chart 2: ROE & ROCE Dual Axis
    chart2_buf = render_roe_roce_chart(ratios_df)
    story.append(Image(chart2_buf, width=547, height=175))

    # ================= PAGE 2 =================
    story.append(PageBreak())

    # Header Page 2
    header_p2 = [
        [
            Paragraph(f"<b>{comp_name}</b> ({ticker}) — Financial Health & Qualitative Audit", header_title_style),
            Paragraph("Page 2 of 2", header_sub_style)
        ]
    ]
    p2_table = Table(header_p2, colWidths=[400, 147])
    p2_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1A365D')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(p2_table)
    story.append(Spacer(1, 6))

    # Capital Allocation Badge
    cap_label = "Reinvestor / Debt Repayer"
    if cap_alloc_df is not None and not cap_alloc_df.empty:
        c_ca = cap_alloc_df[cap_alloc_df['company_id'] == ticker]
        if not c_ca.empty:
            cap_label = c_ca.iloc[-1].get('capital_allocation_label', cap_label)

    badge_data = [[
        Paragraph(f"<b>Capital Allocation Pattern:</b> {cap_label}", badge_style)
    ]]
    badge_table = Table(badge_data, colWidths=[547], rowHeights=[20])
    badge_color = colors.HexColor('#EBF8FF') if "Reinvestor" in cap_label else colors.HexColor('#FFF5F5') if "Distress" in cap_label else colors.HexColor('#F7FAFC')
    badge_border = colors.HexColor('#3182CE') if "Reinvestor" in cap_label else colors.HexColor('#E53E3E') if "Distress" in cap_label else colors.HexColor('#CBD5E0')
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), badge_color),
        ('BOX', (0, 0), (-1, -1), 1, badge_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 6))

    # Side by side charts: Balance Sheet Stacked Bar & Cash Flow Waterfall
    chart3_buf = render_balance_sheet_chart(bs_df)
    chart4_buf = render_cash_flow_waterfall(cf_df)
    charts_row = [
        [Image(chart3_buf, width=270, height=160), Image(chart4_buf, width=270, height=160)]
    ]
    charts_table = Table(charts_row, colWidths=[273, 274])
    charts_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(charts_table)
    story.append(Spacer(1, 6))

    # Pros and Cons Data
    c_pros = []
    c_cons = []
    if pros_cons_df is not None and not pros_cons_df.empty:
        c_pc = pros_cons_df[pros_cons_df['company_id'] == ticker]
        c_pros = c_pc[c_pc['type'] == 'pro']['text'].tolist()[:3]
        c_cons = c_pc[c_pc['type'] == 'con']['text'].tolist()[:3]

    if not c_pros:
        c_pros = ["Demonstrates strong market standing and consistent operational presence."]
    if not c_cons:
        c_cons = ["Market conditions and sector cyclicality require regular ongoing monitoring."]

    # Pros Section Table
    story.append(Paragraph("<b>Key Strengths & Growth Drivers (Pros)</b>", sec_header_style))
    story.append(Spacer(1, 3))
    pros_rows = []
    for p in c_pros:
        pros_rows.append([
            Paragraph("<b>[+]</b>", ParagraphStyle('PBullet', parent=bullet_pro_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#276749'))),
            Paragraph(p, bullet_pro_style)
        ])
    pros_table = Table(pros_rows, colWidths=[22, 525])
    pros_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0FFF4')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#C6F6D5')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(pros_table)
    story.append(Spacer(1, 6))

    # Cons Section Table
    story.append(Paragraph("<b>Risk Factors & Key Concerns (Cons)</b>", sec_header_style))
    story.append(Spacer(1, 3))
    cons_rows = []
    for c in c_cons:
        cons_rows.append([
            Paragraph("<b>[-]</b>", ParagraphStyle('CBullet', parent=bullet_con_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#9B2C2C'))),
            Paragraph(c, bullet_con_style)
        ])
    cons_table = Table(cons_rows, colWidths=[22, 525])
    cons_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF5F5')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#FED7D7')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(cons_table)

    # Build PDF using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return True, "Success"


def run_batch_tearsheets(db_path=None, output_dir=None):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if db_path is None:
        db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    if output_dir is None:
        output_dir = os.path.join(base_dir, 'reports', 'tearsheets')
    os.makedirs(output_dir, exist_ok=True)

    # Load pros/cons and cash flow intelligence
    pc_path = os.path.join(base_dir, 'output', 'pros_cons_generated.csv')
    pros_cons_df = pd.read_csv(pc_path) if os.path.exists(pc_path) else None

    cf_intel_path = os.path.join(base_dir, 'output', 'cashflow_intelligence.xlsx')
    cap_alloc_df = pd.read_excel(cf_intel_path) if os.path.exists(cf_intel_path) else None

    with sqlite3.connect(db_path) as conn:
        companies = pd.read_sql('SELECT id, company_name FROM companies ORDER BY id', conn)

    generated_count = 0
    skipped_records = []

    print(f"Starting batch tearsheet generation for {len(companies)} companies...")

    for idx, row in companies.iterrows():
        cid = row['id']
        out_pdf = os.path.join(output_dir, f"{cid}_tearsheet.pdf")
        success, msg = generate_company_tearsheet(cid, db_path, out_pdf, pros_cons_df, cap_alloc_df)
        if success:
            file_size_kb = os.path.getsize(out_pdf) / 1024.0
            generated_count += 1
            if idx < 5 or idx % 20 == 0:
                print(f"[{generated_count}] {cid}: {file_size_kb:.1f} KB -> {out_pdf}")
        else:
            skipped_records.append({'company_id': cid, 'company_name': row['company_name'], 'reason': msg})
            print(f"SKIPPED {cid}: {msg}")

    # Log skipped tickers
    skipped_df = pd.DataFrame(skipped_records)
    skipped_path = os.path.join(base_dir, 'output', 'skipped_tearsheets.csv')
    skipped_df.to_csv(skipped_path, index=False)
    print(f"\nBatch Completed: {generated_count} tearsheets generated, {len(skipped_df)} skipped.")
    print(f"Skipped log saved to {skipped_path}")

    return generated_count, skipped_df

if __name__ == '__main__':
    run_batch_tearsheets()
