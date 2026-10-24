"""The style spec: what pdfstyle reports about a page.

Every field is a Reading: the value, a confidence, and the evidence it came from. The one rule of
confidence: 1.0 is reserved for values the file stores as such (STORED). Anything inferred must be
reported lower, so a caller can always tell a fact from a judgement.
"""

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
        """The standard paper name this size matches within one point, in either orientation."""
        short, long = sorted((self.width_pt, self.height_pt))
        for name, (w, h) in PAPER_SIZES_PT.items():
            if abs(short - w) <= 1.0 and abs(long - h) <= 1.0:
                return name
        return None


@dataclass
class StyleSpec:
    page: Reading[PageSize]

    def to_dict(self) -> dict[str, Any]:
        size = self.page.value
        return {
            "page": {
                "value": {**asdict(size), "paper": size.paper, "landscape": size.landscape},
                "confidence": self.page.confidence,
                "evidence": self.page.evidence,
            }
        }
