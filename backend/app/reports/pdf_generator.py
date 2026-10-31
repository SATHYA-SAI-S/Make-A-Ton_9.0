"""
PDF Report Generator for SubscriptIQ using ReportLab.
Produces professional financial packs, revenue summaries, and accounting reports.
"""
import io
from typing import List, Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_report_pdf(
    title: str,
    subtitle: str,
    headers: List[str],
    rows: List[List[str]],
    summary_kpis: Optional[Dict[str, str]] = None,
    orientation: str = "landscape"
) -> bytes:
    """
    Generates a structured, professional PDF document from tabular report data.
    """
    buffer = io.BytesIO()
    page_size = landscape(letter) if orientation == "landscape" else letter
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )
    header_cell_style = ParagraphStyle(
        'HeaderCellText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )

    story = []

    # 1. Header & Title
    story.append(Paragraph(f"SubscriptIQ — {title}", title_style))
    story.append(Paragraph(subtitle, subtitle_style))
    story.append(Spacer(1, 8))

    # 2. KPI Summary Grid (if provided)
    if summary_kpis:
        kpi_data = []
        labels = list(summary_kpis.keys())
        vals = list(summary_kpis.values())
        kpi_data.append([Paragraph(f"<b>{k}</b>", cell_style) for k in labels])
        kpi_data.append([Paragraph(v, cell_style) for v in vals])

        kpi_table = Table(kpi_data, hAlign='LEFT')
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 14))

    # 3. Main Data Table
    table_data = []
    # Header row
    table_data.append([Paragraph(h, header_cell_style) for h in headers])

    # Truncate rows if too many to prevent memory overflow (e.g. max 500 rows for PDF pack)
    for r in rows[:500]:
        table_data.append([Paragraph(str(c), cell_style) for c in r])

    main_table = Table(table_data, repeatRows=1, hAlign='LEFT')
    main_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    story.append(main_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
