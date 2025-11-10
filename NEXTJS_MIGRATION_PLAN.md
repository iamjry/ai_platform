# Next.js + Material Design 3 UI 遷移計畫

## 📋 目標

將現有 Streamlit UI 升級為現代化的 Next.js + Material Design 3 (M3) 架構

## 🎯 設計原則

1. **保留 Streamlit**: 舊版 UI 繼續運行在 port 8501
2. **新 UI 獨立**: Next.js 運行在 port 3000
3. **Nginx 統一入口**: 反向代理和路由管理
4. **Material Design 3**: 遵循 Google M3 設計規範
5. **可擴展性**: 支援未來功能擴展

## 📊 現有 UI 功能分析

### Streamlit UI (Port 8501)
| 標籤 | 功能 | 優先級 |
|------|------|--------|
| 💬 對話 | 基本聊天功能 | P0 - 核心 |
| 🤖 Agent任務 | Agent 執行和管理 | P0 - 核心 |
| 👥 Agents目錄 | Agent 類型瀏覽 | P1 - 重要 |
| ⚙️ 模型配置 | LiteLLM 模型管理 | P1 - 重要 |
| 📊 監控 | 系統狀態監控 | P2 - 次要 |
| 📚 知識庫 | RAG 文檔管理 | P1 - 重要 |
| 📄 文檔 | 項目文檔瀏覽 | P2 - 次要 |
| ℹ️ 關於 | 系統資訊 | P2 - 次要 |

## 🏗️ 新架構設計

### 技術棧

```yaml
Frontend:
  Framework: Next.js 14 (App Router)
  UI Library: Material-UI v6 (Material Design 3)
  State Management: Zustand
  API Client: Axios + TanStack Query
  Authentication: NextAuth.js (未來)

Backend Integration:
  Reverse Proxy: Nginx
  API Gateway: /api/* → agent-service, mcp-server, litellm

Development:
  Language: TypeScript
  Package Manager: pnpm
  Code Quality: ESLint, Prettier

Containerization:
  Base: node:20-alpine
  Build: Multi-stage Docker build
  Orchestration: Docker Compose
```

### 目錄結構

```
services/
├── web-ui/                 # Streamlit (保留)
│   └── app.py
├── nextjs-ui/             # 新 Next.js UI
│   ├── src/
│   │   ├── app/           # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── chat/
│   │   │   ├── agents/
│   │   │   ├── knowledge/
│   │   │   └── settings/
│   │   ├── components/    # UI 組件
│   │   │   ├── layout/
│   │   │   │   ├── AppBar.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Footer.tsx
│   │   │   ├── chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   └── InputArea.tsx
│   │   │   ├── agents/
│   │   │   └── common/
│   │   ├── lib/           # 工具函數
│   │   │   ├── api/
│   │   │   ├── theme/
│   │   │   └── utils/
│   │   ├── hooks/         # React Hooks
│   │   ├── stores/        # Zustand stores
│   │   └── types/         # TypeScript types
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
└── nginx/                 # 新增 Nginx 配置
    ├── nginx.conf
    ├── Dockerfile
    └── conf.d/
        ├── nextjs.conf
        ├── streamlit.conf
        └── api.conf
```

## 🎨 Material Design 3 實施

### 主題配置

```typescript
// src/lib/theme/theme.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#6750A4',      // M3 Primary
      container: '#EADDFF',
    },
    secondary: {
      main: '#625B71',
      container: '#E8DEF8',
    },
    tertiary: {
      main: '#7D5260',
      container: '#FFD8E4',
    },
    error: {
      main: '#BA1A1A',
      container: '#FFDAD6',
    },
    background: {
      default: '#FEF7FF',   // M3 Surface
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Noto Sans TC", sans-serif',
    h1: { fontSize: '2.5rem', fontWeight: 500 },
    h2: { fontSize: '2rem', fontWeight: 500 },
    // M3 Typography scale
  },
  shape: {
    borderRadius: 12,       // M3 rounded corners
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 20,   // M3 pill shape
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 1px 3px 1px rgba(0,0,0,0.15)',
        },
      },
    },
    // More M3 components...
  },
});
```

### 主要組件

#### 1. Navigation Rail (側邊導航)
```typescript
// src/components/layout/NavigationRail.tsx
- Home / Dashboard
- Chat (對話)
- Agents (Agent 任務)
- Knowledge Base (知識庫)
- Settings (設定)
```

#### 2. App Bar (頂部欄)
```typescript
// src/components/layout/AppBar.tsx
- Logo
- Page Title
- Search
- Notifications
- User Menu
- Theme Toggle
```

#### 3. Chat Interface
```typescript
// src/components/chat/ChatInterface.tsx
- Message List (Material Design 3 cards)
- Input Area (M3 TextField)
- Model Selector (M3 Select)
- File Upload (M3 Button with icon)
```

## 🔧 Nginx 配置

### 反向代理規則

```nginx
# nginx/conf.d/default.conf

upstream nextjs {
    server nextjs-ui:3000;
}

upstream streamlit {
    server web-ui:8501;
}

upstream agent_service {
    server agent-service:8000;
}

upstream mcp_server {
    server mcp-server:8000;
}

upstream litellm {
    server litellm:4000;
}

server {
    listen 80;
    server_name localhost;

    # Next.js UI (默認)
    location / {
        proxy_pass http://nextjs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Streamlit UI (保留)
    location /streamlit/ {
        proxy_pass http://streamlit/;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # API Endpoints
    location /api/agent/ {
        proxy_pass http://agent_service/;
    }

    location /api/mcp/ {
        proxy_pass http://mcp_server/;
    }

    location /api/litellm/ {
        proxy_pass http://litellm/;
    }

    # Static files (Next.js)
    location /_next/static {
        proxy_cache STATIC;
        proxy_pass http://nextjs;
    }
}
```

## 📦 Docker Compose 配置

### 新增服務

```yaml
# docker-compose.yml (新增部分)

services:
  # 新增 Next.js UI
  nextjs-ui:
    build:
      context: ./services/nextjs-ui
      dockerfile: Dockerfile
    container_name: ai-nextjs-ui
    environment:
      NODE_ENV: production
      NEXT_PUBLIC_API_URL: http://nginx/api
      NEXT_PUBLIC_WS_URL: ws://nginx/api
    ports:
      - "3000:3000"  # 開發時直接訪問
    networks:
      - ai-platform
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 新增 Nginx
  nginx:
    build:
      context: ./services/nginx
      dockerfile: Dockerfile
    container_name: ai-nginx
    ports:
      - "80:80"      # HTTP
      - "443:443"    # HTTPS (未來)
    volumes:
      - ./services/nginx/conf.d:/etc/nginx/conf.d:ro
    networks:
      - ai-platform
    depends_on:
      - nextjs-ui
      - web-ui
      - agent-service
      - mcp-server
      - litellm
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 保留原 Streamlit
  web-ui:
    # ... 原配置不變
    # 改為內部訪問，不直接暴露 8501
    # ports:
    #   - "8501:8501"  # 移除或註釋
```

## 🚀 實施階段

### Phase 1: 基礎架構 (Week 1)
- [ ] 創建 Next.js 專案結構
- [ ] 配置 Material-UI v6 + M3 主題
- [ ] 設置 TypeScript 和基礎配置
- [ ] 實作基本 Layout (AppBar, NavigationRail)
- [ ] 配置 Nginx 反向代理
- [ ] Docker 容器化

### Phase 2: 核心功能 (Week 2-3)
- [ ] Chat Interface (P0)
  - Message List with M3 Cards
  - Input Area with M3 TextField
  - Model Selector
  - File Upload
- [ ] Agent Tasks (P0)
  - Task List
  - Task Execution
  - Result Display
- [ ] API Integration
  - Agent Service
  - MCP Server
  - LiteLLM

### Phase 3: 次要功能 (Week 4)
- [ ] Knowledge Base UI (P1)
  - Document Upload
  - RAG Search
  - Document Management
- [ ] Model Configuration (P1)
  - Model List
  - Model CRUD
- [ ] Agents Catalog (P1)
  - Agent Types
  - Agent Cards

### Phase 4: 進階功能 (Week 5+)
- [ ] System Monitoring (P2)
- [ ] User Authentication (Future)
- [ ] Advanced Settings (P2)
- [ ] Dark Mode
- [ ] Multi-language (i18n)

## 📝 API 適配層

### API Client 設計

```typescript
// src/lib/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '/api',
  timeout: 30000,
});

// Agent Service
export const agentAPI = {
  chat: (data) => apiClient.post('/agent/chat', data),
  execute: (data) => apiClient.post('/agent/execute', data),
  getStatus: (sessionId) => apiClient.get(`/agent/status/${sessionId}`),
};

// MCP Server
export const mcpAPI = {
  listTools: () => apiClient.get('/mcp/tools/list'),
  executeSQL: (query) => apiClient.post('/mcp/tools/sql_query', { query }),
  uploadDocument: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/mcp/rag/upload', formData);
  },
};

// LiteLLM
export const llmAPI = {
  listModels: () => apiClient.get('/litellm/v1/models'),
};
```

## 🎯 用戶訪問路徑

### 生產環境 (通過 Nginx)
```
http://localhost/              → Next.js UI (新界面)
http://localhost/streamlit/    → Streamlit UI (舊界面)
http://localhost/api/agent/*   → Agent Service
http://localhost/api/mcp/*     → MCP Server
http://localhost/api/litellm/* → LiteLLM
```

### 開發環境 (直接訪問)
```
http://localhost:3000/    → Next.js UI (開發伺服器)
http://localhost:8501/    → Streamlit UI
http://localhost:8002/    → Agent Service
http://localhost:8001/    → MCP Server
http://localhost:4000/    → LiteLLM
```

## 🔐 安全考量

1. **CORS 配置**: Nginx 統一處理
2. **API Key 保護**: 環境變數，不暴露給前端
3. **Rate Limiting**: Nginx 層級實施
4. **Input Validation**: 前後端雙重驗證
5. **CSP Headers**: Next.js 配置

## 📊 監控和日誌

```yaml
Logging:
  Nginx: Access logs + Error logs
  Next.js: Winston logger

Monitoring:
  Health Checks: All services
  Metrics: Prometheus (existing)
  Visualization: Grafana (existing)
```

## 🧪 測試策略

```yaml
Unit Tests: Jest + React Testing Library
Integration Tests: Playwright
E2E Tests: Cypress
API Tests: Existing test suite
```

## 📈 性能優化

1. **Next.js Image Optimization**: next/image
2. **Code Splitting**: Dynamic imports
3. **Static Generation**: ISR for static pages
4. **API Caching**: TanStack Query
5. **CDN**: Nginx static file caching

## 🔄 遷移策略

### 漸進式遷移
1. **Phase 1**: 兩個 UI 並存 (Nginx 路由)
2. **Phase 2**: 功能對等測試
3. **Phase 3**: 用戶逐步遷移
4. **Phase 4**: 評估後決定是否棄用 Streamlit

### 回滾計畫
- Nginx 配置快速切換
- Streamlit 保持可用
- 獨立的 Docker 容器

## 🎓 團隊培訓

- Next.js 14 App Router
- Material Design 3 Guidelines
- TypeScript 最佳實踐
- React Hooks 進階用法

## 📋 驗收標準

- [ ] 所有 P0 功能完成並測試通過
- [ ] Material Design 3 設計規範符合度 ≥ 90%
- [ ] 頁面載入時間 < 2s
- [ ] API 響應時間 < 500ms
- [ ] 移動端響應式設計
- [ ] 瀏覽器兼容性 (Chrome, Firefox, Safari, Edge)
- [ ] 無障礙性 (WCAG 2.1 AA)

---

**文檔版本**: 1.0
**創建日期**: 2025-11-10
**作者**: FENC AI Platform Team
**批准**: Pending
