from __future__ import annotations

import logging
from collections import Counter
from os import PathLike
from typing import Any

import pdfplumber

from .fonts import nominal_size, parse_fontname
from .spec import STORED, FontRun, PageSize, Reading, StyleSpec

# pdfminer warns about every Type 3 font without a FontBBox, and browser-made PDFs carry dozens. A null
# handler keeps that off stderr when the application has not configured logging; an application that has
# still receives the warnings through propagation.
logging.getLogger("pdfminer").addHandler(logging.NullHandler())


def read(path: str | PathLike[str], page_number: int = 1) -> StyleSpec:
    """Read the style of one page, counted from 1."""
    with pdfplumber.open(path) as pdf:
        if not 1 <= page_number <= len(pdf.pages):
            raise ValueError(f"page {page_number} does not exist; the file has {len(pdf.pages)} page(s)")
        page = pdf.pages[page_number - 1]
        size = PageSize(float(page.width), float(page.height))
        chars = [c for c in page.chars if c["text"].strip()]
        fonts = _font_runs(chars)
    evidence = f"page {page_number} box as stored: {size.width_pt:g} x {size.height_pt:g} pt"
    return StyleSpec(page=Reading(size, STORED, evidence), fonts=fonts)


def _font_runs(chars: list[dict[str, Any]]) -> Reading[list[FontRun]]:
    counts = Counter((c["fontname"], round(float(c["size"]), 2)) for c in chars)
    total = sum(counts.values())
    if not total:
        return Reading([], STORED, "no text on the page")
    runs: list[FontRun] = []
    confidences: list[float] = []
    for (name, size), n in counts.most_common():
        parsed = parse_fontname(name)
        confidences.append(parsed.confidence)
        runs.append(
            FontRun(
                fontname=name,
                size_pt=size,
                chars=n,
                share=round(n / total, 4),
                subset_tag=parsed.subset_tag,
                family=parsed.family,
                weight=parsed.weight,
                italic=parsed.italic,
                nominal_pt=nominal_size(size),
            )
        )
    evidence = (
        f"{total} characters in {len(counts)} font-size pairs, whitespace excluded; "
        "names parsed by convention with subset tags removed; sizes from the text matrix"
    )
    return Reading(runs, min(confidences), evidence)
