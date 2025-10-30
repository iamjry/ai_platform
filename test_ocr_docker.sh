#!/bin/bash
# Test OCR inside Docker container where all dependencies are available

echo "=========================================="
echo "Testing OCR Inside Docker Container"
echo "=========================================="

docker exec ai-mcp-server python3 << 'EOF'
import sys
import json
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import requests

print("\n1. Creating test image with text...")
# Create a simple test image
img = Image.new('RGB', (600, 200), color='white')
draw = ImageDraw.Draw(img)

# Add text
text_lines = [
    "Hello OCR Test!",
    "這是繁體中文測試",
    "123456789"
]

y_position = 30
for text in text_lines:
    draw.text((20, y_position), text, fill='black')
    y_position += 50

# Save to buffer
buffer = io.BytesIO()
img.save(buffer, format='PNG')
image_data = buffer.getvalue()
image_base64 = base64.b64encode(image_data).decode('utf-8')

print("✓ Test image created")
print(f"  Image size: {len(image_data)} bytes")
print(f"  Text content: {text_lines}")

print("\n2. Testing OCR extraction...")
# Call OCR API
payload = {
    "image_base64": image_base64,
    "use_gpu": False
}

response = requests.post(
    "http://localhost:8000/tools/ocr_extract_image",
    json=payload
)

result = response.json()

if result.get('success'):
    print("✓ OCR extraction successful!")
    print(f"  Backend: {result['backend']}")
    print(f"  Text length: {result['text_length']} characters")
    print(f"  Word count: {result['word_count']} words")
    print("\n  Extracted text:")
    print("  " + "-" * 50)
    for line in result['text'].split('\n'):
        if line.strip():
            print(f"  {line}")
    print("  " + "-" * 50)
else:
    print(f"✗ OCR failed: {result.get('error')}")
    sys.exit(1)

print("\n3. Test complete!")
EOF

echo ""
echo "=========================================="
echo "Docker container test complete!"
echo "=========================================="
