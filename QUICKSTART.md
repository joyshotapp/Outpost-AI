# Factory Insider Platform — 快速開始指南

> 已建立完整的專案目錄結構、技術文件、開發計畫

---

## 📦 已交付的核心文件

### 1. 技術文件

✅ **`docs/technical_architecture.md`** (969 行)
- 系統架構鳥瞰圖
- 前端 3 應用詳細設計（買家/供應商/管理）
- 後端 FastAPI 完整模組結構
- 核心 AI 流程（RFQ 解析 / AI 分身 / 訪客分析 / Outbound / 內容裂變）
- PostgreSQL 完整 Schema（13 張表）
- 15 個第三方 API 整合矩陣
- 安全與合規清單
- 基礎設施部署架構
- 監控與 Observability

✅ **`docs/development_plan.md`** (538 行)
- 14 個 Sprint / 7 個月完整計畫
- 140+ 具體 Task（每個都有負責人、天數、驗收標準）
- 9 人團隊職責分工
- 風險登記簿（10 項風險）
- 訂閱方案設計（Starter / Professional / Enterprise）
- 里程碑與 Go/No-Go 檢查點

### 2. 專案配置

✅ **`.env.example`** — 所有環境變數模板（API Keys、資料庫、AWS 等）

✅ **`docker-compose.yml`** — 完整本地開發環境
- PostgreSQL 16
- Redis 7
- Elasticsearch 8
- FastAPI Backend
- Celery Worker + Beat
- Nginx Gateway

✅ **`README.md`** — 專案總覽、快速開始、技術棧

✅ **`PROJECT_STRUCTURE.md`** — 完整目錄樹狀圖與目錄說明

✅ **`CLAUDE.md`** — Claude Code 專案指令（務必按計畫 / 真實 API / 完整交付）

### 3. 目錄結構

✅ **122 個子目錄** 已建立

```
frontend/              → 3 個 Next.js 應用 + 共享包
  ├── apps/buyer      → 買家前台
  ├── apps/supplier   → 供應商後台
  ├── apps/admin      → 管理後台
  └── packages/       → 共享 UI、工具、型別、Hooks

backend/              → FastAPI 後端
  ├── app/models/     → 13 個 ORM Model
  ├── app/api/v1/     → 20+ API 端點
  ├── app/services/   → AI + 整合 + 業務邏輯
  ├── app/tasks/      → Celery 非同步任務
  └── tests/          → 單元、整合、E2E 測試

infra/                → 基礎設施
  ├── terraform/      → AWS IaC
  ├── docker/         → 容器化配置
  ├── k8s/            → Kubernetes（選項）
  └── monitoring/     → 監控棧

docs/                 → 文件
  ├── api/            → API 端點文件
  ├── guides/         → 開發 / 部署 / 測試指南
  ├── tutorials/      → 實踐教學
  └── decisions/      → 架構決策記錄

.github/workflows/    → GitHub Actions CI/CD
```

---

## 🚀 下一步行動

### Phase 1：設定開發環境（Week 1）

```bash
# 1. 複製環境變數
cp .env.example .env.local
# ⚠️ 編輯 .env.local，填入所有第三方 API Key

# 2. 啟動 Docker 服務
docker-compose up -d

# 3. Backend 初始化
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
# → API 運行於 http://localhost:8000

# 4. Frontend 初始化（新終端機）
cd frontend
npm install
npm run dev
# → 買家前台：http://localhost:3000
# → 供應商後台：http://localhost:3001
# → 管理後台：http://localhost:3002

# 5. Celery Worker（新終端機）
cd backend
celery -A app.tasks worker -l info
```

### Phase 2：第三方 API 設定（Week 1-2）

申請以下帳號並填入 `.env.local`：

| 優先級 | 服務 | 用途 | 申請 URL |
|--------|------|------|---------|
| 🔴 高 | Claude API | RFQ 解析 + Lead Scoring | console.anthropic.com |
| 🔴 高 | HeyGen | 多語系影片 | heygen.com |
| 🔴 高 | Pinecone | 向量資料庫（AI 分身） | pinecone.io |
| 🟠 中 | Clay | 資料富化 | clay.com |
| 🟠 中 | Apollo.io | 企業背景 | apollo.io |
| 🟠 中 | RB2B | 訪客個人識別 | rb2b.com |
| 🟠 中 | Leadfeeder | 企業訪客識別 | leadfeeder.com |
| 🟡 低 | HeyReach | LinkedIn 自動化 | heyreach.io |
| 🟡 低 | Instantly | Email 外展 | instantly.ai |
| 🟡 低 | Stripe | 訂閱計費 | stripe.com |
| 🟡 低 | AWS | S3 + ECS | aws.amazon.com |

**詳見**：`docs/tutorials/third-party-setup.md`

### Phase 3：開始開發（Week 2+）

遵循開發計畫的 Sprint 進度：

```bash
# Sprint 1（Week 1-2）：基礎建設 + 認證系統
# Sprint 2（Week 3-4）：供應商 CRUD + 檔案上傳
# Sprint 3（Week 5-6）：RFQ 解析 + Lead Scoring（核心！）
# Sprint 4（Week 7-8）：AI 分身（RAG）
# ...
# Sprint 14（Week 27-28）：上線

# 建立 Feature Branch
git checkout -b feature/rfq-parsing

# 開發、測試、提交
git commit -m "feat(rfq): implement Claude-based parsing"
git push origin feature/rfq-parsing

# 建立 Pull Request
# → GitHub Actions 自動執行 Lint + Test
# → Code Review 通過
# → 自動部署至 Staging
```

---

## 📊 專案規模

| 項目 | 數量 |
|------|------|
| 子目錄 | 122 |
| 前端頁面 | ~50+ |
| 後端 API 端點 | ~20+ |
| 核心 AI 功能 | 6 個 |
| 第三方整合 | 15 個 |
| Sprint 計畫 | 14 個 |
| Task 總數 | 140+ |
| 技術文件 | 969+538 行 |

---

## 🎯 關鍵成功因素

### ✅ 已完成
- ✓ 完整技術架構設計
- ✓ 詳細開發計畫（14 Sprints）
- ✓ 目錄結構建立（122 子目錄）
- ✓ 環境配置模板
- ✓ Docker 開發環境
- ✓ CI/CD 框架

### ⚠️ 關鍵任務（需立即進行）

1. **第三方 API 申請**（Week 1-2）
   - 優先：Claude + HeyGen + Pinecone + Clay + Apollo
   - 缺乏真實 API Key 會阻礙整個 Sprint 3-8

2. **RFQ 解析 MVP**（Sprint 3）
   - 最難但最核心的功能
   - 需要 20+ 真實 RFQ 樣本進行 Prompt Engineering
   - 準確率必須 ≥ 80%

3. **AI 分身 RAG**（Sprint 4）
   - 決定整個平台的用戶體驗
   - 多語言幻覺率控制在 < 15%
   - 轉人工機制必須可靠

4. **冷啟動策略**（Month 1）
   - 無供應商無法驗證買家端功能
   - 必須招募 20-50 家台灣工廠參與 Beta
   - 預估需要 3-4 週才能有足夠數據

5. **團隊到位**（Week 1）
   - 需要 9 人團隊（見開發計畫）
   - AI 工程師最關鍵（RFQ 解析、Lead Scoring、RAG）
   - 整合工程師必須同步進行 15 個 API 串接

---

## 📖 重要文件快速連結

| 文件 | 用途 | 位置 |
|------|------|------|
| 技術架構 | 系統設計深度理解 | `docs/technical_architecture.md` |
| 開發計畫 | Sprint 執行 + Task 分配 | `docs/development_plan.md` |
| API 文件 | 端點與參數定義 | `docs/api/endpoints.md` |
| 部署指南 | Staging / Production 部署 | `docs/guides/deployment.md` |
| 第三方設定 | API 申請與配置 | `docs/tutorials/third-party-setup.md` |
| 專案指令 | Claude Code 規範 | `CLAUDE.md` |
| 目錄說明 | 每個目錄的用途 | `PROJECT_STRUCTURE.md` |

---

## 🔗 核心功能代碼位置預覽

### 亮點一：AI 多語系影片
```
Backend: backend/app/integrations/heygen.py
         backend/app/services/video_service.py
Frontend: frontend/apps/supplier/components/VideoUploader.tsx
```

### 亮點二：訪客意圖分析
```
Backend: backend/app/integrations/rb2b.py
         backend/app/integrations/leadfeeder.py
         backend/app/services/ai/intent_analyzer.py
Frontend: frontend/apps/supplier/app/visitors/page.tsx
```

### 亮點三：RFQ 自動解析
```
Backend: backend/app/services/ai/rfq_parser.py
         backend/app/api/v1/rfq.py
Frontend: frontend/apps/buyer/app/suppliers/[slug]/rfq/page.tsx
```

### 亮點四：AI 數位業務分身
```
Backend: backend/app/services/ai/chat_rag.py
         backend/app/api/v1/chat.py
Frontend: frontend/apps/buyer/components/ChatWidget.tsx
```

### 亮點五：內容裂變矩陣
```
Backend: backend/app/tasks/content_tasks.py
         backend/app/services/content_service.py
Frontend: frontend/apps/supplier/app/content/page.tsx
```

### 亮點六：Lead Scoring
```
Backend: backend/app/services/ai/lead_scorer.py
Frontend: frontend/apps/supplier/components/LeadScoringTable.tsx
```

---

## ⚙️ 技術棧一覽

```
Frontend:  Next.js 14 + TypeScript + Tailwind CSS + Zustand
Backend:   FastAPI + SQLAlchemy + PostgreSQL + Redis + Celery
AI/LLM:    Claude 3.5 Sonnet + Pinecone + OpenAI Embedding
Infra:     Docker + Terraform + AWS (ECS + RDS + ElastiCache)
Monitor:   Sentry + Prometheus + Grafana
Deploy:    GitHub Actions → Staging / Production
```

---

## 💡 常見問題

### Q: 可以先不做第三方 API 整合，用 Mock 資料嗎？
**A:** ❌ 不行。見 `CLAUDE.md` 規則 #2：「不使用模擬，全部用真實」。Mock 會掩蓋實際 API 問題（費用、限流、延遲），必須從一開始就用真實 API。

### Q: 開發順序可以改嗎，先做簡單的搜尋系統？
**A:** ❌ 不行。見 `CLAUDE.md` 規則 #3：「不要取巧選擇容易與小範圍任務」。開發計畫的順序是經過精心設計的：先做最難最有價值的 AI 功能（RFQ + 分身），不先做「容易但非核心」的功能。

### Q: 開發到一半發現計畫有問題？
**A:** ✅ 這是正常的。見 `CLAUDE.md` 規則 #1：「如果計畫轉出不可行，停止並報告」。有 Go/No-Go 檢查點在每個月結束時決定是否調整計畫。

### Q: 多久可以上線？
**A:** 7 個月（14 Sprint）。但實際上線時間取決於：
- 第三方 API 申請進度（關鍵路徑）
- 團隊到位情況
- 冷啟動供應商招募
- 首批用戶反饋迭代

---

## 🎓 推薦閱讀順序

1. **本文** — 快速概覽（5 分鐘）
2. **`CLAUDE.md`** — 專案指令（3 分鐘）
3. **`docs/technical_architecture.md`** — 技術深度（30 分鐘）
4. **`docs/development_plan.md`** — Sprint 計畫（20 分鐘）
5. **`docs/guides/setup.md`** — 開發環境（10 分鐘）
6. **`docs/tutorials/third-party-setup.md`** — API 設定（15 分鐘）

---

## 📞 聯絡與支援

- 📧 Email: contact@factoryinsider.com
- 📖 Docs: 見 `docs/` 資料夾
- 🐛 Bug Report: 見 `docs/guides/contributing.md`
- 💬 Questions: 在 PR 中詳細說明

---

**建立時間**：2026-02-28
**版本**：v1.0
**狀態**：✅ 就緒（Ready for Development）

**下一步**：複製 `.env.example` 並啟動 `docker-compose up -d`

祝開發順利！🚀
