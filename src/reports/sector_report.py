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

class SectorNumberedCanvas(canvas.Canvas):
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
        self.drawString(24, 15, "Nifty 100 Financial Intelligence Platform  |  Sector Intelligence Brief")
        self.restoreState()


def generate_sector_report(group_name, db_path, output_pdf):
    conn = sqlite3.connect(db_path)
    peers_df = pd.read_sql('SELECT * FROM peer_groups WHERE peer_group_name = ?', conn, params=[group_name])
    companies = pd.read_sql('SELECT id, company_name FROM companies', conn)
    ratios = pd.read_sql('SELECT * FROM financial_ratios', conn)
    mc = pd.read_sql('SELECT * FROM market_cap', conn)
    conn.close()

    if peers_df.empty:
        raise ValueError(f"Peer group {group_name} has no constituents.")

    cids = peers_df['company_id'].unique().tolist()
    ratios['year_dt'] = pd.to_datetime(ratios['year'].astype(str))
    mc['year_dt'] = pd.to_datetime(mc['year'].astype(str))

    # Compile 8 metrics for each company (latest year)
    data_rows = []
    for cid in cids:
        c_r = ratios[ratios['company_id'] == cid].sort_values('year_dt')
        c_mc = mc[mc['company_id'] == cid].sort_values('year_dt')
        c_name = companies[companies['id'] == cid]['company_name'].iloc[0] if cid in companies['id'].values else cid

        lat_r = c_r.iloc[-1] if not c_r.empty else {}
        lat_mc = c_mc.iloc[-1] if not c_mc.empty else {}

        mcap = lat_mc.get('market_cap_crore')
        pe = lat_mc.get('pe_ratio')
        pb = lat_mc.get('pb_ratio')
        roe = lat_r.get('return_on_equity_pct')
        roce = lat_r.get('return_on_capital_pct')
        de = lat_r.get('debt_to_equity')
        opm = lat_r.get('operating_profit_margin_pct')
        cagr = lat_r.get('revenue_cagr_5yr')

        data_rows.append({
            'company_id': cid,
            'company_name': c_name,
            'market_cap': mcap,
            'pe_ratio': pe,
            'pb_ratio': pb,
            'roe': roe,
            'roce': roce,
            'de': de,
            'opm': opm,
            'rev_cagr_5yr': cagr
        })

    df = pd.DataFrame(data_rows)

    # Compute Medians
    med_mcap = df['market_cap'].median()
    med_pe = df['pe_ratio'].median()
    med_pb = df['pb_ratio'].median()
    med_roe = df['roe'].median()
    med_roce = df['roce'].median()
    med_de = df['de'].median()
    med_opm = df['opm'].median()
    med_cagr = df['rev_cagr_5yr'].median()

    # Document setup
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
        'SecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.white
    )

    header_sub_style = ParagraphStyle(
        'SecSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#E2E8F0')
    )

    tile_label = ParagraphStyle(
        'TileL',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor('#718096')
    )

    tile_val = ParagraphStyle(
        'TileV',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11.5,
        textColor=colors.HexColor('#1A365D')
    )

    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.5,
        leading=8,
        textColor=colors.white,
        alignment=1
    )

    td_style = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor('#2D3748'),
        alignment=1
    )

    td_bold = ParagraphStyle(
        'TDBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor('#1A365D'),
        alignment=0
    )

    story = []

    # Navy Header Banner
    header_content = [
        [
            Paragraph(f"<b>SECTOR INTELLIGENCE REPORT: {group_name.upper()}</b>", header_title_style),
            Paragraph(f"Constituents: <b>{len(df)} Companies</b>  |  Nifty 100 Index", header_sub_style)
        ]
    ]
    header_table = Table(header_content, colWidths=[330, 217])
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

    # Median KPI Tiles (2 rows of 4)
    med_tiles = [
        [
            [Paragraph("MEDIAN MARKET CAP", tile_label), Paragraph(f"₹{med_mcap:,.0f} Cr" if pd.notna(med_mcap) else "N/A", tile_val)],
            [Paragraph("MEDIAN P/E RATIO", tile_label), Paragraph(f"{med_pe:.1f}x" if pd.notna(med_pe) else "N/A", tile_val)],
            [Paragraph("MEDIAN P/B RATIO", tile_label), Paragraph(f"{med_pb:.2f}x" if pd.notna(med_pb) else "N/A", tile_val)],
            [Paragraph("MEDIAN ROE", tile_label), Paragraph(f"{med_roe:.1f}%" if pd.notna(med_roe) else "N/A", tile_val)],
        ],
        [
            [Paragraph("MEDIAN ROCE", tile_label), Paragraph(f"{med_roce:.1f}%" if pd.notna(med_roce) else "N/A", tile_val)],
            [Paragraph("MEDIAN D/E RATIO", tile_label), Paragraph(f"{med_de:.2f}x" if pd.notna(med_de) else "N/A", tile_val)],
            [Paragraph("MEDIAN OPM", tile_label), Paragraph(f"{med_opm:.1f}%" if pd.notna(med_opm) else "N/A", tile_val)],
            [Paragraph("MEDIAN 5Y REV CAGR", tile_label), Paragraph(f"{med_cagr:.1f}%" if pd.notna(med_cagr) else "N/A", tile_val)],
        ]
    ]
    med_table = Table(med_tiles, colWidths=[136, 136, 136, 139], rowHeights=[24, 24])
    med_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EDF2F7')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(med_table)
    story.append(Spacer(1, 10))

    # Comparative Table of all Constituents across 8 metrics
    story.append(Paragraph(f"<b>Constituent Comparison (8 Core Metrics) — {group_name}</b>", ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=10, textColor=colors.HexColor('#1A365D'))))
    story.append(Spacer(1, 4))

    table_data = [[
        Paragraph("Ticker", th_style),
        Paragraph("Company Name", th_style),
        Paragraph("M.Cap (Cr)", th_style),
        Paragraph("P/E", th_style),
        Paragraph("P/B", th_style),
        Paragraph("ROE (%)", th_style),
        Paragraph("ROCE (%)", th_style),
        Paragraph("D/E", th_style),
        Paragraph("OPM (%)", th_style),
        Paragraph("5Y Rev CAGR", th_style),
    ]]

    # Sort constituents by market cap descending
    df_sorted = df.sort_values(by='market_cap', ascending=False)
    for _, r in df_sorted.iterrows():
        m_str = f"₹{r['market_cap']:,.0f}" if pd.notna(r['market_cap']) else "-"
        pe_str = f"{r['pe_ratio']:.1f}" if pd.notna(r['pe_ratio']) else "-"
        pb_str = f"{r['pb_ratio']:.2f}" if pd.notna(r['pb_ratio']) else "-"
        roe_str = f"{r['roe']:.1f}%" if pd.notna(r['roe']) else "-"
        roce_str = f"{r['roce']:.1f}%" if pd.notna(r['roce']) else "-"
        de_str = f"{r['de']:.2f}" if pd.notna(r['de']) else "-"
        opm_str = f"{r['opm']:.1f}%" if pd.notna(r['opm']) else "-"
        cagr_str = f"{r['rev_cagr_5yr']:.1f}%" if pd.notna(r['rev_cagr_5yr']) else "-"

        table_data.append([
            Paragraph(r['company_id'], td_bold),
            Paragraph(r['company_name'][:24], ParagraphStyle('TDL', parent=td_style, alignment=0)),
            Paragraph(m_str, td_style),
            Paragraph(pe_str, td_style),
            Paragraph(pb_str, td_style),
            Paragraph(roe_str, td_style),
            Paragraph(roce_str, td_style),
            Paragraph(de_str, td_style),
            Paragraph(opm_str, td_style),
            Paragraph(cagr_str, td_style),
        ])

    comp_table = Table(table_data, colWidths=[48, 115, 56, 36, 36, 46, 46, 36, 46, 52])
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for row_idx in range(1, len(table_data)):
        bg = colors.HexColor('#FFFFFF') if row_idx % 2 == 1 else colors.HexColor('#F7FAFC')
        t_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg))

    comp_table.setStyle(TableStyle(t_style))
    story.append(comp_table)

    doc.build(story, canvasmaker=SectorNumberedCanvas)
    return True


def run_batch_sector_reports(db_path=None, output_dir=None):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if db_path is None:
        db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    if output_dir is None:
        output_dir = os.path.join(base_dir, 'reports', 'sector')
    os.makedirs(output_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    groups = pd.read_sql('SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name', conn)['peer_group_name'].tolist()
    conn.close()

    print(f"Generating 11 Sector PDF reports in {output_dir}...")
    generated = 0
    for g in groups:
        clean_name = g.replace(' ', '_').replace('/', '_')
        out_pdf = os.path.join(output_dir, f"{clean_name}_report.pdf")
        generate_sector_report(g, db_path, out_pdf)
        generated += 1
        print(f"[{generated}/11] Generated sector PDF: {out_pdf}")

    return generated

if __name__ == '__main__':
    run_batch_sector_reports()
