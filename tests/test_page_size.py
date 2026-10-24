"""Ground truth by construction: the test builds the PDF, so the expected numbers are known first."""

import pytest
from fpdf import FPDF

from pdfstyle import read


def make_pdf(path, fmt, orientation="P"):
    pdf = FPDF(orientation=orientation, unit="pt", format=fmt)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="ground truth by construction")
    pdf.output(str(path))
    return path


@pytest.mark.parametrize(
    ("fmt", "orientation", "width", "height", "paper"),
    [
        ("A4", "P", 595.28, 841.89, "A4"),
        ("A4", "L", 841.89, 595.28, "A4"),
        ("Letter", "P", 612.0, 792.0, "Letter"),
        ((300, 500), "P", 300.0, 500.0, None),
    ],
)
def test_page_size_is_read_as_stored(tmp_path, fmt, orientation, width, height, paper):
    spec = read(make_pdf(tmp_path / "t.pdf", fmt, orientation))
    assert spec.page.value.width_pt == pytest.approx(width, abs=0.005)
    assert spec.page.value.height_pt == pytest.approx(height, abs=0.005)
    assert spec.page.value.paper == paper
    assert spec.page.value.landscape is (orientation == "L")
    assert spec.page.confidence == 1.0


def test_missing_page_is_an_error(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        read(make_pdf(tmp_path / "t.pdf", "A4"), page_number=2)


def test_to_dict_is_json_shaped(tmp_path):
    d = read(make_pdf(tmp_path / "t.pdf", "A4")).to_dict()
    assert d["page"]["value"]["paper"] == "A4"
    assert d["page"]["confidence"] == 1.0
    assert "pt" in d["page"]["evidence"]
