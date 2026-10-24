# pdfstyle

Read the visual style of a PDF page as a spec: page size, margins, fonts, colours, rules, tinted
boxes and logo, as JSON, with a confidence and the evidence for every field.

A PDF stores geometry, not design. Margins, "the heading size" and "the brand colour" were never
written into the file; they have to be measured and judged. Parsers such as pdfminer.six and
pdfplumber give you the coordinates and raw values. pdfstyle is the layer above: it turns them into
the spec a template engine needs, and tells you how sure it is.

## The accuracy contract

- A value the file stores as such comes back exactly as stored, with confidence `1.0`.
- A value the file does not store is inferred, reported with a confidence below `1.0` and the
  evidence it rests on. On the test corpus every inferred field is either right or flagged, and the
  share that is right is measured and published per release. No silent wrong value.

## Status

`0.0.1`: page size, and fonts with sizes. Font names are parsed by producer conventions (subset tags,
glued or hyphenated style words, Monotype suffixes) into family, CSS weight and slant; sizes are the
stored text-matrix sizes, with a nominal half-point size added only when the stored value is within
0.08 pt of it. Built in the open, one field at a time, each with its generated ground truth. Colours
next, then margins, rules and fills, the logo, roles and confidence.

## Use

```bash
pip install pdfstyle
```

```python
import pdfstyle

spec = pdfstyle.read("brief.pdf")
print(spec.page.value.paper, spec.page.evidence)
```

## Develop

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest -q
```

## Licence

Apache-2.0. See `LICENSE` and `NOTICE`.
