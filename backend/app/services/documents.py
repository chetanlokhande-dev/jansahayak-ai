"""Document parsing and OCR.

Files are processed entirely in memory (nothing is written to disk) so uploaded
documents leave no temporary files behind. Supported: PDF, DOCX, TXT and images.
"""
from __future__ import annotations

import io
import os
import zipfile
from dataclasses import dataclass, field

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
ALLOWED_EXTS = {".pdf", ".docx", ".txt"} | IMAGE_EXTS


class DocumentError(ValueError):
    """Raised for unsupported, invalid or unreadable documents (safe to show to the user)."""


@dataclass
class Extracted:
    text: str
    kind: str  # pdf | docx | txt | image
    method: str  # e.g. "pymupdf", "pypdf", "pymupdf+ocr", "python-docx", "tesseract"
    pages: int = 1
    warnings: list[str] = field(default_factory=list)


def _ext(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower()


def safe_filename(filename: str) -> str:
    base = os.path.basename((filename or "document").replace("\\", "/"))
    cleaned = "".join(c for c in base if c.isalnum() or c in " ._-()")
    return (cleaned or "document")[:120]


# ---------- OCR ----------

def _ocr_languages(preferred: str) -> str:
    """Use only the Tesseract language packs that are actually installed."""
    try:
        import pytesseract

        installed = set(pytesseract.get_languages(config=""))
    except Exception:
        return "eng"
    wanted = [p for p in preferred.split("+") if p in installed]
    return "+".join(wanted) or ("eng" if "eng" in installed else preferred)


def _ocr_image(img, ocr_langs: str) -> str:
    try:
        import pytesseract
    except ImportError as e:  # pragma: no cover
        raise DocumentError("OCR is not available on this server (pytesseract is not installed).") from e
    try:
        return pytesseract.image_to_string(img, lang=_ocr_languages(ocr_langs))
    except pytesseract.TesseractNotFoundError as e:
        raise DocumentError("OCR is not available on this server (Tesseract is not installed).") from e


# ---------- format readers ----------

def _read_pdf(data: bytes, ocr_langs: str) -> Extracted:
    if not data.startswith(b"%PDF"):
        raise DocumentError("This file does not look like a valid PDF.")
    warnings: list[str] = []
    try:
        import fitz  # PyMuPDF
    except ImportError:
        fitz = None

    if fitz is not None:
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as e:
            raise DocumentError("Could not open the PDF. It may be damaged or password-protected.") from e
        if doc.needs_pass:
            raise DocumentError("This PDF is password-protected. Please remove the password and try again.")
        parts, used_ocr = [], False
        for page in doc:
            text = page.get_text().strip()
            if len(text) < 30:  # probably a scanned page: render and OCR it
                try:
                    from PIL import Image

                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    text = _ocr_image(img, ocr_langs).strip() or text
                    used_ocr = True
                except DocumentError as e:
                    warnings.append(str(e))
                except Exception:
                    warnings.append("A scanned page could not be read.")
            parts.append(text)
        return Extracted("\n\n".join(parts), "pdf", "pymupdf+ocr" if used_ocr else "pymupdf", len(doc), warnings)

    # Fallback without PyMuPDF
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise DocumentError("This PDF is password-protected. Please remove the password and try again.")
        texts = [(p.extract_text() or "") for p in reader.pages]
    except DocumentError:
        raise
    except Exception as e:
        raise DocumentError("Could not read the PDF. It may be damaged.") from e
    if sum(len(t.strip()) for t in texts) < 30:
        warnings.append("This PDF looks like a scan. Install PyMuPDF on the server to enable OCR for scanned PDFs.")
    return Extracted("\n\n".join(texts), "pdf", "pypdf", len(texts), warnings)


def _read_docx(data: bytes) -> Extracted:
    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise DocumentError("This file does not look like a valid DOCX document.")
    try:
        from docx import Document
    except ImportError as e:  # pragma: no cover
        raise DocumentError("DOCX support is not installed on this server.") from e
    try:
        doc = Document(io.BytesIO(data))
    except Exception as e:
        raise DocumentError("Could not read the DOCX file.") from e
    lines = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                lines.append(" | ".join(cells))
    return Extracted("\n".join(lines), "docx", "python-docx")


def _read_txt(data: bytes) -> Extracted:
    for enc in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return Extracted(data.decode(enc), "txt", "plain-text")
        except UnicodeError:
            continue
    raise DocumentError("Could not decode the text file.")


def _read_image(data: bytes, ocr_langs: str) -> Extracted:
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:
        raise DocumentError("This file does not look like a valid image.") from e
    text = _ocr_image(img, ocr_langs)
    warnings = [] if text.strip() else ["No text could be read from this image. Try a clearer, well-lit photo."]
    return Extracted(text, "image", "tesseract", 1, warnings)


# ---------- public API ----------

def extract_text(filename: str, data: bytes, ocr_langs: str = "eng", max_chars: int = 200_000) -> Extracted:
    ext = _ext(filename)
    if ext not in ALLOWED_EXTS:
        raise DocumentError("Unsupported file type. Please upload a PDF, DOCX, TXT or image (PNG, JPG).")
    if not data:
        raise DocumentError("The file is empty.")

    if ext == ".pdf":
        result = _read_pdf(data, ocr_langs)
    elif ext == ".docx":
        result = _read_docx(data)
    elif ext == ".txt":
        result = _read_txt(data)
    else:
        result = _read_image(data, ocr_langs)

    text = "\n".join(line.rstrip() for line in result.text.replace("\x00", "").splitlines()).strip()
    if len(text) > max_chars:
        text = text[:max_chars]
        result.warnings.append("The document is very long, so only the first part was analysed.")
    if not text:
        result.warnings.append("No readable text was found in this document.")
    result.text = text
    return result
