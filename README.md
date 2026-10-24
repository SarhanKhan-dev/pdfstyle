# pdfstyle

Reads the visual style of a PDF page and returns it as JSON: page size, fonts and sizes, and soon
colours, margins, rules, tinted boxes and the logo.

PDFs store geometry, not design. Nothing in the file says "the heading is 13 pt navy" or "the margin
is 36 pt"; that has to be measured and judged. Parsers like pdfminer.six and pdfplumber give you the
raw coordinates and values. pdfstyle sits on top, turns them into a style spec, and says how sure it
is about each part.

Every field comes with a confidence and the evidence behind it. 1.0 means the value was read from
the file as stored. Anything inferred (which colour is the primary, where the margin is, the family
parsed out of a font name) is reported lower, with a note on where it came from. The aim is that
nothing is wrong silently: on the test set each inferred field is either right or flagged.

## Status

Done: page size, fonts and sizes.

Next: colours, margins, rules and fills, logo, roles (body, heading, meta), a CLI, a PyPI release.

## Install

```bash
pip install pdfstyle
```

## Use

```python
import pdfstyle

spec = pdfstyle.read("brief.pdf")
print(spec.page.value.paper)
for run in spec.fonts.value:
    print(run.family, run.weight, run.size_pt, run.share)
print(spec.to_dict())
```

## Develop

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest -q
```

Tests generate their own PDFs with fpdf2, so the expected values are known up front.

## Licence

Apache-2.0.
