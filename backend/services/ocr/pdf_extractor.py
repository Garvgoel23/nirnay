"""
PDF text extraction using pdfminer.six.
Falls back to Document AI for pages with less than 50 chars of extracted text.
"""
import logging
from io import BytesIO
from typing import List

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter

from models.bidder import PageContent

logger = logging.getLogger(__name__)

MIN_TEXT_LENGTH = 50  # Pages below this threshold are flagged for Document AI fallback


def extract_pdf(file_path: str) -> List[PageContent]:
    """
    Extract text from each page of a PDF using pdfminer.six.

    Pages with extracted text shorter than 50 characters are flagged
    with needs_documentai=True for fallback OCR processing.

    Args:
        file_path: Path to the PDF file

    Returns:
        List of PageContent objects, one per page
    """
    pages: List[PageContent] = []
    laparams = LAParams(line_margin=0.5)
    resource_manager = PDFResourceManager()

    try:
        with open(file_path, "rb") as f:
            for page_num, page in enumerate(PDFPage.get_pages(f), start=1):
                output = BytesIO()
                converter = TextConverter(
                    resource_manager, output, laparams=laparams
                )
                interpreter = PDFPageInterpreter(resource_manager, converter)

                try:
                    interpreter.process_page(page)
                    raw_text = output.getvalue().decode("utf-8", errors="replace")
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {e}")
                    raw_text = ""
                finally:
                    converter.close()
                    output.close()

                word_count = len(raw_text.split())
                needs_fallback = len(raw_text.strip()) < MIN_TEXT_LENGTH

                pages.append(PageContent(
                    page_num=page_num,
                    raw_text=raw_text,
                    word_count=word_count,
                    extraction_method="pdfminer",
                    needs_documentai=needs_fallback,
                ))

                if needs_fallback:
                    logger.info(
                        f"Page {page_num}: only {len(raw_text.strip())} chars, "
                        f"flagged for Document AI fallback"
                    )

    except Exception as e:
        logger.error(f"Failed to extract PDF {file_path}: {e}")
        raise

    logger.info(f"Extracted {len(pages)} pages from {file_path}")
    return pages
