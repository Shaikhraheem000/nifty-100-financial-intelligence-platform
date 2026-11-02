import os
import pypdf
import pytest

def test_tearsheets_batch():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    tearsheets_dir = os.path.join(base_dir, 'reports', 'tearsheets')
    skipped_file = os.path.join(base_dir, 'output', 'skipped_tearsheets.csv')

    assert os.path.exists(tearsheets_dir)
    assert os.path.exists(skipped_file)

    files = [f for f in os.listdir(tearsheets_dir) if f.endswith('.pdf')]
    assert len(files) == 92, f"Expected 92 company tearsheet PDFs, got {len(files)}"

    # Check each file size >= 30 KB
    for f in files:
        fpath = os.path.join(tearsheets_dir, f)
        size_kb = os.path.getsize(fpath) / 1024.0
        assert size_kb >= 30.0, f"{f} is smaller than 30 KB ({size_kb:.1f} KB)"

    # Verify 5 samples have exactly 2 pages
    for f in files[:5]:
        reader = pypdf.PdfReader(os.path.join(tearsheets_dir, f))
        assert len(reader.pages) == 2, f"{f} has {len(reader.pages)} pages instead of 2"

def test_sector_reports_batch():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sector_dir = os.path.join(base_dir, 'reports', 'sector')

    assert os.path.exists(sector_dir)
    files = [f for f in os.listdir(sector_dir) if f.endswith('.pdf')]
    assert len(files) == 11, f"Expected 11 sector PDF reports, got {len(files)}"

def test_portfolio_summary_report():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    summary_pdf = os.path.join(base_dir, 'reports', 'portfolio', 'portfolio_summary.pdf')

    assert os.path.exists(summary_pdf)
    size_kb = os.path.getsize(summary_pdf) / 1024.0
    assert size_kb >= 30.0

    reader = pypdf.PdfReader(summary_pdf)
    assert len(reader.pages) == 92, f"Expected 92 pages in portfolio summary, got {len(reader.pages)}"
