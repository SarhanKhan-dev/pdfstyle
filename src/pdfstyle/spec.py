"""What pdfstyle reports about a page. Every field is a Reading with a confidence and its evidence:
1.0 means read from the file as stored, anything inferred is lower."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")

STORED = 1.0

PAPER_SIZES_PT = {
    "A3": (841.89, 1190.55),
    "A4": (595.28, 841.89),
    "A5": (419.53, 595.28),
    "Letter": (612.0, 792.0),
    "Legal": (612.0, 1008.0),
    "Tabloid": (792.0, 1224.0),
}


@dataclass(frozen=True)
class Reading(Generic[T]):
    value: T
    confidence: float
    evidence: str


@dataclass(frozen=True)
class PageSize:
    width_pt: float
    height_pt: float

    @property
    def landscape(self) -> bool:
        return self.width_pt > self.height_pt

    @property
    def paper(self) -> str | None:
        short, long = sorted((self.width_pt, self.height_pt))
        for name, (w, h) in PAPER_SIZES_PT.items():
            if abs(short - w) <= 1.0 and abs(long - h) <= 1.0:
                return name
        return None


@dataclass(frozen=True)
class FontRun:
    """One font at one size. fontname, size_pt, chars, share and subset_tag are as stored;
    family, weight and italic are parsed from the name; nominal_pt is the snapped size, or None."""

    fontname: str
    size_pt: float
    chars: int
    share: float
    subset_tag: str | None
    family: str
    weight: int
    italic: bool
    nominal_pt: float | None


@dataclass
class StyleSpec:
    page: Reading[PageSize]
    fonts: Reading[list[FontRun]]

    def to_dict(self) -> dict[str, Any]:
        size = self.page.value
        return {
            "page": _reading({**asdict(size), "paper": size.paper, "landscape": size.landscape}, self.page),
            "fonts": _reading([asdict(run) for run in self.fonts.value], self.fonts),
        }


def _reading(value: Any, reading: Reading[Any]) -> dict[str, Any]:
    return {"value": value, "confidence": reading.confidence, "evidence": reading.evidence}
