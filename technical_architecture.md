# Factory Insider Platform — 完整技術架構文件

> 版本：v1.0 | 日期：2026-02-28
> 定位：AI 驅動的台灣製造業 B2B 雙邊媒合平台

---

## 1. 系統總覽

### 1.1 平台定位

Factory Insider 是一個雙邊平台（Two-Sided Marketplace），連結：
- **買家側（Buyer）**：全球採購經理、供應鏈負責人（免費使用）
- **供應商側（Supplier）**：台灣製造業工廠（訂閱制付費）

核心差異化：不是被動等待搜尋（阿里巴巴模式），而是 **AI 主動找買家、驗證工廠、媒合雙方**。

### 1.2 系統架構鳥瞰圖

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Factory Insider Platform                     │
├─────────────────┬────────────────────┬──────────────────────────────┤
│   買家前台       │     供應商後台      │        平台管理後台          │
│   (Buyer App)   │  (Supplier Portal) │      (Admin Console)        │
│   Next.js SSR   │     Next.js SPA    │       Next.js SPA           │
├─────────────────┴────────────────────┴──────────────────────────────┤
│                        API Gateway (Nginx)                          │
├─────────────────────────────────────────────────────────────────────┤
│                     Core Backend (FastAPI / Python)                  │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │ Auth     │ Supplier │ Buyer    │ RFQ      │ Lead     │          │
│  │ Service  │ Service  │ Service  │ Service  │ Scoring  │          │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┤          │
│  │ Content  │ Video    │ Outbound │ Chat     │ Analytics│          │
│  │ Pipeline │ Pipeline │ Engine   │ Service  │ Service  │          │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘          │
├─────────────────────────────────────────────────────────────────────┤
│                       Task Queue (Celery + Redis)                   │
├──────────┬──────────┬──────────┬──────────┬─────────────────────────┤
│PostgreSQL│  Redis   │ Pinecone │ AWS S3   │ Elasticsearch           │
│(主資料庫)│(快取/佇列)│(向量 DB) │(檔案儲存)│(全文搜尋)               │
├──────────┴──────────┴──────────┴──────────┴─────────────────────────┤
│                    第三方 API 整合層                                  │
│  HeyGen │ Clay │ Apollo │ RB2B │ Leadfeeder │ HeyReach │ Instantly │
│  Claude │ Slack│ Jasper │ OpusClip │ Repurpose.io │ HubSpot       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 前端架構

### 2.1 技術選型

| 項目 | 技術 | 理由 |
|------|------|------|
| 框架 | Next.js 14 (App Router) | SSR 支援 SEO（買家搜尋頁）、RSC 效能、國際化 |
| 語言 | TypeScript | 型別安全、大團隊協作 |
| UI 組件 | shadcn/ui + Tailwind CSS | 一致性、快速開發、可定制 |
| 狀態管理 | Zustand | 輕量、適合中型應用 |
| 表單 | React Hook Form + Zod | 驗證、型別推導 |
| 圖表 | Recharts | 儀表板資料可視化 |
| 即時通訊 | Socket.io | AI 分身對話、即時通知 |
| 國際化 | next-intl | 多語系支援（en/de/ja/es/zh） |

### 2.2 三個前端應用

#### 2.2.1 買家前台（Public Buyer App）

路由結構：
```
/                           → 平台首頁（搜尋入口）
/suppliers                  → 供應商列表（篩選/搜尋）
/suppliers/[slug]           → 供應商公開頁（影片、介紹、AI 分身）
/suppliers/[slug]/rfq       → 提交 RFQ 表單
/suppliers/[slug]/chat      → AI 採購助理對話
/buyer/dashboard            → 買家儀表板（我的 RFQ、回覆追蹤）
/buyer/messages             → 平台內訊息
/auth/login                 → 買家登入
/auth/register              → 買家註冊
/[locale]/...               → 多語系路由
```

核心頁面功能：
- **供應商搜尋頁**：Elasticsearch 驅動，按產業/認證/國家/產能篩選
- **供應商公開頁**：6 支多語系驗廠影片播放器 + AI 業務分身 + RFQ 入口
- **RFQ 提交頁**：富文字 + PDF/圖片附件上傳 + 即時規格欄位引導
- **AI 採購助理**：嵌入式聊天視窗，RAG 架構 24/7 多語言回覆

#### 2.2.2 供應商後台（Supplier Portal）

路由結構：
```
/supplier/dashboard              → 總覽儀表板（KPI 快照）
/supplier/profile                → 企業資料設定
/supplier/videos                 → 影片管理（上傳 + 多語系生成）
/supplier/videos/[id]/languages  → 多語系版本管理
/supplier/rfq                    → RFQ 收件匣（AI 解析結果）
/supplier/rfq/[id]               → 單筆 RFQ 詳情（規格摘要 + 草稿回覆）
/supplier/leads                  → 線索管理（Lead Score 列表）
/supplier/leads/[id]             → 買家側寫報告
/supplier/visitors               → 訪客意圖儀表板
/supplier/outbound               → Outbound 管理
/supplier/outbound/linkedin      → LinkedIn 外展序列狀態
/supplier/outbound/email         → Email 外展序列狀態
/supplier/outbound/lists         → 目標名單管理
/supplier/content                → 內容裂變管理
/supplier/content/linkedin       → LinkedIn 貼文排程
/supplier/content/blog           → SEO 文章管理
/supplier/content/shorts         → 短影音管理
/supplier/chatbot                → AI 分身設定（知識庫管理）
/supplier/settings               → 帳號 / 訂閱 / 通知設定
/supplier/billing                → 訂閱方案 / 帳單
```

核心儀表板組件：
- **KPI 快照**：本月 RFQ 數 / Lead Score 平均 / 訪客數 / 轉換率
- **即時警報**：A 級線索 Slack 推送 + 站內通知
- **RFQ 解析檢視器**：左側原文、右側 AI 摘要、底部草稿回覆
- **訪客意圖時間軸**：訪客行為軌跡（停留時長、影片觀看、頁面點擊）

#### 2.2.3 平台管理後台（Admin Console）

路由結構：
```
/admin/dashboard           → 全平台數據總覽
/admin/suppliers           → 供應商管理（審核/上下架）
/admin/buyers              → 買家管理
/admin/rfq                 → 全平台 RFQ 監控
/admin/content/review      → AI 生成內容審核佇列
/admin/outbound/health     → Outbound 系統健康度（送達率/退訂率）
/admin/billing             → 訂閱與帳務管理
/admin/api-usage           → 第三方 API 用量監控
/admin/system              → 系統設定 / API Key 管理
```

---

## 3. 後端架構

### 3.1 技術選型

| 項目 | 技術 | 理由 |
|------|------|------|
| 框架 | FastAPI (Python 3.12) | 非同步、型別提示、AI 生態系完整 |
| ORM | SQLAlchemy 2.0 + Alembic | 成熟、Migration 管理 |
| 任務佇列 | Celery + Redis | 非同步任務（影片處理、AI 評分） |
| 快取 | Redis | Session、Rate Limiting、快取 |
| API 文件 | OpenAPI (Swagger) 自動生成 | FastAPI 原生支援 |
| WebSocket | FastAPI WebSocket + Socket.io | AI 分身即時對話 |
| 認證 | JWT + OAuth2 | 多租戶 SaaS 架構 |

### 3.2 服務模組設計

```
backend/
├── app/
│   ├── main.py                    # FastAPI 應用入口
│   ├── config.py                  # 環境配置（所有 API Key 集中管理）
│   ├── database.py                # DB 連線與 Session 管理
│   │
│   ├── models/                    # SQLAlchemy ORM Models
│   │   ├── user.py                # 用戶（買家 + 供應商 + 管理員）
│   │   ├── supplier.py            # 供應商企業資料
│   │   ├── buyer.py               # 買家企業資料
│   │   ├── video.py               # 影片與多語系版本
│   │   ├── rfq.py                 # RFQ 與解析結果
│   │   ├── lead.py                # 線索與評分
│   │   ├── visitor.py             # 訪客行為記錄
│   │   ├── outbound_campaign.py   # Outbound 活動
│   │   ├── content.py             # 內容素材
│   │   ├── conversation.py        # AI 分身對話記錄
│   │   ├── subscription.py        # 訂閱方案
│   │   └── notification.py        # 通知記錄
│   │
│   ├── schemas/                   # Pydantic Request/Response Schemas
│   │   ├── ...（對應每個 model）
│   │
│   ├── api/                       # API Routes
│   │   ├── v1/
│   │   │   ├── auth.py            # 認證 / 註冊 / Token
│   │   │   ├── suppliers.py       # 供應商 CRUD + 公開列表
│   │   │   ├── buyers.py          # 買家 CRUD
│   │   │   ├── videos.py          # 影片上傳 / 多語系生成觸發
│   │   │   ├── rfq.py             # RFQ 提交 / 解析 / 回覆
│   │   │   ├── leads.py           # 線索管理 / Lead Scoring
│   │   │   ├── visitors.py        # 訪客識別資料
│   │   │   ├── outbound.py        # Outbound 活動管理
│   │   │   ├── content.py         # 內容管理
│   │   │   ├── chat.py            # AI 分身 WebSocket
│   │   │   ├── analytics.py       # 分析與報表
│   │   │   ├── notifications.py   # 通知管理
│   │   │   ├── admin.py           # 管理後台 API
│   │   │   └── webhooks.py        # 第三方 Webhook 接收端
│   │
│   ├── services/                  # 業務邏輯層
│   │   ├── ai/
│   │   │   ├── rfq_parser.py      # RFQ 解析（Claude API）
│   │   │   ├── lead_scorer.py     # Lead Scoring（Apollo + Claude）
│   │   │   ├── intent_analyzer.py # 訪客意圖分析
│   │   │   ├── chat_rag.py        # RAG 對話引擎
│   │   │   ├── content_gen.py     # 內容生成（Claude/Jasper）
│   │   │   └── translation.py     # 多語系翻譯
│   │   │
│   │   ├── integrations/
│   │   │   ├── heygen.py          # HeyGen API 封裝
│   │   │   ├── clay.py            # Clay API 封裝
│   │   │   ├── apollo.py          # Apollo.io API 封裝
│   │   │   ├── rb2b.py            # RB2B Webhook 處理
│   │   │   ├── leadfeeder.py      # Leadfeeder API 封裝
│   │   │   ├── heyreach.py        # HeyReach API 封裝
│   │   │   ├── instantly.py       # Instantly API 封裝
│   │   │   ├── opusclip.py        # OpusClip API 封裝
│   │   │   ├── repurpose.py       # Repurpose.io API 封裝
│   │   │   ├── slack_notify.py    # Slack Webhook 推送
│   │   │   └── hubspot.py         # HubSpot CRM 同步
│   │   │
│   │   ├── supplier_service.py
│   │   ├── buyer_service.py
│   │   ├── rfq_service.py
│   │   ├── video_service.py
│   │   ├── outbound_service.py
│   │   ├── content_service.py
│   │   ├── analytics_service.py
│   │   ├── notification_service.py
│   │   └── billing_service.py
│   │
│   ├── tasks/                     # Celery 非同步任務
│   │   ├── video_tasks.py         # 影片轉錄 / 多語系生成
│   │   ├── rfq_tasks.py           # RFQ 解析 + Lead Scoring
│   │   ├── outbound_tasks.py      # Outbound 序列排程
│   │   ├── content_tasks.py       # 內容裂變 Pipeline
│   │   ├── visitor_tasks.py       # 訪客識別 + 富化
│   │   └── notification_tasks.py  # 通知推送
│   │
│   ├── middleware/
│   │   ├── auth.py                # JWT 驗證
│   │   ├── rate_limit.py          # API 限流
│   │   ├── tenant.py              # 多租戶上下文
│   │   └── cors.py                # CORS 設定
│   │
│   └── utils/
│       ├── pdf_parser.py          # PDF 解析工具
│       ├── email_validator.py     # Email 格式驗證
│       ├── slug_generator.py      # 供應商 URL slug
│       └── gdpr.py                # GDPR 合規工具
```

### 3.3 核心服務流程詳解

#### 3.3.1 RFQ 解析流程（亮點三 + 亮點六）

```
買家提交 RFQ
      │
      ▼
[API: POST /api/v1/rfq]
      │
      ├── 儲存原始 RFQ 至 PostgreSQL
      ├── 上傳附件至 S3
      │
      ▼
[Celery Task: rfq_parse_and_score]
      │
      ├── 1. PDF/圖面預處理
      │      └── AWS Textract OCR（掃描式 PDF）
      │      └── Claude Vision API（工程圖面解析）
      │
      ├── 2. RFQ 文字解析（Claude API）
      │      ├── Prompt: 製造業術語專用模板
      │      ├── 輸出: 材料/尺寸/公差/表面處理/數量/交期
      │      └── 輸出: 潛在風險點標記
      │
      ├── 3. 買家背景調查（Apollo.io API）
      │      ├── 輸入: 買家 Email Domain
      │      └── 輸出: 公司規模/產業/營收/員工數/近期動態
      │
      ├── 4. 意圖強弱分析（Claude API）
      │      ├── 規格具體程度（1-30）
      │      ├── 數量明確性（1-30）
      │      ├── 交期急迫性（1-20）
      │      └── 企業背景評分（1-20）
      │
      ├── 5. 合併 Lead Score（1-100）
      │      └── 附帶: 判斷理由 + 建議行動
      │
      ├── 6. 生成草稿回覆信（Claude API）
      │
      └── 7. 通知派送
             ├── Score ≥ 80 → Slack 即時推送（A 級）
             ├── Score 50-79 → Email 通知（B 級）
             └── Score < 50 → 自動回覆（C 級）
```

#### 3.3.2 AI 數位業務分身（亮點四）

```
知識庫建構:
  影片逐字稿 + 產品型錄 + FAQ + 認證文件
      │
      ▼
  [Whisper API 轉錄] → [文件分段 Chunking]
      │
      ▼
  [Embedding: text-embedding-3-large]
      │
      ▼
  [儲存至 Pinecone（per-supplier namespace）]


對話流程:
  買家提問
      │
      ▼
  [語言偵測] → [翻譯至英文（若非英文）]
      │
      ▼
  [Pinecone 語意搜尋 Top-5 Chunks]
      │
      ▼
  [Claude API 生成回覆]
      ├── System Prompt: B2B 業務口吻、該供應商品牌語調
      ├── Context: Top-5 Chunks + 對話歷史
      ├── 回覆語言: 與買家提問語言一致
      └── 信心度評估: < 70% → 觸發「轉人工」
      │
      ▼
  [回覆翻譯至原語言] → [WebSocket 推送至前端]
      │
      ▼
  [對話記錄存入 PostgreSQL + 行為標記]
```

#### 3.3.3 訪客意圖分析（亮點二）

```
訪客進入供應商頁面
      │
      ├── [前端埋點] → 停留時長、影片觀看、頁面點擊
      ├── [RB2B SDK]  → 個人層級識別（姓名/職稱/LinkedIn）
      └── [Leadfeeder SDK] → 企業層級識別（公司/產業/規模）
      │
      ▼
[Webhook → /api/v1/webhooks/visitor]
      │
      ▼
[Celery Task: visitor_enrich_and_score]
      │
      ├── 行為評分
      │     ├── 停留 > 90 秒 → +20
      │     ├── 影片觀看 > 50% → +25
      │     ├── 多頁瀏覽 (≥3 頁) → +15
      │     └── RFQ 頁面進入 → +30
      │
      ├── 企業評分（Clay 富化）
      │     ├── 符合 ICP 產業 → +30
      │     ├── 公司規模 > 100 人 → +15
      │     └── 決策者職稱 → +20
      │
      └── 合併意圖分數 → 推送通知
            ├── Score ≥ 70 → Slack 即時推送
            └── Score < 70 → 儲存，靜默觀察
```

#### 3.3.4 Outbound 自動化引擎（Phase 3）

```
供應商設定 ICP 條件
      │
      ▼
[Clay API: 建立搜尋 + 瀑布式富化]
      │
      ├── LinkedIn Sales Navigator → 目標名單
      ├── Apollo → Work Email
      ├── Hunter → Email 驗證
      ├── Clearbit → 企業背景
      └── Claygent → 個人化開場白素材
      │
      ▼
[匯入平台 Outbound 管理]
      │
      ├── LinkedIn 通道 → HeyReach API
      │     Day 1: 瀏覽頁面
      │     Day 2: 按讚貼文
      │     Day 3: 連結請求（個人化訊息）
      │     Day 8: 第一封訊息
      │     Day 15: Follow-up
      │     Day 25: 最後跟進
      │
      └── Email 通道 → Instantly API
            Day 1: 個人化開場 + 影片連結
            Day 5: 客戶案例
            Day 12: 免費供應商評估報告
            Day 21: Breakup Email
      │
      ▼
[回覆偵測]
      ├── HeyReach Webhook → 標記熱線索
      ├── Instantly Webhook → 暫停序列
      └── 推送至業務工作台
```

#### 3.3.5 內容裂變 Pipeline（亮點五）

```
供應商上傳原始影片
      │
      ▼
[Celery Task: content_pipeline]
      │
      ├── Step 1: Whisper API 轉錄逐字稿
      │
      ├── Step 2: Claude API 生成內容矩陣
      │     ├── LinkedIn 貼文 × 30（含 CTA 變體）
      │     ├── SEO 部落格 × 10（長尾關鍵字佈局）
      │     └── YouTube 影片描述 × 6
      │
      ├── Step 3: OpusClip API 剪輯短影音 × 10
      │
      ├── Step 4: HeyGen API 多語系影片生成
      │     ├── 英語版
      │     ├── 德語版（字數壓縮處理）
      │     ├── 日語版
      │     └── 西班牙語版
      │
      └── Step 5: 排程發布
            ├── Repurpose.io → LinkedIn 每週 3-4 篇
            ├── Buffer → YouTube Shorts
            └── WordPress API → SEO 文章每月 2 篇
```

---

## 4. 資料庫設計

### 4.1 PostgreSQL 核心資料表

```sql
-- 用戶系統（統一身份）
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('buyer', 'supplier_admin', 'supplier_member', 'platform_admin')),
    name VARCHAR(255),
    preferred_language VARCHAR(5) DEFAULT 'en',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 供應商（工廠）
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    company_name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    industry VARCHAR(100),
    sub_industry VARCHAR(100),
    country VARCHAR(50) DEFAULT 'Taiwan',
    city VARCHAR(100),
    employee_count INTEGER,
    established_year INTEGER,
    certifications JSONB DEFAULT '[]',    -- ["ISO 9001", "CE", "UL"]
    capabilities JSONB DEFAULT '{}',      -- 產能、設備、材料
    moq INTEGER,
    lead_time_days INTEGER,
    payment_terms TEXT[],                 -- ["T/T", "L/C", "D/P"]
    description_zh TEXT,
    description_en TEXT,
    logo_url VARCHAR(500),
    cover_image_url VARCHAR(500),
    is_verified BOOLEAN DEFAULT false,
    is_published BOOLEAN DEFAULT false,
    subscription_plan VARCHAR(50),
    subscription_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 買家
CREATE TABLE buyers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    company_name VARCHAR(255),
    company_domain VARCHAR(255),
    industry VARCHAR(100),
    country VARCHAR(100),
    job_title VARCHAR(255),
    linkedin_url VARCHAR(500),
    company_size VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 影片
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id),
    video_type VARCHAR(20) NOT NULL CHECK (video_type IN ('factory_tour', 'qc_process', 'rd_capability', 'delivery', 'case_study', 'founder_intro')),
    title VARCHAR(255),
    original_url VARCHAR(500) NOT NULL,    -- S3 原始影片
    transcript_text TEXT,                  -- Whisper 逐字稿
    duration_seconds INTEGER,
    status VARCHAR(20) DEFAULT 'uploaded', -- uploaded / transcribing / ready
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 影片多語系版本
CREATE TABLE video_translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id),
    language VARCHAR(5) NOT NULL,          -- en, de, ja, es
    translated_url VARCHAR(500),           -- HeyGen 生成的影片
    heygen_job_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',  -- pending / processing / ready / failed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(video_id, language)
);

-- RFQ 詢價單
CREATE TABLE rfqs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id),
    buyer_id UUID REFERENCES buyers(id),
    buyer_email VARCHAR(255) NOT NULL,
    raw_text TEXT,                          -- 買家原始文字
    attachments JSONB DEFAULT '[]',        -- [{url, filename, type}]

    -- AI 解析結果
    parsed_specs JSONB,                    -- {material, dimensions, tolerance, surface_treatment, quantity, delivery}
    risk_flags JSONB DEFAULT '[]',         -- ["tight tolerance", "unusual material"]
    ai_summary TEXT,                       -- AI 規格摘要
    draft_reply TEXT,                      -- AI 草稿回覆

    -- Lead Scoring
    lead_score INTEGER,                    -- 1-100
    score_breakdown JSONB,                 -- {spec_clarity, quantity_clarity, urgency, company_profile}
    score_reason TEXT,                     -- AI 判斷理由
    suggested_action TEXT,                 -- AI 建議行動
    lead_grade VARCHAR(1),                 -- A / B / C

    -- 買家企業背景
    buyer_profile JSONB,                   -- Apollo.io 查詢結果

    -- 狀態管理
    status VARCHAR(20) DEFAULT 'received', -- received / parsing / scored / replied / closed
    supplier_reply TEXT,                   -- 供應商實際回覆
    replied_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 訪客行為
CREATE TABLE visitor_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id),

    -- 訪客身份（RB2B / Leadfeeder）
    visitor_name VARCHAR(255),
    visitor_email VARCHAR(255),
    visitor_company VARCHAR(255),
    visitor_job_title VARCHAR(255),
    visitor_linkedin_url VARCHAR(500),
    company_industry VARCHAR(100),
    company_size VARCHAR(50),
    company_country VARCHAR(100),
    identification_source VARCHAR(20),     -- rb2b / leadfeeder / registered

    -- 行為數據
    page_url VARCHAR(500),
    duration_seconds INTEGER,
    video_watch_percent INTEGER,
    pages_viewed INTEGER,
    entered_rfq_page BOOLEAN DEFAULT false,

    -- 意圖評分
    intent_score INTEGER,
    score_breakdown JSONB,
    enrichment_data JSONB,                 -- Clay 富化結果

    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Outbound 活動
CREATE TABLE outbound_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id),
    name VARCHAR(255) NOT NULL,
    icp_criteria JSONB NOT NULL,           -- {industry, country, job_title, company_size}
    status VARCHAR(20) DEFAULT 'draft',    -- draft / building_list / active / paused / completed

    -- Clay 名單建立
    clay_table_id VARCHAR(100),
    total_contacts INTEGER DEFAULT 0,
    enriched_contacts INTEGER DEFAULT 0,

    -- 外展設定
    linkedin_enabled BOOLEAN DEFAULT true,
    email_enabled BOOLEAN DEFAULT true,
    heyreach_campaign_id VARCHAR(100),
    instantly_campaign_id VARCHAR(100),

    -- 成效追蹤
    linkedin_sent INTEGER DEFAULT 0,
    linkedin_accepted INTEGER DEFAULT 0,
    linkedin_replied INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_replied INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Outbound 聯絡人
CREATE TABLE outbound_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES outbound_campaigns(id),

    -- 聯絡人資料
    name VARCHAR(255),
    email VARCHAR(255),
    linkedin_url VARCHAR(500),
    company VARCHAR(255),
    job_title VARCHAR(255),
    country VARCHAR(100),
    company_size VARCHAR(50),
    enrichment_data JSONB,                 -- Clay 完整富化資料
    personalized_opener TEXT,              -- AI 生成個人化開場白

    -- 序列狀態
    linkedin_status VARCHAR(20) DEFAULT 'pending',  -- pending / sent / accepted / replied
    email_status VARCHAR(20) DEFAULT 'pending',     -- pending / sent / opened / replied / bounced
    is_hot_lead BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 內容素材
CREATE TABLE content_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id),
    source_video_id UUID REFERENCES videos(id),
    content_type VARCHAR(20) NOT NULL,     -- linkedin_post / blog_article / short_video / youtube_desc
    language VARCHAR(5) DEFAULT 'en',
    title VARCHAR(255),
    body TEXT NOT NULL,
    media_url VARCHAR(500),                -- 短影音 URL
    seo_keywords JSONB DEFAULT '[]',

    -- 排程與發布
    scheduled_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    platform VARCHAR(50),                  -- linkedin / youtube / wordpress
    external_post_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'draft',    -- draft / scheduled / published / archived

    -- 成效
    impressions INTEGER DEFAULT 0,
    engagement INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI 分身對話
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id),
    buyer_id UUID REFERENCES buyers(id),
    visitor_session_id VARCHAR(100),
    language VARCHAR(5),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    transferred_to_human BOOLEAN DEFAULT false,
    transfer_reason TEXT,
    message_count INTEGER DEFAULT 0
);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(10) NOT NULL,             -- user / assistant / system
    content TEXT NOT NULL,
    confidence_score FLOAT,                -- AI 回覆信心度
    sources JSONB DEFAULT '[]',            -- RAG 引用來源
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 通知
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    type VARCHAR(50) NOT NULL,             -- hot_lead / rfq_received / visitor_alert / outbound_reply
    title VARCHAR(255) NOT NULL,
    body TEXT,
    metadata JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT false,
    channels JSONB DEFAULT '["web"]',      -- ["web", "slack", "email"]
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 訂閱方案
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id),
    plan VARCHAR(50) NOT NULL,             -- starter / professional / enterprise
    price_monthly_usd DECIMAL(10,2),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    features JSONB,                        -- 各方案功能開關
    stripe_subscription_id VARCHAR(100)
);

-- 索引
CREATE INDEX idx_rfqs_supplier_status ON rfqs(supplier_id, status);
CREATE INDEX idx_rfqs_lead_grade ON rfqs(lead_grade);
CREATE INDEX idx_visitor_events_supplier ON visitor_events(supplier_id, created_at DESC);
CREATE INDEX idx_visitor_events_intent ON visitor_events(intent_score DESC);
CREATE INDEX idx_outbound_contacts_campaign ON outbound_contacts(campaign_id, linkedin_status, email_status);
CREATE INDEX idx_content_items_supplier ON content_items(supplier_id, status, scheduled_at);
CREATE INDEX idx_conversations_supplier ON conversations(supplier_id, started_at DESC);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_suppliers_published ON suppliers(is_published, industry);
```

### 4.2 Pinecone 向量資料庫

```
Namespace 設計（per-supplier 隔離）:
  supplier_{uuid}/
    ├── video_transcripts    （影片逐字稿 chunks）
    ├── product_catalog      （產品型錄 chunks）
    ├── faq                  （FAQ chunks）
    └── certifications       （認證文件 chunks）

Embedding Model: text-embedding-3-large (OpenAI) 或 Cohere embed-v3
Dimension: 3072 (text-embedding-3-large)
Metric: cosine
```

### 4.3 Elasticsearch

```
Indices:
  suppliers/          → 供應商全文搜尋（名稱、產業、認證、能力、城市）
  content_items/      → 內容搜尋（標題、正文、關鍵字）
  rfqs/               → RFQ 搜尋（規格、材料）
```

---

## 5. 第三方 API 整合規範

### 5.1 整合矩陣

| 服務 | API 類型 | 觸發方式 | 數據流向 | 錯誤處理 |
|------|---------|---------|---------|---------|
| HeyGen | REST API | Celery Task | 上傳影片 → 取回多語版 | 重試 3 次 + 降級通知 |
| Claude/Anthropic | REST API | 同步 + 非同步 | RFQ 文字 → 解析結果 | Fallback: GPT-4o |
| Apollo.io | REST API | Celery Task | Email Domain → 企業背景 | 快取 24h + 降級跳過 |
| Clay | REST + Webhook | Celery Task | ICP → 富化名單 | 人工介入 |
| RB2B | Webhook (Push) | 被動接收 | Webhook → 訪客資料 | 冪等處理 |
| Leadfeeder | REST API + Webhook | 被動 + 排程拉取 | 訪客 IP → 企業身份 | 快取 + 降級 |
| HeyReach | REST API + Webhook | Celery Task | 名單 → LinkedIn 序列 | 速率限制尊重 |
| Instantly | REST API v2 + Webhook | Celery Task | 名單 → Email 序列 | Bounce 監控 |
| OpusClip | REST API | Celery Task | 長影片 → 短影音 | 重試 + 降級手動 |
| Jasper | REST API | Celery Task | 逐字稿 → 文案 | Fallback: Claude |
| Repurpose.io | REST API | 排程 Cron | 內容 → 跨平台發布 | 重試 + 告警 |
| Slack | Webhook | 即時推送 | 通知 → Slack 頻道 | 降級 Email |
| HubSpot | REST API | 雙向同步 | CRM 記錄同步 | Conflict Resolution |
| Stripe | REST API + Webhook | 訂閱管理 | 付款 → 訂閱狀態 | Webhook 冪等 |
| AWS Textract | REST API | Celery Task | PDF → OCR 文字 | Fallback: Claude Vision |
| AWS S3 | SDK | 直接上傳 | 檔案儲存 | Presigned URL |

### 5.2 API Key 管理

```python
# config.py — 所有 API Key 統一管理
# 環境變數載入，禁止硬編碼

ANTHROPIC_API_KEY=        # Claude API
OPENAI_API_KEY=           # Embedding + Fallback
HEYGEN_API_KEY=           # 影片多語系
CLAY_API_KEY=             # 數據富化
APOLLO_API_KEY=           # 企業背景
RB2B_WEBHOOK_SECRET=      # Webhook 驗證
LEADFEEDER_API_TOKEN=     # 訪客識別
HEYREACH_API_KEY=         # LinkedIn 自動化
INSTANTLY_API_KEY=        # Email 外展
OPUSCLIP_API_KEY=         # 短影音
JASPER_API_KEY=           # 內容生成
REPURPOSE_API_KEY=        # 跨平台分發
SLACK_WEBHOOK_URL=        # 通知推送
HUBSPOT_API_KEY=          # CRM
STRIPE_SECRET_KEY=        # 付款
STRIPE_WEBHOOK_SECRET=    # Stripe Webhook
AWS_ACCESS_KEY_ID=        # S3 + Textract
AWS_SECRET_ACCESS_KEY=
PINECONE_API_KEY=         # 向量 DB
PINECONE_ENVIRONMENT=
DATABASE_URL=             # PostgreSQL
REDIS_URL=                # Redis
ELASTICSEARCH_URL=        # 搜尋
```

---

## 6. 基礎設施

### 6.1 部署架構

```
                    ┌─────────────┐
                    │ Cloudflare  │
                    │   CDN/WAF   │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │    Nginx    │
                    │  (Gateway)  │
                    └──────┬──────┘
              ┌────────────┼────────────┐
              │            │            │
       ┌──────┴─────┐ ┌───┴────┐ ┌─────┴──────┐
       │  Vercel    │ │ AWS    │ │ AWS        │
       │  Next.js   │ │ ECS    │ │ ECS        │
       │  Frontend  │ │ FastAPI│ │ Celery     │
       │  (3 apps)  │ │ (x3)  │ │ Workers(x4)│
       └────────────┘ └───┬────┘ └─────┬──────┘
                          │            │
         ┌────────────────┼────────────┤
         │                │            │
  ┌──────┴──────┐  ┌──────┴──────┐  ┌──┴───┐
  │ RDS         │  │ ElastiCache │  │ S3   │
  │ PostgreSQL  │  │ Redis       │  │      │
  │ (Primary +  │  │ (Cluster)   │  └──────┘
  │  Read Replica│ └─────────────┘
  └─────────────┘
```

### 6.2 環境規劃

| 環境 | 用途 | 規格 |
|------|------|------|
| Development | 本地開發 | Docker Compose |
| Staging | 整合測試 | AWS (最小規格) |
| Production | 正式營運 | AWS (自動擴縮) |

### 6.3 Docker Compose（開發環境）

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/factory_insider
      - REDIS_URL=redis://redis:6379/0
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on: [db, redis, elasticsearch]

  celery-worker:
    build: ./backend
    command: celery -A app.tasks worker -l info -c 4
    depends_on: [db, redis]

  celery-beat:
    build: ./backend
    command: celery -A app.tasks beat -l info
    depends_on: [redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: factory_insider
      POSTGRES_PASSWORD: postgres
    volumes: [pgdata:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  elasticsearch:
    image: elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports: ["9200:9200"]

volumes:
  pgdata:
```

---

## 7. 安全與合規

### 7.1 安全措施

| 層級 | 措施 |
|------|------|
| 網路 | Cloudflare WAF + DDoS 防護 |
| API | JWT + Rate Limiting + CORS |
| 資料傳輸 | HTTPS/TLS 1.3 全站加密 |
| 資料儲存 | AES-256 加密（靜態資料）|
| 密碼 | bcrypt + salt |
| 檔案上傳 | MIME 驗證 + 病毒掃描 + S3 presigned URL |
| API Key | 環境變數 + AWS Secrets Manager |
| 日誌 | 不記錄 PII，敏感欄位脫敏 |

### 7.2 GDPR 合規清單

| 要求 | 實作方式 |
|------|---------|
| Cookie 同意 | 首次訪問彈出同意橫幅，未同意不啟動 RB2B/Leadfeeder |
| 資料刪除權 | 提供「刪除我的資料」API，72 小時內完成清除 |
| 資料可攜性 | 提供 JSON 格式資料匯出 |
| 隱私政策 | 明確說明數據蒐集目的與第三方共享範圍 |
| DPO | 指定資料保護聯絡人 |
| Email 退訂 | 每封外展信件必含 Unsubscribe Link (CAN-SPAM) |

### 7.3 台灣個資法合規

| 要求 | 實作方式 |
|------|---------|
| 告知義務 | 蒐集前告知目的、用途、保存期間 |
| 同意機制 | 明確取得書面或電子同意 |
| 存取權 | 當事人可查詢、補充、更正 |
| 安全維護 | 制定個資檔案安全維護計畫 |

---

## 8. 監控與 Observability

### 8.1 監控棧

| 工具 | 用途 |
|------|------|
| Sentry | 錯誤追蹤（前端 + 後端）|
| Prometheus + Grafana | 系統指標（CPU/Memory/API Latency）|
| AWS CloudWatch | 基礎設施監控 |
| Uptime Robot | 端點可用性監控 |
| Custom Dashboard | 第三方 API 用量 + 費用追蹤 |

### 8.2 關鍵告警規則

| 指標 | 閾值 | 通知管道 |
|------|------|---------|
| API 回應時間 P95 | > 2 秒 | Slack #engineering |
| 錯誤率 | > 1% | Slack + Email |
| Celery 佇列深度 | > 100 | Slack #engineering |
| 第三方 API 失敗率 | > 5% | Slack + PagerDuty |
| Email Bounce Rate | > 2% | Slack #operations |
| 資料庫連線池 | > 80% | Slack + PagerDuty |
| S3 儲存費用 | > 預算 120% | Email 管理層 |
