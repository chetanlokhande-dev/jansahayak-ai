import io

import pytest

from app.services import documents as docs

SAMPLE = "Pay the tax before 30/06/2026. A penalty of Rs. 50 applies."


def test_txt():
    r = docs.extract_text("a.txt", SAMPLE.encode())
    assert r.kind == "txt" and "penalty" in r.text


def test_txt_unicode_hindi():
    r = docs.extract_text("hi.txt", "यह एक सूचना है".encode("utf-8"))
    assert "सूचना" in r.text


def test_docx_roundtrip():
    from docx import Document

    d = Document()
    d.add_paragraph(SAMPLE)
    t = d.add_table(rows=1, cols=2)
    t.rows[0].cells[0].text, t.rows[0].cells[1].text = "Fee", "Rs. 10"
    buf = io.BytesIO()
    d.save(buf)
    r = docs.extract_text("n.docx", buf.getvalue())
    assert "penalty" in r.text and "Fee | Rs. 10" in r.text


def test_pdf_text():
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 750), "Annual property tax is due before 30 June 2026 and a penalty applies.")
        pdf_bytes = doc.tobytes()
        doc.close()
    except Exception:
        from reportlab.pdfgen import canvas
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(72, 750, "Annual property tax is due before 30 June 2026 and a penalty applies.")
        c.save()
        pdf_bytes = buf.getvalue()

    r = docs.extract_text("n.pdf", pdf_bytes)
    assert "property tax" in r.text and r.kind == "pdf"


def test_image_ocr():
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (900, 160), "white")
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
    except OSError:
        font = ImageFont.load_default()
    ImageDraw.Draw(img).text((20, 50), "Last date is 15 September", fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    try:
        r = docs.extract_text("scan.png", buf.getvalue(), ocr_langs="eng")
        assert "September" in r.text
    except docs.DocumentError as e:
        if "Tesseract is not installed" in str(e) or "OCR is not available" in str(e):
            pytest.skip("Tesseract OCR binary not installed on system")
        raise


@pytest.mark.parametrize(
    "name,data",
    [("evil.exe", b"MZ..."), ("x.pdf", b"not a pdf"), ("x.docx", b"not a zip"), ("x.png", b"not an image"), ("x.txt", b"")],
)
def test_bad_files_rejected_with_friendly_error(name, data):
    with pytest.raises(docs.DocumentError):
        docs.extract_text(name, data)


def test_extension_cannot_disguise_content():
    with pytest.raises(docs.DocumentError):
        docs.extract_text("report.pdf", b"<html>script</html>")


def test_safe_filename_strips_paths():
    assert docs.safe_filename("../../etc/passwd") == "passwd"
    assert docs.safe_filename("C:\\Users\\x\\bill (1).pdf") == "bill (1).pdf"


def test_long_text_truncated_with_warning():
    r = docs.extract_text("big.txt", ("word " * 5000).encode(), max_chars=1000)
    assert len(r.text) == 1000 and r.warnings
