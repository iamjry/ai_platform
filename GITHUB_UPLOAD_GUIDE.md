# GitHub 上傳指南

本文檔記錄將專案安全上傳到 GitHub 的完整步驟。

**日期**: 2026-02-26
**Repository**: https://github.com/iamjry/ai_platform

---

## 目錄

1. [安全檢查](#1-安全檢查)
2. [安裝與設定 GitHub CLI](#2-安裝與設定-github-cli)
3. [建立 GitHub Repository](#3-建立-github-repository)
4. [連接本地專案到 GitHub](#4-連接本地專案到-github)
5. [移除敏感資訊](#5-移除敏感資訊)
6. [重寫 Git 歷史](#6-重寫-git-歷史)
7. [變更 Repository 為 Public](#7-變更-repository-為-public)

---

## 1. 安全檢查

### 1.1 檢查敏感檔案

確認 `.env` 檔案沒有被 git 追蹤：

```bash
# 檢查 .env 是否被追蹤
git ls-files | grep -E "^\.env$"

# 如果有輸出，需要移除追蹤
git rm --cached .env
```

### 1.2 確認 .gitignore 設定

確保 `.gitignore` 包含以下內容：

```
# Environment variables
.env
.env.local
.env.*.local
*.env

# Private keys
*.pem
*.key
*.crt
```

### 1.3 執行安全檢查腳本

```bash
./check_secrets.sh
```

檢查項目：
- ✅ `.env` 未被追蹤
- ✅ `.env` 在 `.gitignore` 中
- ✅ 無硬編碼的 API Keys
- ✅ 無硬編碼的密碼
- ✅ 無 AWS 憑證
- ✅ 無私鑰檔案
- ✅ 無資料庫憑證

### 1.4 搜尋敏感資訊

```bash
# 搜尋 API Keys 和密碼
git ls-files | xargs grep -E "(api[_-]?key|password|token)\s*[=:]\s*[\"'][^\"']+[\"']" 2>/dev/null

# 搜尋個人資訊
git ls-files | xargs grep -i "your-email@example.com" 2>/dev/null
git ls-files | xargs grep -i "your-name" 2>/dev/null
```

---

## 2. 安裝與設定 GitHub CLI

### 2.1 安裝 GitHub CLI

```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
winget install GitHub.cli
```

### 2.2 登入 GitHub

使用瀏覽器認證（支援 Face ID / Passkey）：

```bash
gh auth login -w -p https
```

執行後會顯示：
```
! First copy your one-time code: XXXX-XXXX
Open this URL to continue in your web browser: https://github.com/login/device
```

步驟：
1. 打開瀏覽器前往 https://github.com/login/device
2. 輸入顯示的驗證碼
3. 用 Face ID 或密碼確認授權

### 2.3 設定 Git 認證

```bash
gh auth setup-git
```

---

## 3. 建立 GitHub Repository

### 方法 A：透過網頁

1. 前往 https://github.com/new
2. 填寫：
   - **Repository name**: `ai_platform`
   - **Visibility**: `Private`（初始建議私有）
   - **不要勾選** "Add a README file"
3. 點擊 **Create repository**

### 方法 B：透過 CLI

```bash
gh repo create ai_platform --private --source=. --remote=origin
```

---

## 4. 連接本地專案到 GitHub

### 4.1 添加遠端 Repository

```bash
# 添加遠端
git remote add origin https://github.com/YOUR_USERNAME/ai_platform.git

# 如果遠端已存在，更新 URL
git remote set-url origin https://github.com/YOUR_USERNAME/ai_platform.git

# 確認遠端設定
git remote -v
```

### 4.2 提交與推送

```bash
# 查看狀態
git status

# 添加所有變更
git add .

# 提交
git commit -m "Initial commit: AI Platform"

# 推送到 GitHub
git push -u origin main
```

---

## 5. 移除敏感資訊

### 5.1 找出敏感資訊

```bash
# 搜尋個人 email
git ls-files | xargs grep -n "your-personal-email@gmail.com" 2>/dev/null

# 搜尋個人名字
git ls-files | xargs grep -n "YourName" 2>/dev/null

# 搜尋本地路徑
git ls-files | xargs grep -n "/Users/yourname/" 2>/dev/null
```

### 5.2 手動修改檔案

編輯包含敏感資訊的檔案，將真實資訊替換為範例：

| 原始內容 | 替換為 |
|----------|--------|
| `your-email@gmail.com` | `your-email@gmail.com` |
| `/Users/yourname/projects/` | `/path/to/your/` |
| 真實密碼 | `YOUR_PASSWORD_HERE` |
| 真實 API Key | `your-api-key-here` |

### 5.3 提交修改

```bash
git add .
git commit -m "fix: Remove sensitive information from documentation"
git push origin main
```

---

## 6. 重寫 Git 歷史

如果敏感資訊已經在之前的 commit 中，需要重寫歷史。

### 6.1 安裝 git-filter-repo

```bash
# macOS
brew install git-filter-repo

# 或使用 pip
pip install git-filter-repo
```

### 6.2 建立替換規則檔案

```bash
cat > /tmp/replacements.txt << 'EOF'
your-real-password==>YOUR_PASSWORD_HERE
your-email@gmail.com==>your-email@gmail.com
/Users/yourname/projects/==>/path/to/your/
YourRealName==>John Doe
EOF
```

### 6.3 執行歷史重寫

```bash
git filter-repo --replace-text /tmp/replacements.txt --force
```

注意：此命令會移除 `origin` 遠端設定。

### 6.4 重新添加遠端並強制推送

```bash
# 重新添加遠端
git remote add origin https://github.com/YOUR_USERNAME/ai_platform.git

# 強制推送（覆蓋遠端歷史）
git push --force origin main
```

### 6.5 驗證清除結果

```bash
# 檢查歷史中是否還有敏感資訊
git log --all -p | grep -c "sensitive-keyword"
# 應該輸出 0
```

---

## 7. 變更 Repository 為 Public

確認所有敏感資訊都已移除後，可以將 repository 改為公開。

### 方法 A：透過 CLI

```bash
gh repo edit YOUR_USERNAME/ai_platform --visibility public --accept-visibility-change-consequences
```

### 方法 B：透過網頁

1. 前往 Repository 頁面
2. 點擊 **Settings**
3. 滾動到最下方 **Danger Zone**
4. 點擊 **Change visibility**
5. 選擇 **Make public**
6. 輸入 repository 名稱確認

---

## 安全檢查清單

上傳前請確認：

- [ ] `.env` 檔案未被追蹤
- [ ] 無硬編碼的 API Keys
- [ ] 無硬編碼的密碼
- [ ] 無個人 email 地址
- [ ] 無個人/公司名稱
- [ ] 無本地檔案路徑（如 `/Users/xxx/`）
- [ ] 無私鑰檔案（`.pem`, `.key`）
- [ ] Git 歷史已清除敏感資訊

---

## 常用指令速查

```bash
# 檢查 git 狀態
git status

# 查看遠端設定
git remote -v

# 查看追蹤的檔案
git ls-files

# 搜尋敏感資訊
git ls-files | xargs grep -i "keyword" 2>/dev/null

# 從追蹤中移除檔案（保留本地）
git rm --cached filename

# 強制推送
git push --force origin main

# 變更 repo 可見性
gh repo edit OWNER/REPO --visibility public --accept-visibility-change-consequences
```

---

## 參考資源

- [GitHub CLI 文件](https://cli.github.com/manual/)
- [git-filter-repo 文件](https://github.com/newren/git-filter-repo)
- [GitHub 移除敏感資料指南](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
