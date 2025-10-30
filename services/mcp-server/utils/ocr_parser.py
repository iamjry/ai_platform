"""
OCR Parser with Multiple Backend Support
=========================================

Supports multiple OCR backends:
1. EasyOCR (CPU-based, default) - Works on any machine
2. DeepSeek-OCR (GPU-based, optional) - Best quality, requires CUDA GPU
3. PyPDF2 (text extraction) - For text-based PDFs

Usage:
    from utils.ocr_parser import OCRParser, OCRBackend

    # Default: EasyOCR (CPU)
    parser = OCRParser()

    # With DeepSeek-OCR (if GPU available)
    parser = OCRParser(backend=OCRBackend.DEEPSEEK_OCR)

    # Parse PDF
    text = parser.extract_text_from_pdf("contract.pdf")
"""

import os
import io
import logging
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path
import tempfile

# Standard imports
from PIL import Image
import PyPDF2

logger = logging.getLogger(__name__)


class OCRBackend(Enum):
    """Available OCR backends"""
    PYPDF2 = "pypdf2"  # Text extraction only (fast, no OCR)
    EASYOCR = "easyocr"  # CPU-based OCR (default)
    DEEPSEEK_OCR = "deepseek_ocr"  # GPU-based OCR (best quality)


class OCRParser:
    """
    Multi-backend OCR parser for PDF documents

    Automatically detects if PDF is text-based or scanned,
    and uses appropriate extraction method.
    """

    def __init__(
        self,
        backend: OCRBackend = OCRBackend.EASYOCR,
        languages: List[str] = None,
        use_gpu: bool = False,
        confidence_threshold: float = 0.3
    ):
        """
        Initialize OCR parser

        Args:
            backend: OCR backend to use (default: EasyOCR)
            languages: List of language codes (default: ['en', 'zh_tra', 'zh_sim'])
            use_gpu: Whether to use GPU (for EasyOCR)
            confidence_threshold: Minimum confidence for OCR results
        """
        self.backend = backend
        self.languages = languages or ['en', 'zh_tra', 'zh_sim']  # English, Traditional Chinese, Simplified Chinese
        self.use_gpu = use_gpu
        self.confidence_threshold = confidence_threshold
        self.ocr_engine = None

        # Initialize OCR engine
        self._initialize_engine()

    def _initialize_engine(self):
        """Initialize the selected OCR engine"""
        try:
            if self.backend == OCRBackend.EASYOCR:
                import easyocr
                logger.info(f"Initializing EasyOCR with languages: {self.languages}, GPU: {self.use_gpu}")
                self.ocr_engine = easyocr.Reader(
                    self.languages,
                    gpu=self.use_gpu,
                    verbose=False
                )
                logger.info("✓ EasyOCR initialized successfully")

            elif self.backend == OCRBackend.DEEPSEEK_OCR:
                try:
                    from transformers import AutoModel, AutoTokenizer
                    import torch

                    if not torch.cuda.is_available():
                        logger.warning("CUDA not available, falling back to EasyOCR")
                        self.backend = OCRBackend.EASYOCR
                        return self._initialize_engine()

                    logger.info("Initializing DeepSeek-OCR (GPU-based)")
                    model_name = 'deepseek-ai/DeepSeek-OCR'

                    self.tokenizer = AutoTokenizer.from_pretrained(
                        model_name,
                        trust_remote_code=True
                    )
                    self.ocr_engine = AutoModel.from_pretrained(
                        model_name,
                        _attn_implementation='flash_attention_2',
                        trust_remote_code=True,
                        use_safetensors=True
                    )
                    self.ocr_engine = self.ocr_engine.eval().cuda().to(torch.bfloat16)
                    logger.info("✓ DeepSeek-OCR initialized successfully")

                except ImportError as e:
                    logger.error(f"DeepSeek-OCR dependencies not available: {e}")
                    logger.info("Falling back to EasyOCR")
                    self.backend = OCRBackend.EASYOCR
                    return self._initialize_engine()
                except Exception as e:
                    logger.error(f"Failed to initialize DeepSeek-OCR: {e}")
                    logger.info("Falling back to EasyOCR")
                    self.backend = OCRBackend.EASYOCR
                    return self._initialize_engine()

            elif self.backend == OCRBackend.PYPDF2:
                logger.info("Using PyPDF2 for text extraction (no OCR)")
                self.ocr_engine = "pypdf2"

        except Exception as e:
            logger.error(f"Failed to initialize OCR engine: {e}")
            raise

    def _is_pdf_scanned(self, pdf_path: str) -> bool:
        """
        Detect if PDF is scanned (image-based) or text-based

        Returns:
            True if PDF appears to be scanned/image-based
            False if PDF contains extractable text
        """
        try:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                # Check first 3 pages or all pages if less than 3
                pages_to_check = min(3, len(pdf.pages))

                total_text_length = 0
                for i in range(pages_to_check):
                    page = pdf.pages[i]
                    text = page.extract_text()
                    if text:
                        total_text_length += len(text.strip())

                # If average text per page is less than 100 chars, likely scanned
                avg_text_per_page = total_text_length / pages_to_check
                is_scanned = avg_text_per_page < 100

                logger.info(f"PDF analysis: avg_text_per_page={avg_text_per_page:.0f}, is_scanned={is_scanned}")
                return is_scanned

        except Exception as e:
            logger.warning(f"Error detecting PDF type: {e}, assuming scanned")
            return True

    def _extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2 (fast, text-based PDFs only)"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text_parts = []

                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

                result = "\n\n".join(text_parts)
                logger.info(f"Extracted {len(result)} characters using PyPDF2")
                return result

        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return ""

    def _extract_images_from_pdf(self, pdf_path: str) -> List[Image.Image]:
        """Extract images from PDF pages"""
        images = []

        try:
            from pdf2image import convert_from_path

            # Convert PDF pages to images
            logger.info(f"Converting PDF pages to images: {pdf_path}")
            images = convert_from_path(
                pdf_path,
                dpi=300,  # High DPI for better OCR quality
                fmt='PNG'
            )
            logger.info(f"Extracted {len(images)} images from PDF")

        except Exception as e:
            logger.error(f"Failed to extract images from PDF: {e}")

        return images

    def _ocr_image_easyocr(self, image: Image.Image) -> str:
        """Perform OCR on image using EasyOCR"""
        try:
            # Convert PIL Image to numpy array
            import numpy as np
            img_array = np.array(image)

            # Perform OCR
            results = self.ocr_engine.readtext(
                img_array,
                detail=1,  # Return detailed results with confidence
                paragraph=False
            )

            # Filter by confidence and extract text
            text_parts = []
            for detection in results:
                bbox, text, confidence = detection
                if confidence >= self.confidence_threshold:
                    text_parts.append(text)

            return " ".join(text_parts)

        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return ""

    def _ocr_image_deepseek(self, image: Image.Image, page_num: int) -> str:
        """Perform OCR on image using DeepSeek-OCR"""
        try:
            # Save image temporarily
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                image.save(tmp_path, 'PNG')

            try:
                # Perform OCR with DeepSeek
                result = self.ocr_engine.infer(
                    prompt="Free OCR",  # Task instruction
                    image_file=tmp_path,
                    output_path=tempfile.gettempdir(),
                    base_size=1024,  # Use Base configuration (1024×1024)
                    image_size=1024,
                    crop_mode=False,
                    save_results=False
                )

                # Extract text from result
                if isinstance(result, dict) and 'text' in result:
                    return result['text']
                elif isinstance(result, str):
                    return result
                else:
                    logger.warning(f"Unexpected DeepSeek-OCR result format: {type(result)}")
                    return str(result)

            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"DeepSeek-OCR failed: {e}")
            return ""

    def extract_text_from_pdf(
        self,
        pdf_path: str,
        force_ocr: bool = False
    ) -> str:
        """
        Extract text from PDF using appropriate method

        Args:
            pdf_path: Path to PDF file
            force_ocr: Force OCR even if text-based PDF

        Returns:
            Extracted text
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            logger.info(f"Processing PDF: {pdf_path} with backend: {self.backend.value}")

            # Check if OCR is needed
            needs_ocr = force_ocr or self._is_pdf_scanned(pdf_path)

            if not needs_ocr and self.backend == OCRBackend.PYPDF2:
                # Use fast text extraction
                return self._extract_text_pypdf2(pdf_path)

            if not needs_ocr:
                # Try text extraction first (faster)
                text = self._extract_text_pypdf2(pdf_path)
                if text and len(text.strip()) > 100:
                    logger.info("PDF contains extractable text, skipping OCR")
                    return text

            # PDF needs OCR
            logger.info("PDF appears to be scanned, using OCR")

            # Extract images from PDF
            images = self._extract_images_from_pdf(pdf_path)
            if not images:
                logger.warning("No images extracted from PDF")
                return self._extract_text_pypdf2(pdf_path)  # Fallback

            # Perform OCR on each page
            text_parts = []
            for page_num, image in enumerate(images, start=1):
                logger.info(f"Processing page {page_num}/{len(images)}")

                if self.backend == OCRBackend.DEEPSEEK_OCR:
                    page_text = self._ocr_image_deepseek(image, page_num)
                else:  # EasyOCR
                    page_text = self._ocr_image_easyocr(image)

                if page_text and page_text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{page_text}")

            result = "\n\n".join(text_parts)
            logger.info(f"OCR completed: extracted {len(result)} characters from {len(images)} pages")
            return result

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise

    def extract_text_from_image(
        self,
        image_path: str
    ) -> str:
        """
        Extract text from image file

        Args:
            image_path: Path to image file

        Returns:
            Extracted text
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            logger.info(f"Processing image: {image_path}")

            # Load image
            image = Image.open(image_path)

            # Perform OCR
            if self.backend == OCRBackend.DEEPSEEK_OCR:
                text = self._ocr_image_deepseek(image, 1)
            else:  # EasyOCR
                text = self._ocr_image_easyocr(image)

            logger.info(f"OCR completed: extracted {len(text)} characters")
            return text

        except Exception as e:
            logger.error(f"Failed to extract text from image: {e}")
            raise

    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about current OCR backend"""
        return {
            "backend": self.backend.value,
            "languages": self.languages,
            "use_gpu": self.use_gpu,
            "confidence_threshold": self.confidence_threshold,
            "engine_initialized": self.ocr_engine is not None
        }


# Singleton instance for default usage
_default_parser: Optional[OCRParser] = None


def get_default_parser() -> OCRParser:
    """Get or create default OCR parser instance"""
    global _default_parser

    if _default_parser is None:
        # Try to detect if GPU is available
        use_gpu = False
        try:
            import torch
            use_gpu = torch.cuda.is_available()
        except:
            pass

        # Initialize with GPU if available, otherwise CPU
        backend = OCRBackend.DEEPSEEK_OCR if use_gpu else OCRBackend.EASYOCR
        _default_parser = OCRParser(backend=backend, use_gpu=use_gpu)

        logger.info(f"Default OCR parser initialized: {_default_parser.get_backend_info()}")

    return _default_parser


# Convenience functions
def extract_text_from_pdf(pdf_path: str, force_ocr: bool = False) -> str:
    """Convenience function to extract text from PDF"""
    parser = get_default_parser()
    return parser.extract_text_from_pdf(pdf_path, force_ocr=force_ocr)


def extract_text_from_image(image_path: str) -> str:
    """Convenience function to extract text from image"""
    parser = get_default_parser()
    return parser.extract_text_from_image(image_path)
