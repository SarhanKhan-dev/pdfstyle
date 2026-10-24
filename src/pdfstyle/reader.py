from __future__ import annotations

from os import PathLike

import pdfplumber

from .spec import STORED, PageSize, Reading, StyleSpec


def read(path: str | PathLike[str], page_number: int = 1) -> StyleSpec:
    """Read the style of one page, counted from 1. Page size only, so far."""
    with pdfplumber.open(path) as pdf:
        if not 1 <= page_number <= len(pdf.pages):
            raise ValueError(f"page {page_number} does not exist; the file has {len(pdf.pages)} page(s)")
        page = pdf.pages[page_number - 1]
        size = PageSize(float(page.width), float(page.height))
    evidence = f"page {page_number} box as stored: {size.width_pt:g} x {size.height_pt:g} pt"
    return StyleSpec(page=Reading(size, STORED, evidence))
