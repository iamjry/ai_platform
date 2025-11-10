# Next.js + Material Design 3 Implementation Guide

## 📁 已創建的結構

```
services/nextjs-ui/
├── package.json          ✅ 已創建
├── tsconfig.json         ✅ 已創建
├── next.config.js        ✅ 已創建
├── src/
│   ├── app/             ✅ 目錄已創建
│   ├── components/      ✅ 目錄已創建
│   ├── lib/             ✅ 目錄已創建
│   ├── hooks/           ✅ 目錄已創建
│   ├── stores/          ✅ 目錄已創建
│   └── types/           ✅ 目錄已創建
└── public/              ✅ 目錄已創建
```

## 🚀 下一步：核心文件創建

### Phase 1: Material Design 3 Theme Setup

需要創建以下文件以完成 MUI + M3 主題配置：

1. **Theme Provider** (`src/lib/theme/`)
   - `theme.ts` - Material Design 3 主題配置
   - `ThemeRegistry.tsx` - Emotion cache + theme provider
   - `colors.ts` - M3 color tokens
   - `typography.ts` - M3 typography scale

2. **Root Layout** (`src/app/`)
   - `layout.tsx` - 應用程式根 layout
   - `page.tsx` - 首頁/儀表板
   - `providers.tsx` - React Query + Zustand providers

3. **API Client** (`src/lib/api/`)
   - `client.ts` - Axios instance with interceptors
   - `agent.ts` - Agent Service API
   - `mcp.ts` - MCP Server API
   - `litellm.ts` - LiteLLM API

### Phase 2: Core Components

4. **Layout Components** (`src/components/layout/`)
   - `AppBar.tsx` - Top app bar (M3)
   - `NavigationRail.tsx` - Side navigation (M3)
   - `NavigationDrawer.tsx` - Mobile drawer (M3)
   - `Footer.tsx` - Footer

5. **Chat Interface** (`src/components/chat/`)
   - `ChatInterface.tsx` - Main chat component
   - `MessageList.tsx` - Message display
   - `MessageBubble.tsx` - Individual message (M3 card)
   - `InputArea.tsx` - Chat input (M3 text field)
   - `ModelSelector.tsx` - Model selection dropdown

### Phase 3: Additional Features

6. **Agents** (`src/components/agents/`)
   - `AgentCard.tsx` - Agent display card
   - `AgentList.tsx` - Agent catalog
   - `TaskExecutor.tsx` - Task execution UI

7. **Knowledge Base** (`src/components/knowledge/`)
   - `DocumentUpload.tsx` - File upload (M3)
   - `DocumentList.tsx` - Document management
   - `SearchInterface.tsx` - RAG search

8. **Settings** (`src/components/settings/`)
   - `ModelConfig.tsx` - Model configuration
   - `SystemSettings.tsx` - System settings

## 📦 安裝依賴

```bash
cd /path/to/your/ai_platform/services/nextjs-ui
pnpm install
```

這將安裝：
- Next.js 14
- React 18
- Material-UI v6 (M3)
- Emotion (styling)
- TanStack Query (data fetching)
- Zustand (state management)
- Axios (HTTP client)
- TypeScript
- ESLint

## 🎨 Material Design 3 主題配置

### Color Tokens (M3)

```typescript
// src/lib/theme/colors.ts
export const m3Colors = {
  light: {
    primary: '#6750A4',
    onPrimary: '#FFFFFF',
    primaryContainer: '#EADDFF',
    onPrimaryContainer: '#21005D',

    secondary: '#625B71',
    onSecondary: '#FFFFFF',
    secondaryContainer: '#E8DEF8',
    onSecondaryContainer: '#1D192B',

    tertiary: '#7D5260',
    onTertiary: '#FFFFFF',
    tertiaryContainer: '#FFD8E4',
    onTertiaryContainer: '#31111D',

    error: '#BA1A1A',
    onError: '#FFFFFF',
    errorContainer: '#FFDAD6',
    onErrorContainer: '#410002',

    background: '#FEF7FF',
    onBackground: '#1D1B20',
    surface: '#FEF7FF',
    onSurface: '#1D1B20',
    surfaceVariant: '#E7E0EC',
    onSurfaceVariant: '#49454F',

    outline: '#79747E',
    outlineVariant: '#CAC4D0',
    shadow: '#000000',
    scrim: '#000000',
  },
  dark: {
    primary: '#D0BCFF',
    onPrimary: '#381E72',
    primaryContainer: '#4F378B',
    onPrimaryContainer: '#EADDFF',

    secondary: '#CCC2DC',
    onSecondary: '#332D41',
    secondaryContainer: '#4A4458',
    onSecondaryContainer: '#E8DEF8',

    tertiary: '#EFB8C8',
    onTertiary: '#492532',
    tertiaryContainer: '#633B48',
    onTertiaryContainer: '#FFD8E4',

    error: '#FFB4AB',
    onError: '#690005',
    errorContainer: '#93000A',
    onErrorContainer: '#FFDAD6',

    background: '#1D1B20',
    onBackground: '#E6E0E9',
    surface: '#1D1B20',
    onSurface: '#E6E0E9',
    surfaceVariant: '#49454F',
    onSurfaceVariant: '#CAC4D0',

    outline: '#938F99',
    outlineVariant: '#49454F',
    shadow: '#000000',
    scrim: '#000000',
  },
};
```

### Typography Scale (M3)

```typescript
// src/lib/theme/typography.ts
export const m3Typography = {
  displayLarge: {
    fontSize: '57px',
    lineHeight: '64px',
    letterSpacing: '-0.25px',
    fontWeight: 400,
  },
  displayMedium: {
    fontSize: '45px',
    lineHeight: '52px',
    letterSpacing: 0,
    fontWeight: 400,
  },
  displaySmall: {
    fontSize: '36px',
    lineHeight: '44px',
    letterSpacing: 0,
    fontWeight: 400,
  },
  headlineLarge: {
    fontSize: '32px',
    lineHeight: '40px',
    letterSpacing: 0,
    fontWeight: 400,
  },
  headlineMedium: {
    fontSize: '28px',
    lineHeight: '36px',
    letterSpacing: 0,
    fontWeight: 400,
  },
  headlineSmall: {
    fontSize: '24px',
    lineHeight: '32px',
    letterSpacing: 0,
    fontWeight: 400,
  },
  titleLarge: {
    fontSize: '22px',
    lineHeight: '28px',
    letterSpacing: 0,
    fontWeight: 500,
  },
  titleMedium: {
    fontSize: '16px',
    lineHeight: '24px',
    letterSpacing: '0.15px',
    fontWeight: 500,
  },
  titleSmall: {
    fontSize: '14px',
    lineHeight: '20px',
    letterSpacing: '0.1px',
    fontWeight: 500,
  },
  bodyLarge: {
    fontSize: '16px',
    lineHeight: '24px',
    letterSpacing: '0.5px',
    fontWeight: 400,
  },
  bodyMedium: {
    fontSize: '14px',
    lineHeight: '20px',
    letterSpacing: '0.25px',
    fontWeight: 400,
  },
  bodySmall: {
    fontSize: '12px',
    lineHeight: '16px',
    letterSpacing: '0.4px',
    fontWeight: 400,
  },
  labelLarge: {
    fontSize: '14px',
    lineHeight: '20px',
    letterSpacing: '0.1px',
    fontWeight: 500,
  },
  labelMedium: {
    fontSize: '12px',
    lineHeight: '16px',
    letterSpacing: '0.5px',
    fontWeight: 500,
  },
  labelSmall: {
    fontSize: '11px',
    lineHeight: '16px',
    letterSpacing: '0.5px',
    fontWeight: 500,
  },
};
```

## 🐳 Docker Configuration

### Dockerfile (Multi-stage Build)

```dockerfile
# services/nextjs-ui/Dockerfile

# Stage 1: Dependencies
FROM node:20-alpine AS deps
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# Stage 2: Builder
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1
RUN pnpm build

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### .dockerignore

```
node_modules
.next
.git
.env*.local
*.log
.DS_Store
```

## 🔧 Nginx Configuration

### Nginx Dockerfile

```dockerfile
# services/nginx/Dockerfile

FROM nginx:1.25-alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
```

### Main Nginx Config

```nginx
# services/nginx/nginx.conf

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml font/truetype font/opentype
               application/vnd.ms-fontobject image/svg+xml;

    # Include conf files
    include /etc/nginx/conf.d/*.conf;
}
```

### Site Configuration

```nginx
# services/nginx/conf.d/default.conf

# Upstreams
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

# Cache zone for static files
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=STATIC:10m inactive=7d use_temp_path=off;

server {
    listen 80;
    server_name localhost;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Next.js UI (default)
    location / {
        proxy_pass http://nextjs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 60s;
    }

    # Next.js static files (with caching)
    location /_next/static {
        proxy_cache STATIC;
        proxy_pass http://nextjs;
        proxy_cache_valid 200 7d;
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        add_header Cache-Control "public, max-age=31536000, immutable";
        add_header X-Cache-Status $upstream_cache_status;
    }

    # Streamlit UI (legacy)
    location /streamlit/ {
        proxy_pass http://streamlit/;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    # API Endpoints
    location /api/agent/ {
        proxy_pass http://agent_service/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /api/mcp/ {
        proxy_pass http://mcp_server/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /api/litellm/ {
        proxy_pass http://litellm/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;  # Longer timeout for LLM requests
    }

    # WebSocket support for streaming
    location /api/stream {
        proxy_pass http://agent_service/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

## 🐳 Docker Compose Updates

需要在 `docker-compose.yml` 中添加：

```yaml
services:
  # ... existing services ...

  nextjs-ui:
    build:
      context: ./services/nextjs-ui
      dockerfile: Dockerfile
    container_name: ai-nextjs-ui
    environment:
      NODE_ENV: production
      NEXT_PUBLIC_API_URL: /api
    networks:
      - ai-platform
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    # Don't expose port directly - access through nginx
    # ports:
    #   - "3000:3000"

  nginx:
    build:
      context: ./services/nginx
      dockerfile: Dockerfile
    container_name: ai-nginx
    ports:
      - "80:80"
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
```

## 🚀 開發流程

### 1. 本地開發（不使用 Docker）

```bash
cd services/nextjs-ui
pnpm install
pnpm dev
```

訪問: `http://localhost:3000`

API 會自動代理到後端服務（通過 next.config.js 的 rewrites）

### 2. 使用 Docker Compose

```bash
# 構建所有服務
docker-compose build nextjs-ui nginx

# 啟動服務
docker-compose up -d nextjs-ui nginx

# 查看日誌
docker-compose logs -f nextjs-ui nginx
```

訪問:
- Next.js UI: `http://localhost/`
- Streamlit UI: `http://localhost/streamlit/`

## 📝 下一步行動項目

1. [ ] 執行 `pnpm install` 安裝依賴
2. [ ] 創建核心文件（Theme, Layout, API Client）
3. [ ] 實作 Chat Interface
4. [ ] 配置 Nginx
5. [ ] 更新 Docker Compose
6. [ ] 測試端到端流程
7. [ ] 文檔更新

## 🎯 MVP 功能範圍

**Phase 1 - Core (2 weeks)**:
- ✅ Project setup
- [ ] Material Design 3 theme
- [ ] App layout (AppBar + NavigationRail)
- [ ] Chat interface
- [ ] Basic API integration
- [ ] Nginx reverse proxy
- [ ] Docker containerization

**Phase 2 - Features (1 week)**:
- [ ] Agent tasks UI
- [ ] Model selector
- [ ] File upload
- [ ] Knowledge base basic UI

**Phase 3 - Polish (1 week)**:
- [ ] Loading states
- [ ] Error handling
- [ ] Responsive design
- [ ] Dark mode
- [ ] Performance optimization

---

**文檔版本**: 1.0
**創建日期**: 2025-11-10
**最後更新**: 2025-11-10
