"""
Contract Parser Utility
Handles parsing of contract documents in various formats (PDF, DOCX, TXT)
Includes OCR support for scanned documents via ocr_parser module
"""

import os
import re
from typing import Dict, List, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ContractParser:
    """Parse and extract content from contract documents with OCR support"""

    def __init__(self, enable_ocr: bool = True, use_gpu_ocr: bool = False):
        """
        Initialize contract parser

        Args:
            enable_ocr: Whether to enable OCR for scanned PDFs (default: True)
            use_gpu_ocr: Whether to use GPU-based OCR (DeepSeek-OCR) if available
        """
        self.supported_formats = ['.pdf', '.docx', '.txt', '.md']
        self.enable_ocr = enable_ocr
        self.use_gpu_ocr = use_gpu_ocr
        self._ocr_parser = None

    def parse_file(self, file_path: str) -> Dict[str, any]:
        """
        Parse a contract file and extract structured content

        Args:
            file_path: Path to the contract file

        Returns:
            Dictionary containing parsed contract data
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Contract file not found: {file_path}")

        file_ext = path.suffix.lower()

        if file_ext not in self.supported_formats:
            raise ValueError(
                f"Unsupported file format: {file_ext}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )

        try:
            if file_ext == '.pdf':
                content = self._parse_pdf(file_path)
            elif file_ext == '.docx':
                content = self._parse_docx(file_path)
            elif file_ext in ['.txt', '.md']:
                content = self._parse_text(file_path)
            else:
                content = ""

            # Extract structured information
            structured_data = self._extract_structure(content)
            structured_data['raw_content'] = content
            structured_data['file_name'] = path.name
            structured_data['file_type'] = file_ext[1:]

            return structured_data

        except Exception as e:
            logger.error(f"Error parsing contract file: {str(e)}")
            raise

    def _get_ocr_parser(self):
        """Lazy-load OCR parser"""
        if self._ocr_parser is None and self.enable_ocr:
            try:
                from utils.ocr_parser import OCRParser, OCRBackend

                # Choose backend based on GPU availability
                if self.use_gpu_ocr:
                    try:
                        import torch
                        if torch.cuda.is_available():
                            backend = OCRBackend.DEEPSEEK_OCR
                            logger.info("Using DeepSeek-OCR (GPU) for scanned documents")
                        else:
                            backend = OCRBackend.EASYOCR
                            logger.info("GPU not available, using EasyOCR for scanned documents")
                    except ImportError:
                        backend = OCRBackend.EASYOCR
                        logger.info("PyTorch not available, using EasyOCR for scanned documents")
                else:
                    backend = OCRBackend.EASYOCR
                    logger.info("Using EasyOCR for scanned documents")

                self._ocr_parser = OCRParser(backend=backend, use_gpu=self.use_gpu_ocr)

            except Exception as e:
                logger.warning(f"Failed to initialize OCR parser: {e}. OCR will be disabled.")
                self.enable_ocr = False

        return self._ocr_parser

    def _parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF file with OCR support"""
        try:
            # First, try OCR parser which intelligently handles both text and scanned PDFs
            if self.enable_ocr:
                ocr_parser = self._get_ocr_parser()
                if ocr_parser:
                    try:
                        logger.info(f"Parsing PDF with OCR support: {file_path}")
                        text = ocr_parser.extract_text_from_pdf(file_path)
                        if text and len(text.strip()) > 50:
                            logger.info(f"✓ Successfully extracted {len(text)} characters using OCR parser")
                            return text.strip()
                    except Exception as e:
                        logger.warning(f"OCR parsing failed, falling back to PyPDF2: {e}")

            # Fallback to PyPDF2 for text-based PDFs
            import PyPDF2

            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"

            logger.info(f"Extracted {len(text)} characters using PyPDF2")
            return text.strip()

        except ImportError:
            logger.warning("PyPDF2 not installed, trying pdfplumber")
            return self._parse_pdf_alternative(file_path)
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise

    def _parse_pdf_alternative(self, file_path: str) -> str:
        """Alternative PDF parser using pdfplumber with OCR fallback"""
        try:
            import pdfplumber

            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            # If very little text extracted, try OCR
            if self.enable_ocr and len(text.strip()) < 100:
                logger.info("pdfplumber extracted little text, trying OCR")
                ocr_parser = self._get_ocr_parser()
                if ocr_parser:
                    try:
                        text = ocr_parser.extract_text_from_pdf(file_path, force_ocr=True)
                    except Exception as e:
                        logger.warning(f"OCR fallback failed: {e}")

            return text.strip()

        except ImportError:
            raise ImportError(
                "PDF parsing requires PyPDF2 or pdfplumber. "
                "Install with: pip install PyPDF2 pdfplumber"
            )

    def _parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            from docx import Document

            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])

            return text.strip()

        except ImportError:
            raise ImportError(
                "DOCX parsing requires python-docx. "
                "Install with: pip install python-docx"
            )
        except Exception as e:
            logger.error(f"Error parsing DOCX: {str(e)}")
            raise

    def _parse_text(self, file_path: str) -> str:
        """Extract text from TXT/MD file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            logger.error(f"Error parsing text file: {str(e)}")
            raise

    def _extract_structure(self, content: str) -> Dict[str, any]:
        """
        Extract structured information from contract content

        Args:
            content: Raw contract text

        Returns:
            Dictionary with structured contract data
        """
        sections = self._identify_sections(content)
        parties = self._extract_parties(content)
        dates = self._extract_dates(content)
        amounts = self._extract_amounts(content)

        return {
            'sections': sections,
            'parties': parties,
            'dates': dates,
            'amounts': amounts,
            'word_count': len(content.split()),
            'char_count': len(content)
        }

    def _identify_sections(self, content: str) -> List[Dict[str, str]]:
        """Identify major sections in the contract"""
        sections = []

        # Common section patterns
        section_patterns = [
            r'(?i)^(?:section|article|clause)\s+(\d+[.\d]*)\s*[:\-]?\s*(.+)$',
            r'(?i)^\d+\.\s+([A-Z][A-Za-z\s]+)$',
            r'(?i)^([A-Z][A-Z\s]{3,})\s*$'  # ALL CAPS headers
        ]

        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            for pattern in section_patterns:
                match = re.match(pattern, line)
                if match:
                    sections.append({
                        'line_number': i + 1,
                        'title': line,
                        'content_start': i + 1
                    })
                    break

        return sections

    def _extract_parties(self, content: str) -> List[str]:
        """Extract party names from contract"""
        parties = []

        # Patterns for party identification
        party_patterns = [
            r'(?i)(?:between|by and between)\s+([^,\n]+(?:,\s*[^,\n]+)?)\s+(?:and|&)',
            r'(?i)"([^"]+)"\s+\((?:hereinafter|referred to as)\s+"([^"]+)"\)',
            r'(?i)party\s+(?:of\s+)?(?:the\s+)?(?:first|second|third)\s+part[:\s]+([^\n,]+)',
        ]

        for pattern in party_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    parties.extend([m.strip() for m in match if m.strip()])
                else:
                    parties.append(match.strip())

        # Remove duplicates and clean
        return list(set([p for p in parties if p and len(p) > 3]))

    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates from contract"""
        # Date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD-MM-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY-MM-DD
            r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b'
        ]

        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            dates.extend(matches)

        return list(set(dates))

    def _extract_amounts(self, content: str) -> List[str]:
        """Extract monetary amounts from contract"""
        # Money patterns
        amount_patterns = [
            r'\$\s*[\d,]+(?:\.\d{2})?',  # $1,000.00
            r'USD\s*[\d,]+(?:\.\d{2})?',  # USD 1,000.00
            r'[\d,]+(?:\.\d{2})?\s*(?:dollars|USD|EUR|GBP)',  # 1,000 dollars
        ]

        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            amounts.extend(matches)

        return list(set(amounts))

    def parse_text_content(self, text_content: str, contract_name: str = "Contract") -> Dict[str, any]:
        """
        Parse contract from text content directly

        Args:
            text_content: Raw contract text
            contract_name: Name identifier for the contract

        Returns:
            Dictionary containing parsed contract data
        """
        try:
            structured_data = self._extract_structure(text_content)
            structured_data['raw_content'] = text_content
            structured_data['file_name'] = contract_name
            structured_data['file_type'] = 'text'

            return structured_data

        except Exception as e:
            logger.error(f"Error parsing contract text: {str(e)}")
            raise


# Convenience function
def parse_contract(file_path: str) -> Dict[str, any]:
    """
    Quick function to parse a contract file

    Args:
        file_path: Path to contract file

    Returns:
        Parsed contract data
    """
    parser = ContractParser()
    return parser.parse_file(file_path)


def parse_contract_text(text: str, name: str = "Contract") -> Dict[str, any]:
    """
    Quick function to parse contract text

    Args:
        text: Contract text content
        name: Contract identifier

    Returns:
        Parsed contract data
    """
    parser = ContractParser()
    return parser.parse_text_content(text, name)
