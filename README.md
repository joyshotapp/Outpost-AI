# Factory Insider Platform

> AI-Powered B2B Manufacturing Marketplace
> 台灣製造業 AI 媒合平台

![Status](https://img.shields.io/badge/status-development-yellow)
![Version](https://img.shields.io/badge/version-v0.12--Sprint12-blue)
![License](https://img.shields.io/badge/license-proprietary-red)
![Sprints](https://img.shields.io/badge/sprints-12%2F14%20complete-green)
![Tests](https://img.shields.io/badge/backend%20tests-passing-brightgreen)

## 概述

Factory Insider 是一個**雙邊 B2B 媒合平台**，連結全球買家與台灣製造業供應商。核心特色：

- ✨ **AI 多語系影片生成**（6 種語言一鍵生成）
- 🤖 **AI 數位業務分身**（24/7 多語言 RAG 問答）
- 📊 **RFQ 自動解析 + Lead Scoring**（Claude 驅動）
- 👁️ **訪客意圖分析儀表板**（RB2B + Leadfeeder）
- 🚀 **全自動 Outbound 引擎**（Clay + HeyReach + Instantly）
- 📝 **內容自動裂變矩陣**（1 影片 → 30+ 素材）

### 開發進度（2026-03-03）

| Sprint | 主題 | 狀態 |
|--------|------|------|
| S1-S2 | 基礎架構 + 供應商 CRUD | ✅ 完成 |
| S3-S4 | RFQ 解析 + AI 數位業務分身 | ✅ 完成 |
| S5-S6 | 訪客意圖 + AI 多語系影片 | ✅ 完成 |
| S7-S8 | Outbound 引擎（LinkedIn + Email） | ✅ 完成 |
| S9-S10 | 內容裂變 + 搜尋 + 買家前台 | ✅ 完成 |
| S11-S12 | 訂閱計費 + 管理後台 + 進階功能 | ✅ 完成 |
| S13-S14 | 整合測試 + 上線準備 | 🔲 排程中 |

---

## 快速開始

### 前置要求

- Node.js 18+
- Python 3.12+
- Docker + Docker Compose
- Git

### 開發環境啟動

```bash
# 1. Clone repository
git clone <repo-url>
cd factory-insider

# 2. 設定環境變數
cp .env.example .env.local
# 編輯 .env.local，填入所有第三方 API Key

# 3. 啟動 Docker 服務（PostgreSQL + Redis + Elasticsearch）
docker-compose up -d

# 4. Backend 安裝與啟動
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head  # 執行 Database Migration
python -m uvicorn app.main:app --reload

# 5. Frontend 安裝與啟動（新終端機）
cd frontend
npm install
npm run dev

# 訪問：
# - 買家前台：http://localhost:3004
# - 供應商後台：http://localhost:3001
# - 管理後台：http://localhost:3002
# - API 文件：http://localhost:8001/docs
```

---

## 專案結構

```
factory-insider/
├── frontend/                          # Next.js Monorepo (3 個應用)
│   ├── apps/
│   │   ├── buyer/                    # 買家前台
│   │   │   ├── app/                  # App Router
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   └── ...
│   │   ├── supplier/                 # 供應商後台
│   │   │   └── ...
│   │   └── admin/                    # 管理後台
│   │       └── ...
│   ├── packages/
│   │   ├── ui/                       # 共享 UI 組件
│   │   ├── utils/                    # 工具函數
│   │   ├── types/                    # 共享型別定義
│   │   └── hooks/                    # 自訂 React Hooks
│   ├── turbo.json                    # Turborepo 配置
│   └── package.json
│
├── backend/                           # FastAPI 後端
│   ├── app/
│   │   ├── main.py                   # 應用入口
│   │   ├── config.py                 # 配置（所有 API Key）
│   │   ├── database.py               # 資料庫連線
│   │   │
│   │   ├── models/                   # SQLAlchemy ORM Models
│   │   │   ├── user.py
│   │   │   ├── supplier.py
│   │   │   ├── buyer.py
│   │   │   ├── video.py
│   │   │   ├── rfq.py
│   │   │   ├── lead.py
│   │   │   ├── visitor_event.py
│   │   │   ├── outbound_campaign.py
│   │   │   ├── content_item.py
│   │   │   ├── conversation.py
│   │   │   ├── notification.py
│   │   │   └── subscription.py
│   │   │
│   │   ├── schemas/                  # Pydantic Request/Response
│   │   │   └── (對應每個 model)
│   │   │
│   │   ├── api/v1/                   # API Routes
│   │   │   ├── auth.py               # 認證/登入/註冊
│   │   │   ├── suppliers.py          # 供應商 CRUD
│   │   │   ├── buyers.py             # 買家 CRUD
│   │   │   ├── videos.py             # 影片管理
│   │   │   ├── rfq.py                # RFQ 提交/解析
│   │   │   ├── leads.py              # 線索管理
│   │   │   ├── visitors.py           # 訪客識別
│   │   │   ├── outbound.py           # Outbound 管理
│   │   │   ├── content.py            # 內容管理
│   │   │   ├── chat.py               # AI 分身 WebSocket
│   │   │   ├── analytics.py          # 分析報表
│   │   │   ├── notifications.py      # 通知管理
│   │   │   ├── admin.py              # 管理後台
│   │   │   └── webhooks.py           # 第三方 Webhook
│   │   │
│   │   ├── services/                 # 業務邏輯層
│   │   │   ├── ai/
│   │   │   │   ├── rfq_parser.py     # RFQ 解析（Claude）
│   │   │   │   ├── lead_scorer.py    # Lead Scoring
│   │   │   │   ├── intent_analyzer.py# 訪客意圖分析
│   │   │   │   ├── chat_rag.py       # RAG 對話引擎
│   │   │   │   ├── content_gen.py    # 內容生成
│   │   │   │   └── translation.py    # 多語系翻譯
│   │   │   │
│   │   │   ├── integrations/
│   │   │   │   ├── heygen.py
│   │   │   │   ├── clay.py
│   │   │   │   ├── apollo.py
│   │   │   │   ├── rb2b.py
│   │   │   │   ├── leadfeeder.py
│   │   │   │   ├── heyreach.py
│   │   │   │   ├── instantly.py
│   │   │   │   ├── opusclip.py
│   │   │   │   ├── repurpose.py
│   │   │   │   ├── slack_notify.py
│   │   │   │   └── hubspot.py
│   │   │   │
│   │   │   ├── supplier_service.py
│   │   │   ├── buyer_service.py
│   │   │   ├── rfq_service.py
│   │   │   ├── video_service.py
│   │   │   ├── outbound_service.py
│   │   │   ├── content_service.py
│   │   │   ├── analytics_service.py
│   │   │   └── billing_service.py
│   │   │
│   │   ├── tasks/                    # Celery 非同步任務
│   │   │   ├── video_tasks.py
│   │   │   ├── rfq_tasks.py
│   │   │   ├── outbound_tasks.py
│   │   │   ├── content_tasks.py
│   │   │   ├── visitor_tasks.py
│   │   │   └── notification_tasks.py
│   │   │
│   │   ├── middleware/               # Express/FastAPI Middleware
│   │   │   ├── auth.py
│   │   │   ├── rate_limit.py
│   │   │   ├── tenant.py
│   │   │   └── cors.py
│   │   │
│   │   └── utils/
│   │       ├── pdf_parser.py
│   │       ├── email_validator.py
│   │       ├── slug_generator.py
│   │       └── gdpr.py
│   │
│   ├── tests/                        # 測試
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   ├── migrations/                   # Alembic Database Migration
│   │
│   ├── config/
│   │   └── logging.yaml
│   │
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pyproject.toml
│
├── infra/                             # 基礎設施
│   ├── terraform/                    # Infrastructure as Code
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── vpc/
│   │   ├── rds/
│   │   ├── cache/
│   │   ├── compute/
│   │   ├── storage/
│   │   └── cdn/
│   │
│   ├── docker/
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   └── nginx.conf
│   │
│   ├── k8s/                          # Kubernetes (選項)
│   │   ├── manifests/
│   │   ├── charts/
│   │   └── scripts/
│   │
│   ├── monitoring/
│   │   ├── prometheus.yml
│   │   ├── grafana/
│   │   └── sentry.conf
│   │
│   └── docker-compose.yml
│
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       ├── frontend-ci.yml
│       ├── deploy-staging.yml
│       └── deploy-production.yml
│
├── docs/                             # 文件
│   ├── technical_architecture.md     # ✅ 技術架構文件
│   ├── development_plan.md           # ✅ 開發計畫（14 Sprints）
│   ├── api/
│   │   ├── endpoints.md              # API 端點列表
│   │   └── authentication.md
│   ├── guides/
│   │   ├── setup.md                  # 開發環境設定
│   │   ├── deployment.md             # 部署指南
│   │   ├── testing.md                # 測試策略
│   │   └── contributing.md           # 貢獻指南
│   ├── tutorials/
│   │   ├── supplier-onboarding.md
│   │   ├── api-integration.md
│   │   └── third-party-setup.md      # 第三方 API 設定
│   ├── diagrams/
│   │   ├── architecture.png
│   │   ├── data-flow.png
│   │   └── deployment.png
│   └── decisions/                    # ADR (Architecture Decision Records)
│       ├── 001-nextjs-for-frontend.md
│       ├── 002-fastapi-backend.md
│       └── 003-postgresql-pinecone.md
│
├── CLAUDE.md                         # ✅ Claude Code 專案指令
├── .env.example
├── .gitignore
├── README.md                         # 📍 本文件
├── docker-compose.yml
├── package.json                      # Root workspace
├── turbo.json                        # Turborepo
├── tsconfig.json
├── pyproject.toml
└── LICENSE
```

---

## 核心功能模組

### 1️⃣ AI RFQ 解析 + Lead Scoring（亮點三 + 亮點六）
```
買家提交 RFQ
  ↓
Claude 3.5 Sonnet 多模態解析（PDF + 文字）
  ↓
Apollo.io 企業背景查詢
  ↓
AI 評分（1-100）& A/B/C 分級
  ↓
Slack 即時推送 + 草稿回覆生成
```
**檔案位置**：
- Backend: `backend/app/services/ai/rfq_parser.py` + `lead_scorer.py`
- API: `backend/app/api/v1/rfq.py`

### 2️⃣ AI 數位業務分身（亮點四）
```
知識庫：逐字稿 + 型錄 + FAQ
  ↓
Pinecone 向量資料庫（per-supplier namespace）
  ↓
訪客提問 → Semantic Search → Claude RAG 回覆
  ↓
多語言支援 + 轉人工機制
```
**檔案位置**：
- Backend: `backend/app/services/ai/chat_rag.py`
- API: `backend/app/api/v1/chat.py`
- Frontend: `frontend/apps/buyer/components/ChatWidget.tsx`

### 3️⃣ 訪客意圖分析（亮點二）
```
前端埋點（停留時長、影片觀看）
  ↓
RB2B Webhook（個人識別）
  ↓
Leadfeeder API（企業識別）
  ↓
Clay 背景富化 + 意圖評分
  ↓
高意圖即時通知（Slack + 站內）
```
**檔案位置**：
- Backend: `backend/app/integrations/rb2b.py` + `leadfeeder.py`
- Service: `backend/app/services/ai/intent_analyzer.py`

### 4️⃣ AI 多語系影片生成（亮點一）
```
上傳影片 → Whisper 轉錄
  ↓
HeyGen API：自動生成 4 語言版本
  ↓
德語字數自動壓縮處理
  ↓
影片多語言播放器
```
**檔案位置**：
- Backend: `backend/app/integrations/heygen.py`
- Service: `backend/app/services/video_service.py`

### 5️⃣ Outbound 自動化引擎（Phase 3）
```
ICP 設定 → Clay 瀑布式富化（150+ 資料源）
  ↓
LinkedIn 自動化序列（HeyReach）+ Email 序列（Instantly）
  ↓
AI 個人化開場白
  ↓
回覆偵測 + 熱線索標記
```
**檔案位置**：
- Backend: `backend/app/integrations/clay.py` + `heyreach.py` + `instantly.py`
- Service: `backend/app/services/outbound_service.py`

### 6️⃣ 內容裂變矩陣（亮點五）
```
1 支影片 + 逐字稿
  ↓
OpusClip：自動剪短影音 × 10
  ↓
Claude：生成 LinkedIn × 30 + SEO × 10
  ↓
Repurpose.io：跨平台排程發布
```
**檔案位置**：
- Backend: `backend/app/tasks/content_tasks.py`
- Service: `backend/app/services/content_service.py`

---

## 技術棧

### 前端
- **框架**：Next.js 14 (App Router)
- **語言**：TypeScript
- **UI**：shadcn/ui + Tailwind CSS
- **狀態**：Zustand
- **表單**：React Hook Form + Zod
- **實時**：Socket.io
- **多語系**：next-intl

### 後端
- **框架**：FastAPI
- **ORM**：SQLAlchemy 2.0 + Alembic
- **非同步**：Celery + Redis
- **AI/LLM**：Claude API (Anthropic)
- **向量 DB**：Pinecone
- **搜尋**：Elasticsearch
- **認證**：JWT + OAuth2

### 資料庫
- **主資料庫**：PostgreSQL 16
- **快取**：Redis 7
- **向量資料庫**：Pinecone
- **全文搜尋**：Elasticsearch 8

### 基礎設施
- **主機**：AWS (ECS + RDS + ElastiCache)
- **CDN**：CloudFront
- **容器**：Docker
- **IaC**：Terraform
- **監控**：Sentry + Prometheus + Grafana

---

## API 端點概覽

詳見 `docs/api/endpoints.md`

```
# 認證
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me

# 供應商
GET    /api/v1/suppliers                    # 列表（搜尋 + 篩選）
POST   /api/v1/suppliers                    # 建立
GET    /api/v1/suppliers/{id}               # 詳情
PUT    /api/v1/suppliers/{id}               # 更新
GET    /api/v1/suppliers/{slug}             # 公開頁

# 影片
POST   /api/v1/videos                       # 上傳
GET    /api/v1/videos/{id}                  # 詳情
POST   /api/v1/videos/{id}/translate        # 觸發多語系生成
GET    /api/v1/videos/{id}/translations     # 查詢多語版本

# RFQ
POST   /api/v1/rfq                          # 提交
GET    /api/v1/rfq/{id}                     # 詳情（含 AI 解析）
PUT    /api/v1/rfq/{id}/reply               # 回覆

# 線索
GET    /api/v1/leads                        # 列表
GET    /api/v1/leads/{id}                   # 詳情（買家背景 + 評分）

# AI 分身
WS     /api/v1/chat/{supplier_id}           # WebSocket 對話

# Outbound
POST   /api/v1/outbound/campaigns           # 建立活動
GET    /api/v1/outbound/campaigns/{id}      # 詳情
POST   /api/v1/outbound/campaigns/{id}/start # 啟動
GET    /api/v1/outbound/contacts            # 聯絡人列表

# 內容
GET    /api/v1/content                      # 列表
POST   /api/v1/content/{video_id}/generate  # 觸發裂變

# 訪客
GET    /api/v1/visitors                     # 訪客列表
POST   /api/v1/webhooks/rb2b                # RB2B Webhook
POST   /api/v1/webhooks/leadfeeder          # Leadfeeder Webhook

# 分析
GET    /api/v1/analytics/dashboard          # KPI 快照
GET    /api/v1/analytics/kpis               # 詳細指標

# 訂閱
GET    /api/v1/subscriptions/plans          # 方案列表
POST   /api/v1/subscriptions                # 訂閱
GET    /api/v1/subscriptions/{id}           # 訂閱詳情
```

---

## 開發流程

### 1. 建立 Feature Branch
```bash
git checkout -b feature/rfq-parsing
```

### 2. 遵循 Commit 規範
```bash
git commit -m "feat(rfq): implement Claude-based RFQ parsing"
```

### 3. 推送並建立 Pull Request
```bash
git push origin feature/rfq-parsing
```

### 4. Code Review + CI/CD
- GitHub Actions 自動執行 lint + test
- 至少 1 人 Review 才能合併

### 5. 自動部署至 Staging
PR 合併後自動部署至 staging 環境

---

## 環境變數設定

複製 `.env.example` 並填入：

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/factory_insider

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
ANTHROPIC_API_KEY=sk-...
HEYGEN_API_KEY=...
CLAY_API_KEY=...
APOLLO_API_KEY=...
PINECONE_API_KEY=...
# ... 其他第三方 API Keys

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-southeast-1

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Frontend URLs
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_BUYER_URL=http://localhost:3000
NEXT_PUBLIC_SUPPLIER_URL=http://localhost:3001
```

詳見 `.env.example`

---

## 測試

### Backend 單元測試
```bash
cd backend
pytest tests/unit -v
```

### Backend 整合測試
```bash
pytest tests/integration -v
```

### Frontend 單元測試
```bash
cd frontend
npm run test
```

### E2E 測試（Playwright）
```bash
npm run test:e2e
```

### 覆蓋率報告
```bash
pytest --cov=app tests/ --cov-report=html
```

---

## 部署

### Staging 部署
```bash
git push origin feature/my-feature
# PR 合併後自動部署至 staging
```

### Production 部署
```bash
git tag v1.0.0
git push origin v1.0.0
# GitHub Actions 自動部署至 production
```

詳見 `docs/guides/deployment.md`

---

## 監控 & 告警

### Sentry（錯誤追蹤）
- Frontend 錯誤自動上報
- Backend 例外自動記錄

### Prometheus + Grafana（系統指標）
- API 回應時間
- 資料庫連線數
- Redis 記憶體使用

### Uptime Robot（可用性監控）
- 每 5 分鐘檢查 `/health` 端點

詳見 `infra/monitoring/`

---

## 貢獻指南

1. Fork 本 repository
2. 建立 feature branch：`git checkout -b feature/AmazingFeature`
3. Commit 變更：`git commit -m 'Add AmazingFeature'`
4. Push 至 branch：`git push origin feature/AmazingFeature`
5. 開啟 Pull Request

詳見 `docs/guides/contributing.md`

---

## 常見問題

### Q: 如何新增第三方 API 整合？
A: 見 `docs/tutorials/third-party-setup.md`

### Q: 如何本地測試 Stripe 支付？
A: 使用 Stripe CLI 測試 Webhook，見 `docs/tutorials/stripe-local.md`

### Q: 如何重置資料庫？
A:
```bash
cd backend
alembic downgrade base  # 清空
alembic upgrade head    # 重新建立
```

---

## 資源連結

- 📖 [技術架構](docs/technical_architecture.md)
- 📋 [開發計畫（14 Sprints）](docs/development_plan.md)
- 🚀 [部署指南](docs/guides/deployment.md)
- 🔌 [API 文件](docs/api/endpoints.md)
- 🛠️ [開發環境設定](docs/guides/setup.md)

---

## License

Proprietary — All Rights Reserved

---

## 聯絡方式

- 📧 Email: contact@factoryinsider.com
- 🔗 Website: (TBD)
- 💬 Slack: (Internal)

---

**Last Updated**: 2026-03-03
**Status**: 開發中 — Sprint 12/14 完成
