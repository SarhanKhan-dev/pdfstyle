from __future__ import annotations

import logging
from collections import Counter
from os import PathLike
from typing import Any

import pdfplumber

from .fonts import nominal_size, parse_fontname
from .spec import STORED, FontRun, PageSize, Reading, StyleSpec

# pdfminer logs a warning for every Type 3 font without a FontBBox; keep that quiet unless the app set up logging
logging.getLogger("pdfminer").addHandler(logging.NullHandler())


def read(path: str | PathLike[str], page_number: int = 1) -> StyleSpec:
    """Read one page (1-based)."""
    with pdfplumber.open(path) as pdf:
        if not 1 <= page_number <= len(pdf.pages):
            raise ValueError(f"page {page_number} does not exist, the file has {len(pdf.pages)} page(s)")
        page = pdf.pages[page_number - 1]
        size = PageSize(float(page.width), float(page.height))
        chars = [c for c in page.chars if c["text"].strip()]
        fonts = _font_runs(chars)
    evidence = f"page {page_number} box, {size.width_pt:g} x {size.height_pt:g} pt"
    return StyleSpec(page=Reading(size, STORED, evidence), fonts=fonts)


def _font_runs(chars: list[dict[str, Any]]) -> Reading[list[FontRun]]:
    counts = Counter((c["fontname"], round(float(c["size"]), 2)) for c in chars)
    total = sum(counts.values())
    if not total:
        return Reading([], STORED, "no text")
    runs: list[FontRun] = []
    confidence = 1.0
    for (name, size), n in counts.most_common():
        p = parse_fontname(name)
        confidence = min(confidence, p.confidence)
        runs.append(
            FontRun(name, size, n, round(n / total, 4), p.subset_tag, p.family, p.weight, p.italic, nominal_size(size))
        )
    return Reading(runs, confidence, f"{total} non-space chars grouped by font and size")
