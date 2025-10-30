# Contract Review OCR 測試指南

## 問題修復說明

**問題**: Contract Review 上傳掃描版 PDF 無法正確透過 OCR 做出審查

**原因**: Web UI 的文件上傳邏輯只使用 PyPDF2 提取文字，對於掃描版 PDF（圖片形式）無法提取任何文字

**修復**: 在 Web UI 文件上傳時自動偵測掃描版 PDF 並調用 OCR API

## 修復內容

### 變更文件
- `services/web-ui/app.py` (lines 1034-1068)

### 工作流程
```
上傳 PDF
    ↓
使用 PyPDF2 嘗試提取文字
    ↓
檢查提取的文字長度
    ↓
如果 < 100 字符 → 判定為掃描版 PDF
    ↓
調用 MCP Server OCR API (base64 編碼)
    ↓
提取完整文字 → 傳給 Agent 審查
```

### 技術細節

**偵測邏輯**:
```python
if len(file_content.strip()) < 100:
    # 判定為掃描版 PDF，使用 OCR
```

**OCR API 調用**:
```python
requests.post(
    f"{MCP_SERVER_URL}/tools/ocr_extract_pdf",
    json={"pdf_base64": pdf_base64, "use_gpu": False},
    timeout=120.0
)
```

**用戶反饋**:
- 🔍 偵測到掃描版 PDF，正在使用 OCR 提取文字...
- ✅ OCR 成功提取 X 個字符
- ⚠️ OCR 失敗: [錯誤訊息]

## 測試步驟

### 測試 1: 文字型 PDF（確保沒有破壞既有功能）

1. 開啟 Web UI: http://localhost:8501
2. 切換到 **Agent Tasks** 頁籤
3. 選擇 **📋 Contract Review** agent
4. 上傳一個文字型 PDF 契約
5. **預期結果**:
   - ✅ 文件已載入: filename.pdf (XXXX 字符)
   - 快速提取（< 1 秒）
   - 不會顯示 OCR 訊息

### 測試 2: 掃描版 PDF（主要修復）

1. 開啟 Web UI: http://localhost:8501
2. 切換到 **Agent Tasks** 頁籤
3. 選擇 **📋 Contract Review** agent
4. 上傳一個掃描版 PDF 契約
5. **預期結果**:
   - 🔍 偵測到掃描版 PDF，正在使用 OCR 提取文字...
   - 處理時間：5-30 秒（取決於頁數）
   - ✅ OCR 成功提取 XXXX 個字符
   - Agent 收到完整文字並進行審查

### 測試 3: Contract Review 執行

**使用掃描版 PDF**:
1. 文件上傳完成後（OCR 已執行）
2. 點擊 **執行任務** 按鈕
3. **預期結果**:
   - Agent 應該能看到完整的契約文字
   - 進行風險評估、條款分析
   - 提供具體的審查建議
   - **不應該**出現「無法讀取文件」或「內容為空」的錯誤

### 測試 4: Chat OCR（確保現有功能不受影響）

1. 切換到 **Chat** 頁籤
2. 輸入: "請使用 OCR 提取這個 PDF 的文字" + 上傳掃描版 PDF
3. **預期結果**:
   - Agent 調用 `ocr_extract_pdf` 工具
   - 成功提取文字
   - 功能正常運作（未被本次修改影響）

## 驗證 OCR 服務

### 檢查 OCR 狀態
```bash
curl http://localhost:8001/tools/ocr_get_status | jq .
```

**預期輸出**:
```json
{
  "ocr_available": true,
  "backends": [
    {
      "name": "EasyOCR",
      "type": "cpu",
      "available": true
    }
  ]
}
```

### 檢查 MCP 工具列表
```bash
curl http://localhost:8001/tools/list | jq '[.tools[] | select(.name | startswith("ocr_"))]'
```

**預期輸出**: 3 個 OCR 工具
- ocr_extract_pdf
- ocr_extract_image
- ocr_get_status

### 檢查服務日誌
```bash
# Web UI 日誌
docker-compose logs web-ui --tail 50

# MCP Server 日誌（OCR 處理）
docker-compose logs mcp-server --tail 50
```

## 效能指標

### 文字型 PDF
- 提取時間: < 1 秒
- 方法: PyPDF2（快速路徑）

### 掃描版 PDF (EasyOCR)
- 首次運行: 5-10 分鐘（下載模型）
- 後續運行: 2-5 秒/頁
- 記憶體: ~1-2 GB

### 範例
- 1 頁掃描 PDF: ~3-5 秒
- 5 頁掃描 PDF: ~15-25 秒
- 10 頁掃描 PDF: ~30-50 秒

## 錯誤處理測試

### 測試場景 1: OCR 服務不可用
```bash
# 停止 MCP server
docker-compose stop mcp-server

# 嘗試上傳掃描版 PDF
# 預期: ⚠️ OCR API 錯誤: 連線失敗
```

### 測試場景 2: 超大 PDF 文件
```bash
# 上傳 > 50 頁的掃描 PDF
# 預期:
# - 可能超時（120 秒限制）
# - 顯示警告訊息
# - 不會導致 UI 崩潰
```

### 測試場景 3: 損壞的 PDF
```bash
# 上傳損壞或格式錯誤的 PDF
# 預期:
# - ❌ 文件載入錯誤: [具體錯誤訊息]
# - 不會導致服務崩潰
```

## 對比測試

### 修復前 (Before)
```
上傳掃描版 PDF
    ↓
PyPDF2 提取 → 0 字符
    ↓
Agent 收到空內容
    ↓
❌ 無法審查契約
```

### 修復後 (After)
```
上傳掃描版 PDF
    ↓
PyPDF2 提取 → 0 字符
    ↓
自動偵測掃描版
    ↓
調用 OCR API
    ↓
成功提取 5000+ 字符
    ↓
✅ Agent 成功審查契約
```

## 成功標準

所有測試通過且滿足以下條件:

- ✅ 文字型 PDF 仍然快速提取（< 1 秒）
- ✅ 掃描版 PDF 自動觸發 OCR
- ✅ OCR 成功提取文字（> 100 字符）
- ✅ Contract Review agent 能夠審查 OCR 提取的文字
- ✅ 用戶收到清楚的進度反饋
- ✅ 錯誤情況有適當的訊息
- ✅ Chat OCR 功能不受影響

## 已知限制

1. **首次 OCR 運行慢**: EasyOCR 需下載模型（約 5-10 分鐘）
2. **語言限制**: 目前預設只支援英文，需手動配置其他語言
3. **超時限制**: 120 秒超時，非常大的 PDF 可能處理不完
4. **記憶體使用**: OCR 處理會使用 1-2 GB 記憶體

## 未來改進

- [ ] 支援進度條顯示 OCR 處理進度
- [ ] 支援多語言 OCR（中文、日文等）
- [ ] 可配置 OCR 超時時間
- [ ] 支援 GPU 加速 OCR（DeepSeek-OCR）
- [ ] 快取 OCR 結果（相同文件不重複處理）

## 相關文件

- `OCR_TESTING_GUIDE.md` - 完整 OCR 測試指南
- `AGENT_OCR_USAGE.md` - Agent OCR 使用指南
- `PROJECT_OVERVIEW.md` - 專案總覽（包含 OCR 章節）

---

**修復日期**: 2025-10-30
**Git Commit**: `292ebd4`
**測試狀態**: ✅ 已驗證
