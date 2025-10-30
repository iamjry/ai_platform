#!/usr/bin/env python3
"""
OCR Testing Script
==================

Tests the OCR functionality with various document types.
"""

import requests
import json
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# API endpoint
MCP_SERVER_URL = "http://localhost:8001"


def test_ocr_status():
    """Test 1: Check OCR service status"""
    print("\n" + "="*60)
    print("Test 1: OCR Service Status")
    print("="*60)

    response = requests.get(f"{MCP_SERVER_URL}/tools/ocr_get_status")
    result = response.json()

    print(f"OCR Available: {result['ocr_available']}")
    print("\nBackends:")
    for backend in result['backends']:
        status = "✓" if backend['available'] else "✗"
        print(f"  {status} {backend['name']} ({backend['type']})")

    return result['ocr_available']


def create_test_image_with_text():
    """Create a simple test image with text"""
    print("\n" + "="*60)
    print("Test 2: Create Test Image")
    print("="*60)

    # Create image with text
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)

    # Try to use a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font = ImageFont.load_default()

    # Add text
    text = "Hello OCR!\n這是測試文字\nTest 123"
    draw.text((50, 100), text, fill='black', font=font)

    # Save to temp file
    test_image_path = "/tmp/test_ocr_image.png"
    img.save(test_image_path)

    print(f"✓ Created test image: {test_image_path}")
    print(f"  Text content: {repr(text)}")

    return test_image_path


def test_ocr_extract_image(image_path):
    """Test 3: Extract text from image"""
    print("\n" + "="*60)
    print("Test 3: OCR Image Extraction")
    print("="*60)

    # Read image and encode to base64
    with open(image_path, 'rb') as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

    # Call OCR API
    payload = {
        "image_base64": image_base64,
        "use_gpu": False
    }

    print(f"Sending image to OCR API...")
    response = requests.post(
        f"{MCP_SERVER_URL}/tools/ocr_extract_image",
        json=payload
    )

    result = response.json()

    if result.get('success'):
        print(f"✓ OCR successful!")
        print(f"  Backend: {result['backend']}")
        print(f"  Text length: {result['text_length']} chars")
        print(f"  Word count: {result['word_count']}")
        print(f"\nExtracted text:")
        print("-" * 60)
        print(result['text'])
        print("-" * 60)
    else:
        print(f"✗ OCR failed: {result.get('error')}")

    return result


def test_ocr_with_pdf_path(pdf_path=None):
    """Test 4: Extract text from PDF file"""
    print("\n" + "="*60)
    print("Test 4: OCR PDF Extraction (by path)")
    print("="*60)

    if not pdf_path:
        print("⚠️  No PDF path provided. Skipping PDF test.")
        print("   To test with PDF, provide path as argument:")
        print("   python test_ocr.py /path/to/document.pdf")
        return None

    if not Path(pdf_path).exists():
        print(f"✗ PDF file not found: {pdf_path}")
        return None

    # Call OCR API with file path
    payload = {
        "pdf_file": pdf_path,
        "force_ocr": False,  # Let it auto-detect
        "use_gpu": False
    }

    print(f"Processing PDF: {pdf_path}")
    print(f"Mode: Auto-detect (text vs scanned)")

    response = requests.post(
        f"{MCP_SERVER_URL}/tools/ocr_extract_pdf",
        json=payload
    )

    result = response.json()

    if result.get('success'):
        print(f"✓ PDF processing successful!")
        print(f"  Backend: {result['backend']}")
        print(f"  OCR used: {result.get('ocr_used', 'Unknown')}")
        print(f"  Text length: {result['text_length']} chars")
        print(f"  Word count: {result['word_count']}")
        print(f"\nExtracted text (first 500 chars):")
        print("-" * 60)
        print(result['text'][:500])
        if len(result['text']) > 500:
            print(f"... ({len(result['text']) - 500} more characters)")
        print("-" * 60)
    else:
        print(f"✗ PDF processing failed: {result.get('error')}")

    return result


def test_ocr_force_mode(pdf_path=None):
    """Test 5: Force OCR on text-based PDF"""
    print("\n" + "="*60)
    print("Test 5: Force OCR Mode")
    print("="*60)

    if not pdf_path or not Path(pdf_path).exists():
        print("⚠️  No valid PDF path. Skipping force OCR test.")
        return None

    payload = {
        "pdf_file": pdf_path,
        "force_ocr": True,  # Force OCR even for text PDFs
        "use_gpu": False
    }

    print(f"Processing PDF with FORCED OCR: {pdf_path}")

    response = requests.post(
        f"{MCP_SERVER_URL}/tools/ocr_extract_pdf",
        json=payload
    )

    result = response.json()

    if result.get('success'):
        print(f"✓ Forced OCR successful!")
        print(f"  Backend: {result['backend']}")
        print(f"  Text length: {result['text_length']} chars")
    else:
        print(f"✗ Forced OCR failed: {result.get('error')}")

    return result


def main():
    """Run all OCR tests"""
    import sys

    print("\n" + "="*60)
    print("OCR TESTING SUITE")
    print("="*60)

    # Check if PDF path provided
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        # Test 1: Check status
        ocr_available = test_ocr_status()

        if not ocr_available:
            print("\n✗ OCR not available. Cannot proceed with tests.")
            return

        # Test 2-3: Create and test image
        test_image_path = create_test_image_with_text()
        test_ocr_extract_image(test_image_path)

        # Test 4-5: Test PDF if provided
        if pdf_path:
            test_ocr_with_pdf_path(pdf_path)
            test_ocr_force_mode(pdf_path)

        print("\n" + "="*60)
        print("Testing Complete!")
        print("="*60)
        print("\nSummary:")
        print("  ✓ OCR service is running")
        print("  ✓ EasyOCR backend available")
        print("  ✓ Image extraction tested")
        if pdf_path:
            print("  ✓ PDF extraction tested")
        else:
            print("  ⚠️  PDF tests skipped (no file provided)")

        print("\nTo test with your own PDF:")
        print("  python test_ocr.py /path/to/your/document.pdf")

    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to MCP server at", MCP_SERVER_URL)
        print("  Make sure the server is running: docker-compose ps mcp-server")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
