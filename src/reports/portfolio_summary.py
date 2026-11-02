import os
import sqlite3
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.pdfgen import canvas

class PortfolioNumberedCanvas(canvas.Canvas):
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
        self.drawString(24, 15, "Nifty 100 Portfolio Summary Compendium  |  Annual Performance Review")
        self.restoreState()


def get_trend_indicator(curr_val, prev_val, higher_is_better=True):
    if pd.isna(curr_val) or pd.isna(prev_val) or prev_val == 0:
        return "N/A", colors.HexColor('#718096'), "►"

    pct_change = ((curr_val - prev_val) / abs(prev_val)) * 100.0

    if abs(pct_change) <= 2.0:
        return f"{pct_change:+.1f}% (Flat)", colors.HexColor('#4A5568'), "►"

    if higher_is_better:
        if pct_change > 2.0:
            return f"{pct_change:+.1f}% (Improved)", colors.HexColor('#22543D'), "▲"
        else:
            return f"{pct_change:+.1f}% (Declined)", colors.HexColor('#742A2A'), "▼"
    else:
        # Lower is better (e.g. Debt/Equity)
        if pct_change < -2.0:
            return f"{pct_change:+.1f}% (Improved)", colors.HexColor('#22543D'), "▲"
        else:
            return f"{pct_change:+.1f}% (Declined)", colors.HexColor('#742A2A'), "▼"


def generate_portfolio_summary(db_path=None, output_pdf=None):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if db_path is None:
        db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    if output_pdf is None:
        output_pdf = os.path.join(base_dir, 'reports', 'portfolio', 'portfolio_summary.pdf')
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    conn = sqlite3.connect(db_path)
    companies = pd.read_sql('SELECT id, company_name FROM companies ORDER BY id ASC', conn)
    ratios = pd.read_sql('SELECT * FROM financial_ratios', conn)
    pl = pd.read_sql('SELECT * FROM profitandloss', conn)
    mc = pd.read_sql('SELECT * FROM market_cap', conn)
    sectors = pd.read_sql('SELECT * FROM sectors', conn)
    conn.close()

    ratios['year_dt'] = pd.to_datetime(ratios['year'].astype(str))
    pl['year_dt'] = pd.to_datetime(pl['year'].astype(str))
    mc['year_dt'] = pd.to_datetime(mc['year'].astype(str))

    sectors_map = sectors.set_index('company_id')['broad_sector'].to_dict()
    subsectors_map = sectors.set_index('company_id')['sub_sector'].to_dict()

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
        'PortTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=15,
        textColor=colors.white
    )

    header_sub_style = ParagraphStyle(
        'PortSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#E2E8F0')
    )

    card_header = ParagraphStyle(
        'CardH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1A365D')
    )

    th_style = ParagraphStyle(
        'THP',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )

    td_style = ParagraphStyle(
        'TDP',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#2D3748'),
        alignment=1
    )

    story = []

    print(f"Generating portfolio summary PDF for {len(companies)} companies...")

    for idx, row in companies.iterrows():
        cid = row['id']
        cname = row['company_name']
        sec = sectors_map.get(cid, 'N/A')
        subsec = subsectors_map.get(cid, 'N/A')

        c_r = ratios[ratios['company_id'] == cid].sort_values('year_dt')
        c_pl = pl[pl['company_id'] == cid].sort_values('year_dt')
        c_mc = mc[mc['company_id'] == cid].sort_values('year_dt')

        # Extract latest and previous values for top 6 KPIs
        # 1. Revenue
        if len(c_pl) >= 2:
            rev_curr = c_pl.iloc[-1]['sales']
            rev_prev = c_pl.iloc[-2]['sales']
        elif len(c_pl) == 1:
            rev_curr = c_pl.iloc[-1]['sales']
            rev_prev = None
        else:
            rev_curr, rev_prev = None, None

        # 2. Net Profit
        if len(c_pl) >= 2:
            pat_curr = c_pl.iloc[-1]['net_profit']
            pat_prev = c_pl.iloc[-2]['net_profit']
        elif len(c_pl) == 1:
            pat_curr = c_pl.iloc[-1]['net_profit']
            pat_prev = None
        else:
            pat_curr, pat_prev = None, None

        # 3. OPM
        if len(c_r) >= 2:
            opm_curr = c_r.iloc[-1]['operating_profit_margin_pct']
            opm_prev = c_r.iloc[-2]['operating_profit_margin_pct']
        elif len(c_r) == 1:
            opm_curr = c_r.iloc[-1]['operating_profit_margin_pct']
            opm_prev = None
        else:
            opm_curr, opm_prev = None, None

        # 4. ROE
        if len(c_r) >= 2:
            roe_curr = c_r.iloc[-1]['return_on_equity_pct']
            roe_prev = c_r.iloc[-2]['return_on_equity_pct']
        elif len(c_r) == 1:
            roe_curr = c_r.iloc[-1]['return_on_equity_pct']
            roe_prev = None
        else:
            roe_curr, roe_prev = None, None

        # 5. ROCE
        if len(c_r) >= 2:
            roce_curr = c_r.iloc[-1]['return_on_capital_pct']
            roce_prev = c_r.iloc[-2]['return_on_capital_pct']
        elif len(c_r) == 1:
            roce_curr = c_r.iloc[-1]['return_on_capital_pct']
            roce_prev = None
        else:
            roce_curr, roce_prev = None, None

        # 6. D/E
        if len(c_r) >= 2:
            de_curr = c_r.iloc[-1]['debt_to_equity']
            de_prev = c_r.iloc[-2]['debt_to_equity']
        elif len(c_r) == 1:
            de_curr = c_r.iloc[-1]['debt_to_equity']
            de_prev = None
        else:
            de_curr, de_prev = None, None

        # Format rows for Top 6 KPIs
        kpis = [
            ("Revenue (Sales)", f"₹{rev_curr:,.0f} Cr" if pd.notna(rev_curr) else "N/A", f"₹{rev_prev:,.0f} Cr" if pd.notna(rev_prev) else "N/A", get_trend_indicator(rev_curr, rev_prev, True)),
            ("Net Profit (PAT)", f"₹{pat_curr:,.0f} Cr" if pd.notna(pat_curr) else "N/A", f"₹{pat_prev:,.0f} Cr" if pd.notna(pat_prev) else "N/A", get_trend_indicator(pat_curr, pat_prev, True)),
            ("Operating Margin (OPM)", f"{opm_curr:.1f}%" if pd.notna(opm_curr) else "N/A", f"{opm_prev:.1f}%" if pd.notna(opm_prev) else "N/A", get_trend_indicator(opm_curr, opm_prev, True)),
            ("Return on Equity (ROE)", f"{roe_curr:.1f}%" if pd.notna(roe_curr) else "N/A", f"{roe_prev:.1f}%" if pd.notna(roe_prev) else "N/A", get_trend_indicator(roe_curr, roe_prev, True)),
            ("Return on Capital (ROCE)", f"{roce_curr:.1f}%" if pd.notna(roce_curr) else "N/A", f"{roce_prev:.1f}%" if pd.notna(roce_prev) else "N/A", get_trend_indicator(roce_curr, roce_prev, True)),
            ("Debt to Equity (D/E)", f"{de_curr:.2f}x" if pd.notna(de_curr) else "N/A", f"{de_prev:.2f}x" if pd.notna(de_prev) else "N/A", get_trend_indicator(de_curr, de_prev, False)),
        ]

        # Page Header Banner
        header_table = Table([
            [
                Paragraph(f"<b>{cname}</b> ({cid})", header_title_style),
                Paragraph(f"Sector: <b>{sec}</b>  |  Sub-Sector: <b>{subsec}</b>", header_sub_style)
            ]
        ], colWidths=[280, 267])
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
        story.append(Spacer(1, 12))

        # KPI Table Header
        story.append(Paragraph("<b>Core Financial Indicators & Directional Trend Tracking</b>", card_header))
        story.append(Spacer(1, 6))

        table_rows = [[
            Paragraph("Core KPI Metric", th_style),
            Paragraph("Latest Period", th_style),
            Paragraph("Prior Period", th_style),
            Paragraph("Trend Arrow", th_style),
            Paragraph("YoY Direction & Signal", th_style),
        ]]

        for metric_name, val_curr, val_prev, (text_desc, col_tag, arrow) in kpis:
            arrow_style = ParagraphStyle(
                f'Arr_{metric_name}',
                parent=td_style,
                fontName='Helvetica-Bold',
                fontSize=11,
                textColor=col_tag
            )
            desc_style = ParagraphStyle(
                f'Desc_{metric_name}',
                parent=td_style,
                fontName='Helvetica-Bold',
                textColor=col_tag
            )
            table_rows.append([
                Paragraph(f"<b>{metric_name}</b>", ParagraphStyle('MetricName', parent=td_style, alignment=0)),
                Paragraph(val_curr, td_style),
                Paragraph(val_prev, td_style),
                Paragraph(arrow, arrow_style),
                Paragraph(text_desc, desc_style),
            ])

        kpi_table = Table(table_rows, colWidths=[150, 95, 95, 65, 142], rowHeights=[22] + [25]*6)
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]
        for r_i in range(1, len(table_rows)):
            bg = colors.HexColor('#FFFFFF') if r_i % 2 == 1 else colors.HexColor('#F7FAFC')
            t_style.append(('BACKGROUND', (0, r_i), (-1, r_i), bg))

        kpi_table.setStyle(TableStyle(t_style))
        story.append(kpi_table)
        story.append(Spacer(1, 14))

        # Recent 5-Year History Table
        story.append(Paragraph("<b>Five-Year Historical Metric Synopsis</b>", card_header))
        story.append(Spacer(1, 6))

        hist_head = [Paragraph("Year", th_style), Paragraph("Sales (Cr)", th_style), Paragraph("PAT (Cr)", th_style), Paragraph("ROE (%)", th_style), Paragraph("ROCE (%)", th_style), Paragraph("D/E", th_style)]
        hist_rows = [hist_head]

        recent_pl = c_pl.tail(5)
        for _, pl_r in recent_pl.iterrows():
            yr_str = str(pl_r['year'])[:7]
            s_val = f"₹{pl_r['sales']:,.0f}" if pd.notna(pl_r.get('sales')) else "-"
            p_val = f"₹{pl_r['net_profit']:,.0f}" if pd.notna(pl_r.get('net_profit')) else "-"
            # Find matching ratio row
            r_match = c_r[c_r['year'].astype(str).str[:4] == yr_str[:4]]
            if not r_match.empty:
                lat_match = r_match.iloc[-1]
                roe_m = f"{lat_match['return_on_equity_pct']:.1f}%" if pd.notna(lat_match.get('return_on_equity_pct')) else "-"
                roce_m = f"{lat_match['return_on_capital_pct']:.1f}%" if pd.notna(lat_match.get('return_on_capital_pct')) else "-"
                de_m = f"{lat_match['debt_to_equity']:.2f}" if pd.notna(lat_match.get('debt_to_equity')) else "-"
            else:
                roe_m, roce_m, de_m = "-", "-", "-"

            hist_rows.append([
                Paragraph(yr_str, td_style),
                Paragraph(s_val, td_style),
                Paragraph(p_val, td_style),
                Paragraph(roe_m, td_style),
                Paragraph(roce_m, td_style),
                Paragraph(de_m, td_style),
            ])

        hist_table = Table(hist_rows, colWidths=[77, 94, 94, 94, 94, 94])
        h_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D3748')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        for r_i in range(1, len(hist_rows)):
            bg = colors.HexColor('#FFFFFF') if r_i % 2 == 1 else colors.HexColor('#F7FAFC')
            h_style.append(('BACKGROUND', (0, r_i), (-1, r_i), bg))
        hist_table.setStyle(TableStyle(h_style))
        story.append(hist_table)

        # Force page break for each company (except after last company)
        if idx < len(companies) - 1:
            story.append(PageBreak())

    doc.build(story, canvasmaker=PortfolioNumberedCanvas)
    print(f"Generated Portfolio Summary PDF at: {output_pdf}")
    return output_pdf

if __name__ == '__main__':
    generate_portfolio_summary()
