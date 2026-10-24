"""Parse PDF font resource names into family, weight and slant."""

from __future__ import annotations

import re
from dataclasses import dataclass

SUBSET_TAG = re.compile(r"^([A-Z]{6})\+")
SEPARATORS = re.compile(r"[-,_]+")
FOUNDRY_SUFFIXES = ("PSMT", "MT", "PS")

# longest first, so ExtraBold is not read as Bold
WEIGHT_WORDS = (
    ("ExtraLight", 200),
    ("UltraLight", 200),
    ("ExtraBold", 800),
    ("UltraBold", 800),
    ("SemiBold", 600),
    ("DemiBold", 600),
    ("Hairline", 100),
    ("Regular", 400),
    ("Medium", 500),
    ("Normal", 400),
    ("Light", 300),
    ("Heavy", 900),
    ("Black", 900),
    ("Roman", 400),
    ("Thin", 100),
    ("Bold", 700),
    ("Book", 400),
)
SLANT_WORDS = ("Italic", "Oblique")
# only as a separate word: "Times-Roman" yes, "TimesNewRoman" no
STANDALONE_ONLY = {"Roman", "Book", "Normal"}
STYLE_WORDS = tuple(sorted([w for w, _ in WEIGHT_WORDS] + list(SLANT_WORDS), key=len, reverse=True))
GLUED_WORDS = tuple(w for w in STYLE_WORDS if w not in STANDALONE_ONLY)
_WEIGHT_OF = {w.lower(): n for w, n in WEIGHT_WORDS}
_SLANT = {w.lower() for w in SLANT_WORDS}

SIZE_SNAP_PT = 0.5
SIZE_TOLERANCE_PT = 0.08


@dataclass(frozen=True)
class ParsedFont:
    stored: str
    subset_tag: str | None
    base_name: str
    family: str
    weight: int
    italic: bool
    confidence: float
    notes: tuple[str, ...]


def parse_fontname(stored: str) -> ParsedFont:
    """Names follow producer habits ("Times-Bold", "ABCDEF+CalibriBold", "Arial,BoldItalic",
    "Nunito-Sans-12pt-ExtraLight-12pt-Normal-ExtraBold"), so this is a best guess with a confidence."""
    tag = SUBSET_TAG.match(stored)
    base = stored[tag.end() :] if tag else stored
    tokens = [t for raw in SEPARATORS.sub(" ", base).split() for t in _split_glued(_strip_foundry(raw))]

    family: list[str] = []
    weights: list[int] = []
    italic = False
    stray: list[str] = []
    for t in tokens:
        key = t.lower()
        if key in _WEIGHT_OF:
            weights.append(_WEIGHT_OF[key])
        elif key in _SLANT:
            italic = True
        elif weights or italic:
            stray.append(t)
        else:
            family.append(t)

    notes: list[str] = []
    if stray:
        notes.append("unrecognised words after the style: " + " ".join(stray))
    if len(set(weights)) > 1:
        notes.append("several weight words, last one taken")
    if not family:
        family = [base]
        notes.append("no family word before the style")
    return ParsedFont(
        stored=stored,
        subset_tag=tag.group(1) if tag else None,
        base_name=base,
        family=" ".join(family),
        weight=weights[-1] if weights else 400,
        italic=italic,
        confidence=0.75 if notes else 0.95,
        notes=tuple(notes),
    )


def nominal_size(size_pt: float) -> float | None:
    """Snap to the nearest half point when the stored size is close to one (Word writes 13 pt as 12.96)."""
    snapped = round(size_pt / SIZE_SNAP_PT) * SIZE_SNAP_PT
    return snapped if abs(snapped - size_pt) <= SIZE_TOLERANCE_PT else None


def _strip_foundry(token: str) -> str:
    for suffix in FOUNDRY_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix):
            return token[: -len(suffix)]
    return token


def _split_glued(token: str) -> list[str]:
    # CalibriBold -> Calibri Bold, BoldItalic -> Bold Italic, ExtraBold stays whole
    if token.lower() in _WEIGHT_OF or token.lower() in _SLANT:
        return [token]
    peeled: list[str] = []
    rest = token
    while rest:
        for word in GLUED_WORDS:
            if rest.endswith(word) and len(rest) > len(word):
                peeled.insert(0, word)
                rest = rest[: -len(word)]
                break
        else:
            break
        if rest.lower() in _WEIGHT_OF or rest.lower() in _SLANT:
            peeled.insert(0, rest)
            rest = ""
    return ([rest] if rest else []) + peeled
