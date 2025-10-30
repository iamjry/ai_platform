# OCR Testing Guide

Complete guide to testing the OCR functionality in the AI Platform.

## Quick Status Check

```bash
# Check if OCR service is available
curl -s http://localhost:8001/tools/ocr_get_status | jq .

# List all OCR tools
curl -s http://localhost:8001/tools/list | jq '.tools[] | select(.name | startswith("ocr_"))'
```

## Method 1: Simple Shell Script Test ⚡

Run the provided test script:

```bash
bash test_ocr_simple.sh
```

This will:
- ✓ Check OCR service status
- ✓ Verify tool registration
- ✓ Display MCP server info

## Method 2: Test with Your Own PDF 📄

### Option A: Using File Path (file must be accessible to container)

```bash
# Copy your PDF to the container
docker cp your-document.pdf ai-mcp-server:/tmp/test.pdf

# Test OCR extraction
curl -X POST http://localhost:8001/tools/ocr_extract_pdf \
  -H 'Content-Type: application/json' \
  -d '{"pdf_file": "/tmp/test.pdf"}' | jq .
```

### Option B: Using Base64 Encoding

```bash
# Encode PDF to base64
PDF_BASE64=$(base64 -i your-document.pdf)

# Test OCR extraction
curl -X POST http://localhost:8001/tools/ocr_extract_pdf \
  -H 'Content-Type: application/json' \
  -d "{\"pdf_base64\": \"$PDF_BASE64\"}" | jq .
```

## Method 3: Test Inside Docker Container 🐳

The most comprehensive test with all dependencies available:

```bash
docker exec -it ai-mcp-server python3 << 'EOF'
from utils.ocr_parser import OCRParser, OCRBackend
from PIL import Image, ImageDraw
import io, base64, requests

# Create test image
img = Image.new('RGB', (400, 150), color='white')
draw = ImageDraw.Draw(img)
draw.text((20, 50), "Test OCR 123", fill='black')

# Convert to base64
buffer = io.BytesIO()
img.save(buffer, format='PNG')
img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

# Test OCR API
response = requests.post(
    "http://localhost:8000/tools/ocr_extract_image",
    json={"image_base64": img_base64}
)

result = response.json()
print(f"Success: {result.get('success')}")
print(f"Text: {result.get('text')}")
EOF
```

## Method 4: Test via Web UI 🖥️

1. Go to **Agent Tasks** tab in Web UI (http://localhost:8501)
2. Select **contract_review** agent type
3. Upload a PDF file (scanned or text-based)
4. The agent will automatically use OCR if needed

## Method 5: Direct API Testing 🔧

### Test Image OCR:

```bash
curl -X POST http://localhost:8001/tools/ocr_extract_image \
  -H 'Content-Type: application/json' \
  -d '{
    "image_file": "/path/to/image.png",
    "use_gpu": false
  }' | jq .
```

### Test PDF OCR (auto-detect):

```bash
curl -X POST http://localhost:8001/tools/ocr_extract_pdf \
  -H 'Content-Type: application/json' \
  -d '{
    "pdf_file": "/path/to/document.pdf",
    "force_ocr": false
  }' | jq .
```

### Test PDF OCR (force mode):

```bash
curl -X POST http://localhost:8001/tools/ocr_extract_pdf \
  -H 'Content-Type: application/json' \
  -d '{
    "pdf_file": "/path/to/document.pdf",
    "force_ocr": true
  }' | jq .
```

## Understanding OCR Behavior

### Auto-Detection Logic

The OCR system automatically detects if a PDF needs OCR:

1. **Text-based PDF** (≥100 chars/page): Uses PyPDF2 (fast)
2. **Scanned PDF** (<100 chars/page): Uses EasyOCR

You can force OCR mode with `"force_ocr": true`.

### Language Support

**Current Default**: English only (`['en']`)

**To use other languages**, initialize OCR parser with language list:

```python
# Example: English + Traditional Chinese
parser = OCRParser(languages=['en', 'ch_tra'])

# Note: Some languages MUST be combined with English
# - ch_tra (Traditional Chinese) → ['en', 'ch_tra']
# - ch_sim (Simplified Chinese) → ['en', 'ch_sim']
# - ja (Japanese) → ['en', 'ja']
```

**Available EasyOCR Languages**:
- `en` - English
- `ch_tra` - Traditional Chinese (繁體中文)
- `ch_sim` - Simplified Chinese (简体中文)
- `ja` - Japanese (日本語)
- `ko` - Korean (한국어)
- `fr` - French
- `de` - German
- `es` - Spanish
- `pt` - Portuguese

[Full list](https://www.jaided.ai/easyocr/)

## Troubleshooting

### OCR Status Shows "available: false"

Check EasyOCR installation:
```bash
docker exec ai-mcp-server pip list | grep easyocr
```

### "Module not found" errors

Rebuild the container:
```bash
docker-compose build mcp-server
docker-compose up -d mcp-server
```

### OCR is very slow

- First run downloads models (can take 5-10 minutes)
- Subsequent runs are faster (models are cached)
- For better performance, use GPU-based OCR (requires CUDA)

### Check MCP Server Logs

```bash
docker-compose logs -f mcp-server
```

## Expected Response Format

### Successful OCR:

```json
{
  "success": true,
  "text": "Extracted text content...",
  "text_length": 1234,
  "word_count": 200,
  "backend": "easyocr",
  "ocr_used": true,
  "file": "document.pdf"
}
```

### Failed OCR:

```json
{
  "success": false,
  "error": "Error message here"
}
```

## Performance Notes

- **EasyOCR (CPU)**:
  - First run: ~5-10 min (model download)
  - Subsequent: ~2-5 sec per page
  - Memory: ~1-2 GB

- **DeepSeek-OCR (GPU)**:
  - Requires: CUDA 11.8+, ~4 GB GPU memory
  - Speed: ~1-2 sec per page
  - Quality: Better accuracy for complex documents

## Integration Examples

### Python Integration:

```python
import requests

def extract_text_from_pdf(pdf_path):
    response = requests.post(
        "http://localhost:8001/tools/ocr_extract_pdf",
        json={"pdf_file": pdf_path}
    )
    result = response.json()
    return result.get('text') if result.get('success') else None
```

### Contract Review Integration:

The Contract Review agent automatically uses OCR when processing uploaded documents. No special configuration needed!

## Next Steps

1. ✅ Tested basic OCR functionality
2. ✅ Verified with your own documents
3. 🔄 Consider adding GPU support for better performance
4. 📚 Integrate OCR into your workflows

## Support

- **Logs**: `docker-compose logs mcp-server`
- **Status**: `curl http://localhost:8001/tools/ocr_get_status`
- **Tools**: `curl http://localhost:8001/tools/list`
