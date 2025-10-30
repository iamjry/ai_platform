"""
OCR Tools for MCP Server
========================

Provides OCR capabilities for extracting text from scanned documents and images.
Supports multiple OCR backends including EasyOCR (CPU) and DeepSeek-OCR (GPU).

Available Tools:
1. ocr_extract_pdf - Extract text from PDF files (handles both text and scanned PDFs)
2. ocr_extract_image - Extract text from image files
3. ocr_get_status - Get OCR service status and backend information
"""

import os
import logging
import tempfile
import json
from typing import Dict, Any, Optional
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


async def ocr_extract_pdf_tool(
    pdf_file: str = None,
    pdf_base64: str = None,
    force_ocr: bool = False,
    use_gpu: bool = False
) -> str:
    """
    Extract text from PDF file using OCR

    Automatically detects if PDF is text-based or scanned, and uses
    appropriate extraction method.

    Args:
        pdf_file: Path to PDF file (either pdf_file or pdf_base64 required)
        pdf_base64: Base64-encoded PDF content
        force_ocr: Force OCR even for text-based PDFs
        use_gpu: Use GPU-based OCR if available (DeepSeek-OCR)

    Returns:
        JSON string with extracted text and metadata
    """
    try:
        from utils.ocr_parser import OCRParser, OCRBackend

        # Handle input
        temp_file = None
        if pdf_base64:
            # Decode base64 and save to temp file
            pdf_content = base64.b64decode(pdf_base64)
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.write(pdf_content)
            temp_file.close()
            pdf_path = temp_file.name
        elif pdf_file:
            pdf_path = pdf_file
            if not os.path.exists(pdf_path):
                return json.dumps({
                    "success": False,
                    "error": f"PDF file not found: {pdf_path}"
                })
        else:
            return json.dumps({
                "success": False,
                "error": "Either pdf_file or pdf_base64 must be provided"
            })

        try:
            # Initialize OCR parser
            backend = OCRBackend.DEEPSEEK_OCR if use_gpu else OCRBackend.EASYOCR
            parser = OCRParser(backend=backend, use_gpu=use_gpu)

            # Extract text
            logger.info(f"Extracting text from PDF: {pdf_path}")
            text = parser.extract_text_from_pdf(pdf_path, force_ocr=force_ocr)

            # Get backend info
            backend_info = parser.get_backend_info()

            result = {
                "success": True,
                "text": text,
                "text_length": len(text),
                "word_count": len(text.split()),
                "backend": backend_info["backend"],
                "ocr_used": force_ocr or "OCR" in text or len(text) > 0,
                "file": os.path.basename(pdf_path)
            }

            logger.info(f"✓ Extracted {len(text)} characters from PDF")
            return json.dumps(result, ensure_ascii=False, indent=2)

        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    except Exception as e:
        logger.error(f"OCR PDF extraction failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


async def ocr_extract_image_tool(
    image_file: str = None,
    image_base64: str = None,
    use_gpu: bool = False
) -> str:
    """
    Extract text from image file using OCR

    Args:
        image_file: Path to image file (either image_file or image_base64 required)
        image_base64: Base64-encoded image content
        use_gpu: Use GPU-based OCR if available (DeepSeek-OCR)

    Returns:
        JSON string with extracted text and metadata
    """
    try:
        from utils.ocr_parser import OCRParser, OCRBackend

        # Handle input
        temp_file = None
        if image_base64:
            # Decode base64 and save to temp file
            image_content = base64.b64decode(image_base64)
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_file.write(image_content)
            temp_file.close()
            image_path = temp_file.name
        elif image_file:
            image_path = image_file
            if not os.path.exists(image_path):
                return json.dumps({
                    "success": False,
                    "error": f"Image file not found: {image_path}"
                })
        else:
            return json.dumps({
                "success": False,
                "error": "Either image_file or image_base64 must be provided"
            })

        try:
            # Initialize OCR parser
            backend = OCRBackend.DEEPSEEK_OCR if use_gpu else OCRBackend.EASYOCR
            parser = OCRParser(backend=backend, use_gpu=use_gpu)

            # Extract text
            logger.info(f"Extracting text from image: {image_path}")
            text = parser.extract_text_from_image(image_path)

            # Get backend info
            backend_info = parser.get_backend_info()

            result = {
                "success": True,
                "text": text,
                "text_length": len(text),
                "word_count": len(text.split()),
                "backend": backend_info["backend"],
                "file": os.path.basename(image_path)
            }

            logger.info(f"✓ Extracted {len(text)} characters from image")
            return json.dumps(result, ensure_ascii=False, indent=2)

        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    except Exception as e:
        logger.error(f"OCR image extraction failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


async def ocr_get_status_tool() -> str:
    """
    Get OCR service status and available backends

    Returns:
        JSON string with OCR service information
    """
    try:
        status = {
            "ocr_available": True,
            "backends": []
        }

        # Check EasyOCR
        try:
            import easyocr
            status["backends"].append({
                "name": "EasyOCR",
                "type": "cpu",
                "available": True,
                "languages": ["en", "ch_tra", "ch_sim", "ja", "ko", "fr", "de", "es", "pt"]
            })
        except ImportError:
            status["backends"].append({
                "name": "EasyOCR",
                "type": "cpu",
                "available": False,
                "error": "Not installed"
            })

        # Check DeepSeek-OCR
        try:
            import torch
            from transformers import AutoModel

            gpu_available = torch.cuda.is_available()
            status["backends"].append({
                "name": "DeepSeek-OCR",
                "type": "gpu",
                "available": gpu_available,
                "cuda_available": gpu_available,
                "model": "deepseek-ai/DeepSeek-OCR (3B params)",
                "requirements": "CUDA GPU required"
            })
        except ImportError:
            status["backends"].append({
                "name": "DeepSeek-OCR",
                "type": "gpu",
                "available": False,
                "error": "PyTorch or Transformers not installed"
            })

        # Add usage recommendations
        status["recommendations"] = {
            "default": "Use EasyOCR for CPU-based processing",
            "high_quality": "Use DeepSeek-OCR for best OCR quality (requires GPU)",
            "scanned_docs": "Both backends support scanned documents",
            "text_pdfs": "Text-based PDFs are handled automatically without OCR"
        }

        return json.dumps(status, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Failed to get OCR status: {e}")
        return json.dumps({
            "ocr_available": False,
            "error": str(e)
        })


# Tool definitions for MCP server
OCR_TOOLS = [
    {
        "name": "ocr_extract_pdf",
        "description": "Extract text from PDF files using OCR. Automatically detects if PDF is scanned or text-based and uses appropriate method. Supports both EasyOCR (CPU) and DeepSeek-OCR (GPU).",
        "category": "document",
        "parameters": {
            "pdf_file": {
                "type": "string",
                "description": "Path to PDF file",
                "required": False
            },
            "pdf_base64": {
                "type": "string",
                "description": "Base64-encoded PDF content",
                "required": False
            },
            "force_ocr": {
                "type": "boolean",
                "description": "Force OCR even for text-based PDFs",
                "required": False,
                "default": False
            },
            "use_gpu": {
                "type": "boolean",
                "description": "Use GPU-based OCR (DeepSeek-OCR) if available",
                "required": False,
                "default": False
            }
        },
        "returns": "JSON with extracted text and metadata",
        "handler": ocr_extract_pdf_tool
    },
    {
        "name": "ocr_extract_image",
        "description": "Extract text from image files (PNG, JPG, etc.) using OCR. Supports both EasyOCR (CPU) and DeepSeek-OCR (GPU).",
        "category": "document",
        "parameters": {
            "image_file": {
                "type": "string",
                "description": "Path to image file",
                "required": False
            },
            "image_base64": {
                "type": "string",
                "description": "Base64-encoded image content",
                "required": False
            },
            "use_gpu": {
                "type": "boolean",
                "description": "Use GPU-based OCR (DeepSeek-OCR) if available",
                "required": False,
                "default": False
            }
        },
        "returns": "JSON with extracted text and metadata",
        "handler": ocr_extract_image_tool
    },
    {
        "name": "ocr_get_status",
        "description": "Get OCR service status, available backends, and recommendations",
        "category": "system",
        "parameters": {},
        "returns": "JSON with OCR service information",
        "handler": ocr_get_status_tool
    }
]
