"""pdfstyle: read the visual style of a PDF page as a spec with confidence and evidence per field."""

from .reader import read
from .spec import FontRun, PageSize, Reading, StyleSpec

__all__ = ["FontRun", "PageSize", "Reading", "StyleSpec", "read"]
__version__ = "0.0.1"
