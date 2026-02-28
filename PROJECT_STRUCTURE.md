# Factory Insider Platform — 完整目錄結構

```
factory-insider/
│
├── 📂 frontend/                                 # Next.js Monorepo (3 個應用)
│   ├── 📂 apps/
│   │   ├── 📂 buyer/                          # 買家前台應用
│   │   │   ├── 📂 app/                        # Next.js 14 App Router
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   └── [locale]/...
│   │   │   ├── 📂 components/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── SearchBar.tsx
│   │   │   │   ├── SupplierCard.tsx
│   │   │   │   ├── ChatWidget.tsx
│   │   │   │   └── ...
│   │   │   ├── 📂 lib/
│   │   │   │   ├── api.ts                     # API Client
│   │   │   │   ├── hooks/
│   │   │   │   └── utils/
│   │   │   ├── 📂 hooks/
│   │   │   │   ├── useChat.ts
│   │   │   │   ├── useRFQ.ts
│   │   │   │   └── ...
│   │   │   ├── 📂 styles/
│   │   │   └── package.json
│   │   │
│   │   ├── 📂 supplier/                       # 供應商後台應用
│   │   │   ├── 📂 app/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── videos/
│   │   │   │   ├── rfq/
│   │   │   │   ├── leads/
│   │   │   │   ├── outbound/
│   │   │   │   ├── content/
│   │   │   │   ├── visitors/
│   │   │   │   └── settings/
│   │   │   ├── 📂 components/
│   │   │   │   ├── DashboardOverview.tsx
│   │   │   │   ├── RFQInbox.tsx
│   │   │   │   ├── LeadScoringTable.tsx
│   │   │   │   ├── VideoUploader.tsx
│   │   │   │   ├── OutboundManager.tsx
│   │   │   │   ├── ContentPlanner.tsx
│   │   │   │   ├── VisitorTimeline.tsx
│   │   │   │   └── ...
│   │   │   ├── 📂 lib/
│   │   │   └── package.json
│   │   │
│   │   └── 📂 admin/                          # 管理後台應用
│   │       ├── 📂 app/
│   │       │   ├── dashboard/
│   │       │   ├── suppliers/
│   │       │   ├── buyers/
│   │       │   ├── content-review/
│   │       │   ├── system/
│   │       │   └── ...
│   │       ├── 📂 components/
│   │       └── package.json
│   │
│   ├── 📂 packages/                           # 共享包
│   │   ├── 📂 ui/                             # UI 組件庫
│   │   │   ├── 📂 components/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Tabs.tsx
│   │   │   │   ├── Table.tsx
│   │   │   │   └── ...
│   │   │   ├── 📂 hooks/
│   │   │   └── package.json
│   │   │
│   │   ├── 📂 utils/                          # 工具函數
│   │   │   ├── api.ts
│   │   │   ├── validation.ts
│   │   │   ├── date.ts
│   │   │   └── ...
│   │   │
│   │   ├── 📂 types/                          # 共享型別定義
│   │   │   ├── index.ts
│   │   │   ├── api.ts
│   │   │   ├── models.ts
│   │   │   └── ...
│   │   │
│   │   └── 📂 hooks/                          # 自訂 Hooks
│   │       ├── useAuth.ts
│   │       ├── useApi.ts
│   │       ├── useLocalStorage.ts
│   │       └── ...
│   │
│   ├── 📂 public/
│   │   ├── 📂 images/
│   │   └── 📂 icons/
│   │
│   ├── 📄 turbo.json                          # Turborepo 配置
│   ├── 📄 package.json                        # Root workspace
│   ├── 📄 tsconfig.json
│   ├── 📄 tailwind.config.js
│   ├── 📄 .eslintrc.json
│   └── 📄 next.config.js
│
├── 📂 backend/                                 # FastAPI 後端
│   ├── 📂 app/
│   │   ├── 📄 main.py                         # FastAPI 應用入口
│   │   ├── 📄 config.py                       # 所有 API Key 管理
│   │   ├── 📄 database.py                     # SQLAlchemy 連線
│   │   │
│   │   ├── 📂 models/                         # ORM Models
│   │   │   ├── __init__.py
│   │   │   ├── user.py                        # User, Supplier, Buyer
│   │   │   ├── supplier.py                    # Supplier 詳細資料
│   │   │   ├── buyer.py                       # Buyer 詳細資料
│   │   │   ├── video.py                       # Video + VideoTranslation
│   │   │   ├── rfq.py                         # RFQ + 解析結果
│   │   │   ├── lead.py                        # Lead + Scoring
│   │   │   ├── visitor_event.py               # VisitorEvent 行為追蹤
│   │   │   ├── outbound_campaign.py           # OutboundCampaign + Contact
│   │   │   ├── content_item.py                # ContentItem 內容素材
│   │   │   ├── conversation.py                # Conversation + Message
│   │   │   ├── notification.py                # Notification
│   │   │   └── subscription.py                # Subscription 訂閱
│   │   │
│   │   ├── 📂 schemas/                        # Pydantic Request/Response
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── supplier.py
│   │   │   ├── rfq.py
│   │   │   ├── lead.py
│   │   │   ├── video.py
│   │   │   ├── outbound.py
│   │   │   ├── content.py
│   │   │   ├── visitor.py
│   │   │   ├── analytics.py
│   │   │   └── ...
│   │   │
│   │   ├── 📂 api/
│   │   │   ├── __init__.py
│   │   │   └── 📂 v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py                    # 認證：登入/註冊/Token
│   │   │       ├── suppliers.py               # 供應商 CRUD
│   │   │       ├── buyers.py                  # 買家 CRUD
│   │   │       ├── videos.py                  # 影片管理 + 多語系
│   │   │       ├── rfq.py                     # RFQ 提交/解析
│   │   │       ├── leads.py                   # 線索管理
│   │   │       ├── visitors.py                # 訪客識別資料
│   │   │       ├── outbound.py                # Outbound 活動管理
│   │   │       ├── content.py                 # 內容管理
│   │   │       ├── chat.py                    # AI 分身 WebSocket
│   │   │       ├── analytics.py               # 分析報表
│   │   │       ├── notifications.py           # 通知管理
│   │   │       ├── admin.py                   # 管理後台
│   │   │       └── webhooks.py                # 第三方 Webhook
│   │   │
│   │   ├── 📂 services/                       # 業務邏輯層
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── 📂 ai/                         # AI 功能模組
│   │   │   │   ├── __init__.py
│   │   │   │   ├── rfq_parser.py              # RFQ 多模態解析
│   │   │   │   ├── lead_scorer.py             # Lead Scoring 引擎
│   │   │   │   ├── intent_analyzer.py         # 訪客意圖分析
│   │   │   │   ├── chat_rag.py                # RAG 對話引擎
│   │   │   │   ├── content_gen.py             # 內容自動生成
│   │   │   │   ├── translation.py             # 多語系翻譯
│   │   │   │   └── prompts.py                 # Prompt 模板集合
│   │   │   │
│   │   │   ├── 📂 integrations/               # 第三方 API 封裝
│   │   │   │   ├── __init__.py
│   │   │   │   ├── heygen.py                  # HeyGen 多語系影片
│   │   │   │   ├── clay.py                    # Clay 瀑布式富化
│   │   │   │   ├── apollo.py                  # Apollo 企業背景查詢
│   │   │   │   ├── rb2b.py                    # RB2B Webhook 處理
│   │   │   │   ├── leadfeeder.py              # Leadfeeder API
│   │   │   │   ├── heyreach.py                # HeyReach LinkedIn 自動化
│   │   │   │   ├── instantly.py               # Instantly Email 外展
│   │   │   │   ├── opusclip.py                # OpusClip 短影音
│   │   │   │   ├── repurpose.py               # Repurpose 內容分發
│   │   │   │   ├── slack_notify.py            # Slack 通知推送
│   │   │   │   ├── hubspot.py                 # HubSpot CRM 同步
│   │   │   │   ├── stripe.py                  # Stripe 支付
│   │   │   │   └── base.py                    # 基礎 API 客戶端
│   │   │   │
│   │   │   ├── supplier_service.py            # 供應商業務邏輯
│   │   │   ├── buyer_service.py               # 買家業務邏輯
│   │   │   ├── rfq_service.py                 # RFQ 完整流程
│   │   │   ├── video_service.py               # 影片管理業務
│   │   │   ├── outbound_service.py            # Outbound 引擎
│   │   │   ├── content_service.py             # 內容裂變業務
│   │   │   ├── analytics_service.py           # 分析計算
│   │   │   ├── notification_service.py        # 通知分發
│   │   │   └── billing_service.py             # 訂閱計費
│   │   │
│   │   ├── 📂 tasks/                          # Celery 非同步任務
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py                  # Celery 實例
│   │   │   ├── video_tasks.py                 # 影片轉錄 + 多語系
│   │   │   ├── rfq_tasks.py                   # RFQ 解析 + 評分
│   │   │   ├── outbound_tasks.py              # Outbound 序列執行
│   │   │   ├── content_tasks.py               # 內容裂變 Pipeline
│   │   │   ├── visitor_tasks.py               # 訪客識別 + 富化
│   │   │   └── notification_tasks.py          # 通知推送
│   │   │
│   │   ├── 📂 middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                        # JWT 驗證
│   │   │   ├── rate_limit.py                  # API 限流
│   │   │   ├── tenant.py                      # 多租戶上下文
│   │   │   └── cors.py                        # CORS 設定
│   │   │
│   │   ├── 📂 utils/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py                  # PDF 解析工具
│   │   │   ├── email_validator.py             # Email 驗證
│   │   │   ├── slug_generator.py              # URL slug 生成
│   │   │   ├── gdpr.py                        # GDPR 合規工具
│   │   │   ├── logger.py                      # 日誌工具
│   │   │   └── date.py                        # 日期工具
│   │   │
│   │   └── 📂 security/
│   │       ├── __init__.py
│   │       ├── password.py                    # 密碼雜湊
│   │       ├── jwt.py                         # JWT Token
│   │       └── permissions.py                 # 權限檢查
│   │
│   ├── 📂 tests/                              # 測試套件
│   │   ├── __init__.py
│   │   ├── conftest.py                        # Pytest 配置
│   │   ├── 📂 unit/
│   │   │   ├── test_auth.py
│   │   │   ├── test_rfq_parser.py
│   │   │   ├── test_lead_scorer.py
│   │   │   ├── test_rag.py
│   │   │   └── ...
│   │   ├── 📂 integration/
│   │   │   ├── test_rfq_flow.py
│   │   │   ├── test_outbound_flow.py
│   │   │   ├── test_api_endpoints.py
│   │   │   └── ...
│   │   └── 📂 e2e/
│   │       ├── test_supplier_onboarding.py
│   │       ├── test_buyer_experience.py
│   │       └── ...
│   │
│   ├── 📂 migrations/                         # Alembic DB Migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── 📂 versions/
│   │       ├── 001_initial_schema.py
│   │       ├── 002_add_ai_fields.py
│   │       └── ...
│   │
│   ├── 📂 config/
│   │   └── logging.yaml                       # 日誌配置
│   │
│   ├── 📂 scripts/
│   │   ├── init_db.py                         # 初始化資料庫
│   │   ├── seed_data.py                       # 測試資料
│   │   └── ...
│   │
│   ├── 📂 notebooks/                          # Jupyter Notebooks（分析）
│   │   ├── explore_data.ipynb
│   │   └── test_apis.ipynb
│   │
│   ├── 📄 requirements.txt
│   ├── 📄 requirements-dev.txt
│   ├── 📄 pyproject.toml
│   ├── 📄 setup.py
│   ├── 📄 Dockerfile
│   ├── 📄 .dockerignore
│   └── 📄 pytest.ini
│
├── 📂 infra/                                   # 基礎設施代碼
│   ├── 📂 terraform/                          # Infrastructure as Code
│   │   ├── 📄 main.tf                         # 主配置
│   │   ├── 📄 variables.tf                    # 變數定義
│   │   ├── 📄 outputs.tf                      # 輸出值
│   │   ├── 📄 provider.tf                     # AWS Provider
│   │   │
│   │   ├── 📂 vpc/
│   │   │   ├── main.tf                        # VPC、Subnet、Route
│   │   │   └── variables.tf
│   │   │
│   │   ├── 📂 rds/
│   │   │   ├── main.tf                        # RDS PostgreSQL
│   │   │   └── variables.tf
│   │   │
│   │   ├── 📂 cache/
│   │   │   ├── main.tf                        # ElastiCache Redis
│   │   │   └── variables.tf
│   │   │
│   │   ├── 📂 compute/
│   │   │   ├── main.tf                        # ECS Cluster + Services
│   │   │   └── variables.tf
│   │   │
│   │   ├── 📂 storage/
│   │   │   ├── main.tf                        # S3 Buckets
│   │   │   └── variables.tf
│   │   │
│   │   └── 📂 cdn/
│   │       ├── main.tf                        # CloudFront CDN
│   │       └── variables.tf
│   │
│   ├── 📂 docker/
│   │   ├── 📄 Dockerfile.backend              # Backend 容器
│   │   ├── 📄 Dockerfile.frontend             # Frontend 容器
│   │   ├── 📄 docker-compose.yml              # 本地開發
│   │   ├── 📄 nginx.conf                      # Nginx 閘道設定
│   │   └── 📂 ssl/                            # SSL 證書（開發）
│   │
│   ├── 📂 k8s/                                # Kubernetes（選項）
│   │   ├── 📂 manifests/
│   │   │   ├── backend-deployment.yaml
│   │   │   ├── frontend-deployment.yaml
│   │   │   ├── database-statefulset.yaml
│   │   │   ├── ingress.yaml
│   │   │   └── ...
│   │   │
│   │   ├── 📂 charts/
│   │   │   └── factory-insider/
│   │   │       ├── Chart.yaml                 # Helm Chart
│   │   │       ├── values.yaml
│   │   │       └── templates/
│   │   │
│   │   └── 📂 scripts/
│   │       ├── deploy.sh
│   │       └── rollback.sh
│   │
│   ├── 📂 monitoring/
│   │   ├── 📄 prometheus.yml                  # Prometheus 配置
│   │   ├── 📄 alerting_rules.yml              # 告警規則
│   │   │
│   │   ├── 📂 grafana/
│   │   │   ├── 📄 dashboards.yml
│   │   │   └── 📂 dashboards/
│   │   │       ├── system-metrics.json
│   │   │       ├── api-performance.json
│   │   │       └── business-metrics.json
│   │   │
│   │   └── 📂 sentry/
│   │       └── 📄 sentry.conf.py
│   │
│   ├── 📂 scripts/
│   │   ├── 📄 init-aws.sh                     # AWS 初始化
│   │   ├── 📄 deploy-staging.sh               # Staging 部署
│   │   ├── 📄 deploy-production.sh            # Production 部署
│   │   ├── 📄 backup-database.sh              # 資料庫備份
│   │   └── 📄 health-check.sh                 # 健康檢查
│   │
│   └── 📄 docker-compose.yml                  # 本地開發環境
│
├── 📂 .github/
│   └── 📂 workflows/                          # GitHub Actions
│       ├── 📄 backend-ci.yml                  # Backend 測試 + Lint
│       ├── 📄 frontend-ci.yml                 # Frontend 測試 + Build
│       ├── 📄 deploy-staging.yml              # 自動部署至 Staging
│       └── 📄 deploy-production.yml           # 自動部署至 Production
│
├── 📂 docs/                                    # 文件
│   ├── 📄 technical_architecture.md           # ✅ 技術架構完整版
│   ├── 📄 development_plan.md                 # ✅ 開發計畫（14 Sprints）
│   │
│   ├── 📂 api/
│   │   ├── 📄 endpoints.md                    # API 端點列表
│   │   ├── 📄 authentication.md               # 認證流程
│   │   ├── 📄 error-handling.md               # 錯誤處理
│   │   └── 📄 webhooks.md                     # Webhook 文件
│   │
│   ├── 📂 guides/
│   │   ├── 📄 setup.md                        # 開發環境設定
│   │   ├── 📄 deployment.md                   # 部署指南
│   │   ├── 📄 testing.md                      # 測試策略
│   │   ├── 📄 contributing.md                 # 貢獻指南
│   │   ├── 📄 code-standards.md               # 程式碼規範
│   │   └── 📄 troubleshooting.md              # 常見問題排除
│   │
│   ├── 📂 tutorials/
│   │   ├── 📄 supplier-onboarding.md          # 供應商入駐流程
│   │   ├── 📄 api-integration.md              # API 整合教學
│   │   ├── 📄 third-party-setup.md            # 第三方服務設定
│   │   ├── 📄 stripe-local.md                 # 本地支付測試
│   │   └── 📄 ai-api-testing.md               # AI API 測試
│   │
│   ├── 📂 diagrams/
│   │   ├── 📄 architecture.png                # 系統架構圖
│   │   ├── 📄 data-flow.png                   # 資料流程圖
│   │   ├── 📄 deployment.png                  # 部署架構圖
│   │   ├── 📄 rfq-flow.png                    # RFQ 流程圖
│   │   └── 📄 outbound-flow.png               # Outbound 流程圖
│   │
│   └── 📂 decisions/                          # Architecture Decision Records
│       ├── 📄 001-nextjs-for-frontend.md
│       ├── 📄 002-fastapi-backend.md
│       ├── 📄 003-postgresql-pinecone.md
│       ├── 📄 004-celery-async-tasks.md
│       └── 📄 005-third-party-api-strategy.md
│
├── 📄 CLAUDE.md                               # ✅ Claude Code 專案指令
├── 📄 README.md                               # ✅ 專案總覽
├── 📄 PROJECT_STRUCTURE.md                    # 📍 本文件（目錄結構）
├── 📄 .gitignore
├── 📄 .env.example                            # ✅ 環境變數模板
├── 📄 .editorconfig
├── 📄 .eslintignore
├── 📄 docker-compose.yml                      # ✅ 本地開發環境
├── 📄 package.json                            # Root workspace（Turborepo）
├── 📄 turbo.json                              # Turborepo 配置
├── 📄 tsconfig.json                           # TypeScript 根配置
├── 📄 pyproject.toml                          # Python 根配置
├── 📄 LICENSE
└── 📄 CHANGELOG.md
```

---

## 關鍵目錄說明

### Frontend Monorepo（Turborepo）

三個獨立的 Next.js 應用：

1. **`apps/buyer`** — 買家前台
   - 供應商搜尋、瀏覽、RFQ 提交、AI 分身聊天、訊息通知
   - Port 3000

2. **`apps/supplier`** — 供應商後台
   - 企業資料、影片管理、RFQ 收件、Lead Score、訪客意圖、Outbound 管理、內容排程、KPI 儀表板
   - Port 3001

3. **`apps/admin`** — 管理後台
   - 全平台數據監控、供應商/買家管理、內容審核、系統設定、API 費用追蹤
   - Port 3002

**共享包**（`packages/`）：
- `ui/` — 統一 UI 組件庫（Button、Input、Modal 等）
- `utils/` — 工具函數（API 客戶端、驗證等）
- `types/` — 共享型別定義（API Response、Models）
- `hooks/` — 自訂 React Hooks（useAuth、useApi 等）

### Backend 服務分層

```
API 層 (api/v1/)
    ↓
服務層 (services/)
    ├── AI 模組（rfq_parser、lead_scorer、chat_rag 等）
    └── 整合層（第三方 API 封裝）
    ↓
資料層 (models/)
    ↓
資料庫 (PostgreSQL + Pinecone)
```

核心 AI 功能：
- **RFQ 解析**：`rfq_parser.py` + `lead_scorer.py`
- **AI 分身**：`chat_rag.py`
- **訪客分析**：`intent_analyzer.py`
- **內容生成**：`content_gen.py`

第三方整合（15 個服務）：
- 影片：HeyGen、OpusClip
- 資料：Clay、Apollo、RB2B、Leadfeeder
- 外展：HeyReach、Instantly
- 發布：Repurpose.io
- 通知：Slack、HubSpot
- 支付：Stripe

### Infrastructure

- **Terraform**：AWS 完整基礎設施即代碼（VPC、RDS、ECS、S3、CDN）
- **Docker**：容器化（Backend、Frontend、Nginx）
- **Kubernetes**：可選的編排（Helm Charts + Manifests）
- **監控**：Prometheus + Grafana + Sentry

### 文件組織

- **technical_architecture.md**：系統設計深度文件
- **development_plan.md**：14 個 Sprint、140+ Tasks、完整任務分解
- **api/**：API 文件（Swagger 自動生成）
- **guides/**：開發、部署、測試、貢獻指南
- **tutorials/**：實踐教學（第三方 API 設定、測試）
- **diagrams/**：視覺化架構和流程圖
- **decisions/**：架構決策記錄（ADR）

---

## 快速命令參考

```bash
# 開發環境啟動
docker-compose up -d

# Backend 啟動
cd backend && python -m uvicorn app.main:app --reload

# Frontend 啟動
cd frontend && npm run dev

# 執行遷移
cd backend && alembic upgrade head

# 執行測試
cd backend && pytest tests/

# 建立新 Feature Branch
git checkout -b feature/rfq-parsing

# 提交並推送
git commit -m "feat(rfq): implement Claude-based parsing"
git push origin feature/rfq-parsing
```

---

## 檔案計數統計

```
前端代碼：
  - components: ~150 個
  - pages: ~50 個
  - services: ~20 個
  總計：~1500+ 行 TypeScript

後端代碼：
  - API endpoints: ~20 個
  - Services: ~15 個
  - Models: ~13 個
  - Tasks: ~10 個
  - Integrations: ~15 個
  總計：~10,000+ 行 Python

基礎設施：
  - Terraform modules: 6 個
  - Docker configs: 3 個
  - Kubernetes manifests: ~10 個
  - Monitoring configs: 3 個

文件：
  - 技術架構：969 行
  - 開發計畫：538 行（14 Sprints）
  - API 文件：自動生成（Swagger）
  - 其他指南：~50 篇

總代碼行數：~12,000+ 行
```

---

## 目錄建立時間表

| 時間 | 操作 |
|------|------|
| Week 1 | 建立完整目錄結構、根配置文件 |
| Week 2 | 初始化 frontend/backend 專案 |
| Sprint 1 | 設定 Docker、CI/CD、資料庫 |
| Sprint 2+ | 逐步填充各功能模組 |

---

**目錄結構最後更新**：2026-02-28
**版本**：v1.0
**狀態**：就緒（Ready for Development）
