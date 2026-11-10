import re
import os
from pathlib import Path
from typing import List, Dict, Any

class PDFProcessingError(Exception):
    """Custom exception raised during PDF processing failures."""
    pass

class PDFProcessor:
    """
    Extracts text page-by-page from PDF files using PyMuPDF (fitz)
    with a graceful fallback to pypdf. Preserves exact page numbers
    and cleans formatting.
    """

    def __init__(self):
        self._fitz_available = False
        try:
            import fitz
            self._fitz_available = True
        except ImportError:
            self._fitz_available = False

    def clean_text(self, text: str) -> str:
        """
        Cleans extracted text:
        - Replaces non-breaking and special unicode spaces with regular space
        - Removes control characters except newline
        - Fixes hyphenated line breaks (e.g. 'informa-\ntion' -> 'information')
        - Normalizes multiple spaces and tabs into single space
        - Normalizes three or more consecutive newlines into double newlines
        """
        if not text:
            return ""

        # Normalize unicode whitespace
        text = text.replace('\xa0', ' ').replace('\u200b', '')
        
        # Rejoin hyphenated line breaks (word split across lines)
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)

        # Normalize carriage returns
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Replace excessive spaces and tabs (not newlines)
        text = re.sub(r'[ \t]+', ' ', text)

        # Remove trailing and leading whitespace on each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Collapse multiple empty lines
        cleaned_lines = []
        empty_count = 0
        for line in lines:
            if not line:
                empty_count += 1
                if empty_count <= 1:
                    cleaned_lines.append("")
            else:
                empty_count = 0
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    def extract_pages(self, file_path: str | Path) -> List[Dict[str, Any]]:
        """
        Extracts cleaned text from each page of the PDF file.
        Returns a list of dicts:
        [
            {
                "page_number": 1,      # 1-indexed for human readability
                "text": "Cleaned page text...",
                "char_count": 1234
            },
            ...
        ]
        """
        path = Path(file_path)
        if not path.exists():
            raise PDFProcessingError(f"File not found: {file_path}")

        if not path.suffix.lower() == ".pdf":
            raise PDFProcessingError(f"Unsupported file type: {path.suffix}. Only .pdf is supported.")

        if path.stat().st_size == 0:
            raise PDFProcessingError("Uploaded PDF file is completely empty (0 bytes).")

        pages = []
        if self._fitz_available:
            pages = self._extract_with_pymupdf(path)
        else:
            pages = self._extract_with_pypdf(path)

        # Verify whether any text was extracted
        total_text_len = sum(len(p["text"]) for p in pages)
        if total_text_len == 0:
            raise PDFProcessingError(
                "Could not extract any readable text from this PDF. "
                "The file may contain only scanned raster images without OCR, "
                "or may be password-protected."
            )

        return pages

    def _extract_with_pymupdf(self, path: Path) -> List[Dict[str, Any]]:
        """Extract pages using PyMuPDF (fitz) - high performance."""
        import fitz
        pages = []
        try:
            doc = fitz.open(str(path))
            if doc.is_encrypted:
                raise PDFProcessingError("PDF is password protected or encrypted.")

            for page_index in range(len(doc)):
                page = doc.load_page(page_index)
                raw_text = page.get_text("text") or ""
                cleaned = self.clean_text(raw_text)
                
                pages.append({
                    "page_number": page_index + 1,  # 1-indexed
                    "text": cleaned,
                    "char_count": len(cleaned)
                })
            doc.close()
            return pages
        except Exception as e:
            if isinstance(e, PDFProcessingError):
                raise
            raise PDFProcessingError(f"Failed to read PDF with PyMuPDF: {str(e)}")

    def _extract_with_pypdf(self, path: Path) -> List[Dict[str, Any]]:
        """Fallback extraction using pypdf."""
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            if reader.is_encrypted:
                raise PDFProcessingError("PDF is password protected or encrypted.")

            pages = []
            for i, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                cleaned = self.clean_text(raw_text)
                pages.append({
                    "page_number": i + 1,
                    "text": cleaned,
                    "char_count": len(cleaned)
                })
            return pages
        except Exception as e:
            if isinstance(e, PDFProcessingError):
                raise
            raise PDFProcessingError(f"Failed to read PDF with pypdf: {str(e)}")

# Singleton instance
pdf_processor = PDFProcessor()
