"""
OCR fallback using Tesseract for scanned documents and images.
Replaces Google Document AI — fully local, no cloud dependency.
"""
import logging
import os
from typing import List

from models.bidder import PageContent

logger = logging.getLogger(__name__)


def extract_with_tesseract(file_path: str, mime_type: str) -> List[PageContent]:
    """
    Extract text from scanned PDFs or images using Tesseract OCR.
    
    Requires tesseract-ocr installed on the system (apt-get install tesseract-ocr).
    Supports both Hindi and English via language packs.

    Args:
        file_path: Path to the file (PDF or image)
        mime_type: MIME type of the file

    Returns:
        List of PageContent objects with extraction_method="tesseract"
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        logger.error("pytesseract or Pillow not installed")
        raise ImportError("pip install pytesseract Pillow")

    pages: List[PageContent] = []

    if mime_type == "application/pdf":
        # Convert PDF pages to images then OCR
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Render page to image at 300 DPI
                mat = fitz.Matrix(300 / 72, 300 / 72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # OCR with English + Hindi
                raw_text = pytesseract.image_to_string(img, lang="eng+hin")
                
                # Get confidence data
                data = pytesseract.image_to_data(img, lang="eng+hin", output_type=pytesseract.Output.DICT)
                confidences = [int(c) for c in data["conf"] if int(c) > 0]
                avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0

                word_count = len(raw_text.split())

                pages.append(PageContent(
                    page_num=page_num + 1,
                    raw_text=raw_text,
                    word_count=word_count,
                    extraction_method="tesseract",
                    needs_documentai=False,
                    confidence_avg=avg_confidence,
                ))

            doc.close()
        except Exception as e:
            logger.error(f"Tesseract PDF extraction failed: {e}")
            raise

    elif mime_type.startswith("image/"):
        # Direct image OCR
        try:
            img = Image.open(file_path)
            raw_text = pytesseract.image_to_string(img, lang="eng+hin")

            data = pytesseract.image_to_data(img, lang="eng+hin", output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0

            word_count = len(raw_text.split())

            pages.append(PageContent(
                page_num=1,
                raw_text=raw_text,
                word_count=word_count,
                extraction_method="tesseract",
                needs_documentai=False,
                confidence_avg=avg_confidence,
            ))
        except Exception as e:
            logger.error(f"Tesseract image extraction failed: {e}")
            raise

    logger.info(f"Tesseract extracted {len(pages)} pages from {file_path}")
    return pages
