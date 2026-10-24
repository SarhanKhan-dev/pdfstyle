"""Font names are conventions; the parsing table below holds names seen from real producers
(core fonts, fpdf2, Word, Chromium, Monotype). The page test builds its own PDF."""

from pathlib import Path

import pytest
from fpdf import FPDF

from pdfstyle import read
from pdfstyle.fonts import nominal_size, parse_fontname

TRUETYPE_CANDIDATES = [
    r"C:\Windows\Fonts\calibri.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
]


@pytest.mark.parametrize(
    ("stored", "family", "weight", "italic", "tag"),
    [
        ("Helvetica", "Helvetica", 400, False, None),
        ("Times-Roman", "Times", 400, False, None),
        ("Times-Bold", "Times", 700, False, None),
        ("Helvetica-BoldOblique", "Helvetica", 700, True, None),
        ("MPDFAA+Calibri", "Calibri", 400, False, "MPDFAA"),
        ("MPDFAA+CalibriBold", "Calibri", 700, False, "MPDFAA"),
        ("BCDEEE+NirmalaText", "NirmalaText", 400, False, "BCDEEE"),
        ("BCDFEE+NirmalaText-Bold", "NirmalaText", 700, False, "BCDFEE"),
        ("BCDGEE+Avenir Next LT Pro Light", "Avenir Next LT Pro", 300, False, "BCDGEE"),
        ("BCDLEE+Avenir Next LT Pro Light,Italic", "Avenir Next LT Pro", 300, True, "BCDLEE"),
        ("LAAAAA+Nunito-Sans-12pt-ExtraLight-12pt-Normal", "Nunito Sans 12pt", 400, False, "LAAAAA"),
        ("AAAAAA+Nunito-Sans-12pt-ExtraLight-12pt-Normal-ExtraBold", "Nunito Sans 12pt", 800, False, "AAAAAA"),
        ("ArialMT", "Arial", 400, False, None),
        ("Arial-BoldItalicMT", "Arial", 700, True, None),
        ("TimesNewRomanPSMT", "TimesNewRoman", 400, False, None),
        ("Arial,BoldItalic", "Arial", 700, True, None),
    ],
)
def test_font_names_parse_by_convention(stored, family, weight, italic, tag):
    p = parse_fontname(stored)
    assert (p.family, p.weight, p.italic, p.subset_tag) == (family, weight, italic, tag)
    assert p.confidence < 1.0


def test_messy_names_get_lower_confidence():
    messy = parse_fontname("LAAAAA+Nunito-Sans-12pt-ExtraLight-12pt-Normal")
    clean = parse_fontname("Times-Bold")
    assert messy.confidence < clean.confidence
    assert messy.notes


@pytest.mark.parametrize(
    ("stored", "nominal"),
    [(12.96, 13.0), (9.96, 10.0), (11.04, 11.0), (8.52, 8.5), (12.0, 12.0), (9.37, None), (10.87, None)],
)
def test_nominal_size_snaps_only_within_tolerance(stored, nominal):
    assert nominal_size(stored) == nominal


def test_font_runs_from_a_generated_page(tmp_path):
    # fpdf2 names an embedded font after the file's own internal name, not the family it is registered
    # under, so the embedded run is found by its size and checked for a subset tag, never by name.
    ttf = next((p for p in TRUETYPE_CANDIDATES if Path(p).exists()), None)
    texts = {"body": "Body body body body body body", "title": "Title", "heading": "Heading", "meta": "Meta line"}
    pdf = FPDF(unit="pt", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text=texts["body"])
    pdf.ln(20)
    pdf.set_font("Times", style="B", size=17)
    pdf.cell(text=texts["title"])
    pdf.ln(24)
    pdf.set_font("Times", style="B", size=13)
    pdf.cell(text=texts["heading"])
    pdf.ln(20)
    if ttf:
        pdf.add_font("Embedded", fname=ttf)
        pdf.set_font("Embedded", size=11)
        pdf.cell(text=texts["meta"])
    else:
        del texts["meta"]
    path = tmp_path / "fonts.pdf"
    pdf.output(str(path))

    spec = read(path)
    runs = spec.fonts.value

    def one(**want):
        matches = [r for r in runs if all(getattr(r, k) == v for k, v in want.items())]
        assert len(matches) == 1, (want, runs)
        return matches[0]

    body = one(family="Helvetica", size_pt=12.0)
    assert runs[0] is body
    assert (body.weight, body.nominal_pt, body.subset_tag, body.italic) == (400, 12.0, None, False)
    assert one(family="Times", size_pt=17.0).weight == 700
    assert one(family="Times", size_pt=13.0).weight == 700
    assert len(runs) == len(texts)
    assert sum(r.chars for r in runs) == sum(len(t.replace(" ", "")) for t in texts.values())
    assert sum(r.share for r in runs) == pytest.approx(1.0, abs=1e-3)
    assert 0 < spec.fonts.confidence < 1.0
    if ttf:
        meta = one(size_pt=11.0)
        assert meta.subset_tag and len(meta.subset_tag) == 6 and meta.subset_tag.isupper()
        assert meta.weight == 400


def test_blank_page_has_no_fonts(tmp_path):
    pdf = FPDF(unit="pt", format="A4")
    pdf.add_page()
    path = tmp_path / "blank.pdf"
    pdf.output(str(path))
    spec = read(path)
    assert spec.fonts.value == []
    assert spec.fonts.confidence == 1.0
