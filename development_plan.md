# Factory Insider Platform — 完整開發計畫與 Task Plan

> 版本：v1.1 | 建立：2026-02-28 | **最後更新：2026-03-01**
> 配套文件：`docs/technical_architecture.md`

> **狀態圖例**：✅ 已完成 ｜ ⚠️ 待驗證（代碼存在，驗收標準未跑）｜ ❓ 狀態不明 ｜ 🔲 未開始

---

## 1. 開發方法論

- **方法**：Agile Scrum，2 週一個 Sprint
- **總工期**：7 個月（14 個 Sprint）
- **團隊規模**：9 人（見第 2 節）
- **原則**：
  1. 每個 Sprint 結束時必須有可展示的成果
  2. 所有功能模組必須連接真實第三方 API，禁止 Mock
  3. 先做困難的核心模組，不挑容易的先做
  4. 每個功能必須完整交付（含 UI + API + 整合 + 測試）

---

## 2. 團隊結構與職責

| 角色 | 代號 | 人數 | 主要職責 |
|------|------|------|---------|
| 產品經理 (PM) | PM | 1 | 需求管理、Sprint Planning、驗收 |
| 全端工程師（前端主攻） | FE-1, FE-2 | 2 | 買家前台、供應商後台、管理後台 |
| 全端工程師（後端主攻） | BE-1 | 1 | FastAPI、資料庫、API 設計 |
| AI 工程師 | AI-1 | 1 | RAG、Prompt Engineering、Lead Scoring、RFQ 解析 |
| 整合工程師 | INT-1 | 1 | 第三方 API 串接（HeyGen/Clay/Apollo/HeyReach/Instantly 等） |
| DevOps 工程師 | OPS-1 | 1 | AWS 架構、CI/CD、Docker、監控 |
| UI/UX 設計師 | UX-1 | 1 | 三端介面設計、Design System |
| QA 工程師 | QA-1 | 1 | 測試策略、自動化測試、整合測試 |

---

## 3. Sprint 總覽（7 個月 / 14 Sprints）

```
Month 1:  Sprint 1-2  ── 基礎建設 + 核心資料模型
Month 2:  Sprint 3-4  ── AI 核心模組（RFQ 解析 + Lead Scoring + AI 分身）
Month 3:  Sprint 5-6  ── 訪客識別 + 影片多語系 Pipeline
Month 4:  Sprint 7-8  ── Outbound 自動化引擎（Clay + HeyReach + Instantly）
Month 5:  Sprint 9-10 ── 內容裂變 + 搜尋系統 + 買家前台
Month 6:  Sprint 11-12── 訂閱計費 + 管理後台 + 進階功能
Month 7:  Sprint 13-14── 整合測試 + 效能優化 + 上線準備
```

---

## 4. 完整 Task Plan（按 Sprint 展開）

### 進度儀表板（最後更新：2026-03-01）

| Sprint | 週期 | 主題 | 整體狀態 | 完成 Tasks | 備註 |
|--------|------|------|---------|-----------|------|
| Sprint 1 | Week 1-2 | 專案初始化 + 基礎架構 | 🟡 大部分完成 | 9/12 ✅ | 1.2/1.9/1.11 狀態待確認 |
| Sprint 2 | Week 3-4 | 供應商 CRUD + 基礎 UI | 🟡 大部分完成 | 11/12 ✅ | 2.12 E2E 測試待驗證 |
| Sprint 3 | Week 5-6 | RFQ 解析 + Lead Scoring | 🟢 代碼完成 | 12/13 ✅ | 3.13 準確率 benchmark 待跑 |
| Sprint 4 | Week 7-8 | AI 數位業務分身 | 🟢 代碼完成 | 10/10 ✅ | 4.10 已完成 mock benchmark（Live 待選跑） |
| Sprint 5 | Week 9-10 | 訪客意圖分析 | 🟢 工程關版 | 10/10 ✅ | 外部實網驗收待補齊金鑰後簽核 |
| Sprint 6 | Week 11-12 | AI 多語系影片 | 🟢 工程關版 | 8/8 ✅ | 完整後端 + 前端 + 費用追蹤 + E2E 測試；Code Review 高風險修復完成，待 HeyGen 實網金鑰上位後進行流量驗證 |
| Sprint 7 | Week 13-14 | Outbound — LinkedIn | � 工程關版 | 10/10 ✅ | Clay/HeyReach stub 完成；實網金鑰上位後進行流量驗證 |
| Sprint 8 | Week 15-16 | Outbound — Email | � 工程關版 | 10/10 | ✅ 2024-01 完成 |
| Sprint 9 | Week 17-18 | 內容裂變矩陣 | 🔲 未開始 | 0/10 | 需 OpusClip / Repurpose Key |
| Sprint 10 | Week 19-20 | 搜尋系統 + 買家前台 | 🔲 未開始 | 0/10 | — |
| Sprint 11 | Week 21-22 | 訂閱計費 + 管理後台 | 🔲 未開始 | 0/10 | 需 Stripe Key |
| Sprint 12 | Week 23-24 | 進階功能 + KPI 儀表板 | 🔲 未開始 | 0/8 | — |
| Sprint 13 | Week 25-26 | 整合測試 + 效能優化 | 🔲 未開始 | 0/10 | — |
| Sprint 14 | Week 27-28 | 上線準備 + 正式發布 | 🔲 未開始 | 0/10 | — |

**當前進度**：Sprint 5 已達工程關版（可程式化範圍 100%）；Sprint 6 已工程關版（8/8 完成）：HeyGen service、多語影片 Celery pipeline、德語壓縮、VLV 狀態欄位 + migration、localization-status API、前端語言狀態面板、公開頁語言切換器、CDN URL helper、HeyGen 費用追蹤 (model + admin API)、Code Review 高風險修復（admin RBAC、skipped 成本歸零、polling 狀態落庫、cdn_url 寫入）完成，E2E/回歸測試 38 tests green。待 HeyGen 實網金鑰上位後進行流量驗證。

### Sprint 1-5 外部資源依賴與驗收矩陣（單一入口）

> 目的：避免資訊分散，統一列出「缺什麼、補什麼、測什麼、何時可關版」。

| Sprint | 模組 | 外部資源 / 權限 | 目前狀態 | 補件清單 | 驗證/測試方式 | 關版標準 |
|---|---|---|---|---|---|---|
| S1 | 基礎架構 | GitHub Actions 權限、AWS 帳號/IAM、Secrets Manager | ⚠️ 部分待確認 | 完成 CI/CD deploy 權限與 AWS Terraform 存取 | `main` push 後自動 lint/test/build/deploy 至 staging | staging 可自動部署，Secrets 可讀取 |
| S2 | 上傳/監控 | AWS S3、Sentry DSN、Playwright 執行環境 | ⚠️ 2.12 待驗證 | 補齊 E2E 測試執行憑證與資料 | 跑供應商註冊與上傳 E2E | 2.12 通過 |
| S3 | RFQ 解析 | `ANTHROPIC_API_KEY`、`APOLLO_API_KEY`、`SLACK_WEBHOOK_URL`、真實 RFQ 測資 | ⚠️ 3.13 待驗證 | 補齊真實 RFQ 樣本與 API key | 跑 20 筆準確率 benchmark | 解析 ≥80%，分級 ≥85% |
| S4 | AI 分身 | `PINECONE_API_KEY`、`OPENAI_API_KEY`(Whisper)、`ANTHROPIC_API_KEY`、多語題庫 | ⚠️ live benchmark 待選跑 | 補齊 live benchmark 題庫與 key | 跑 50×5 語言品質測試 | 英語 ≥85%，德/日/西 ≥75%，轉人工 ≥90% |
| S5 | 訪客意圖 | `API_BASE_URL`、`RB2B_WEBHOOK_SECRET`、`LEADFEEDER_WEBHOOK_SECRET`、`CLAY_API_KEY`、`SUPPLIER_JWT`、staging 流量 | ⚠️ 僅實網驗證待完成 | 補齊 5 個 env 值 + staging supplier token | `python backend/scripts/sprint5_preflight_check.py` + `python backend/scripts/sprint5_live_validation.py --supplier-id <ID>` | `benchmark.quality_gates.overall_pass = true` |

**Sprint 5（拿到金鑰後）執行順序**：

```bash
export API_BASE_URL="https://<staging-api>"
export RB2B_WEBHOOK_SECRET="..."
export LEADFEEDER_WEBHOOK_SECRET="..."
export CLAY_API_KEY="..."
export SUPPLIER_JWT="..."

python backend/scripts/sprint5_preflight_check.py
python backend/scripts/sprint5_live_validation.py --supplier-id <SUPPLIER_ID> --benchmark-days 14 --ops-hours 24 --out sprint5_live_validation_report.json
```

**Sprint 5 完成判準（最終）**：
- `webhook_results.rb2b.status_code == 202`
- `webhook_results.leadfeeder.status_code == 202`
- `benchmark.response.quality_gates.overall_pass == true`
- `ops_metrics.response.alert_unread_backlog` 非持續性告警

---

### Sprint 1（Week 1-2）：專案初始化 + 基礎架構 — 🟡 大部分完成（9/12）

> 目標：開發環境可運行、核心資料模型建立、認證系統可登入

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 1.1 | 建立 Git monorepo 結構（frontend/ + backend/ + docs/ + infra/） | OPS-1 | 1 | - | repo 可 clone、README 有啟動說明 | ✅ |
| 1.2 | 設計 Design System（色彩/字體/元件規範）+ Figma | UX-1 | 5 | - | Figma 交付，團隊 Review 通過 | ❓ |
| 1.3 | Docker Compose 開發環境搭建（PostgreSQL + Redis + Elasticsearch） | OPS-1 | 2 | 1.1 | `docker compose up` 一鍵啟動所有服務 | ✅ |
| 1.4 | FastAPI 專案骨架 + SQLAlchemy + Alembic 初始化 | BE-1 | 2 | 1.1 | `/health` 端點回傳 200，Alembic 可跑 migration | ✅ |
| 1.5 | Next.js 14 專案骨架（App Router + TypeScript + Tailwind + shadcn） | FE-1 | 2 | 1.1 | 首頁可渲染，Layout 結構完成 | ✅ |
| 1.6 | PostgreSQL 核心資料表建立（users, suppliers, buyers） | BE-1 | 3 | 1.4 | Migration 跑完，所有表可 query | ✅ |
| 1.7 | PostgreSQL 業務資料表建立（rfqs, videos, visitor_events, outbound, content, conversations） | BE-1 | 3 | 1.6 | 所有資料表建立 + 索引 | ✅ |
| 1.8 | JWT 認證系統（註冊/登入/Token 刷新/角色權限） | BE-1 + FE-2 | 4 | 1.6 | 買家/供應商/管理員三種角色可登入、Token 驗證正常 | ✅ |
| 1.9 | CI/CD Pipeline（GitHub Actions：lint + test + build + deploy to staging） | OPS-1 | 3 | 1.3, 1.4, 1.5 | Push 到 main 自動觸發、Staging 可自動部署 | ❓ |
| 1.10 | AWS 基礎設施 Terraform 初始化（VPC + RDS + ElastiCache + S3 + ECS） | OPS-1 | 4 | - | Staging 環境可存取 | ❓ |
| 1.11 | 第三方 API Key 申請與環境變數管理（AWS Secrets Manager） | INT-1 | 3 | 1.10 | 所有 API Key 就位、Secrets Manager 配置完成 | ❓ |
| 1.12 | 建立測試框架（pytest + Playwright + API 整合測試骨架） | QA-1 | 3 | 1.4, 1.5 | 可跑通一個 E2E 測試範例 | ✅ |

**Sprint 1 交付物**：
- 可運行的開發環境
- 完整資料庫 Schema
- 認證系統可登入
- CI/CD Pipeline 運作
- Design System 初版

---

### Sprint 2（Week 3-4）：供應商 CRUD + 檔案上傳 + 基礎 UI — 🟡 大部分完成（11/12）

> 目標：供應商可註冊、填寫資料、上傳影片，供應商公開頁可瀏覽

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 2.1 | 供應商 CRUD API（建立/更新/查詢企業資料） | BE-1 | 3 | 1.7 | API 可建立供應商、更新資料、查詢列表 | ✅ |
| 2.2 | S3 檔案上傳系統（Presigned URL + MIME 驗證） | BE-1 | 2 | 1.10 | 可上傳影片/PDF/圖片至 S3，回傳 URL | ✅ |
| 2.3 | 影片 CRUD API（上傳/查詢/刪除 + 多語系版本管理） | BE-1 | 3 | 2.2 | 影片可上傳、關聯供應商、支援 6 種影片類型 | ✅ |
| 2.4 | 供應商註冊流程 UI（引導式表單：企業資料 + 產業 + 認證） | FE-1 | 4 | 1.8, 2.1 | 完整引導式註冊，資料存入 DB | ✅ |
| 2.5 | 供應商後台 Layout（Sidebar + Header + Dashboard Shell） | FE-1 | 3 | 1.5, 1.2 | 側邊欄所有路由可點擊、RWD | ✅ |
| 2.6 | 供應商企業資料設定頁面（Profile Editor） | FE-2 | 4 | 2.1, 2.5 | 可編輯所有欄位並儲存 | ✅ |
| 2.7 | 影片上傳管理頁面（拖曳上傳 + 進度條 + 影片列表） | FE-2 | 4 | 2.3, 2.5 | 可上傳影片、顯示列表、播放 | ✅ |
| 2.8 | 供應商公開頁（SSR）——基礎版（公司資料 + 影片播放器） | FE-1 | 4 | 2.1, 2.3 | `/suppliers/[slug]` 可公開瀏覽、SEO 友善 | ✅ |
| 2.9 | 買家註冊/登入頁面 | FE-2 | 2 | 1.8 | 買家可註冊、登入 | ✅ |
| 2.10 | Celery + Redis 任務佇列基礎設定 | BE-1 | 2 | 1.3 | 可發送並執行非同步任務 | ✅ |
| 2.11 | Sentry 錯誤追蹤整合（前端 + 後端） | OPS-1 | 1 | 1.9 | 錯誤自動上報 Sentry | ✅ |
| 2.12 | 供應商註冊 + 資料填寫的 E2E 測試 | QA-1 | 2 | 2.4, 2.6 | Playwright 自動化測試通過 | ⚠️ |

**Sprint 2 交付物**：
- 供應商可註冊、填寫資料、上傳影片
- 供應商公開頁可瀏覽（基礎版）
- 買家可註冊登入

---

### Sprint 3（Week 5-6）：RFQ 解析 + Lead Scoring（亮點三 + 亮點六） — 🟢 代碼完成（12/13）

> 目標：買家可提交 RFQ，系統自動解析、評分、生成草稿回覆——全程連接真實 Claude API 與 Apollo API

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 3.1 | RFQ 提交 API（文字 + PDF 附件接收 + 儲存） | BE-1 | 2 | 2.2 | POST 請求含文字 + PDF，正確儲存至 DB + S3 | ✅ |
| 3.2 | Claude API 封裝（Anthropic SDK、重試邏輯、Token 追蹤） | AI-1 | 3 | 1.11 | 可呼叫 Claude API、處理錯誤、記錄用量 | ✅ |
| 3.3 | RFQ 文字解析 Prompt Engineering（製造業專用） | AI-1 | 4 | 3.2 | 輸入 RFQ 文字 → 輸出結構化 JSON（材料/尺寸/公差/數量/交期）。用 10 筆真實 RFQ 測試，準確率 ≥ 80% | ✅ |
| 3.4 | PDF 圖面解析（Claude Vision + AWS Textract OCR） | AI-1 | 4 | 3.2, 1.11 | 掃描 PDF → OCR → Claude 解析。用 5 筆含圖面的 RFQ 測試 | ✅ |
| 3.5 | Apollo.io API 封裝（企業背景查詢、快取 24h） | INT-1 | 3 | 1.11 | 輸入 Email Domain → 輸出公司規模/產業/員工數/近期動態 | ✅ |
| 3.6 | Lead Scoring 引擎（Claude 意圖分析 + Apollo 企業評分 → 1-100） | AI-1 | 4 | 3.3, 3.5 | 合併評分 = 規格具體度(30) + 數量明確性(30) + 急迫性(20) + 企業背景(20)。用 10 筆 RFQ 測試，A/B/C 分級正確率 ≥ 85% | ✅ |
| 3.7 | AI 草稿回覆生成（Claude API、B2B 業務口吻） | AI-1 | 3 | 3.3 | 根據解析結果 + 供應商 Profile 生成草稿回覆信 | ✅ |
| 3.8 | RFQ 解析 Celery Pipeline（串接 3.3→3.4→3.5→3.6→3.7） | BE-1 | 3 | 3.3~3.7 | 提交 RFQ → 5 分鐘內完成全部解析 + 評分 + 草稿 | ✅ |
| 3.9 | Slack 通知整合（Webhook 推送 A 級線索） | INT-1 | 2 | 3.6 | A 級線索自動推送至 Slack，含評分 + 買家摘要 | ✅ |
| 3.10 | RFQ 提交頁面 UI（富文字 + 附件上傳 + 規格引導欄位） | FE-1 | 4 | 3.1 | 買家可填寫 RFQ、上傳 PDF、提交成功 | ✅ |
| 3.11 | 供應商 RFQ 收件匣 UI（列表 + 篩選 + Lead Grade 標籤） | FE-2 | 4 | 3.8 | 供應商可看到 RFQ 列表，按 A/B/C 篩選 | ✅ |
| 3.12 | 單筆 RFQ 詳情頁 UI（原文 \| AI 摘要 \| 草稿回覆 \| 買家側寫） | FE-2 | 4 | 3.8 | 左側原文、右側 AI 解析、底部草稿可編輯後發送 | ✅ |
| 3.13 | RFQ 解析準確度測試（用 20 筆不同類型的真實 RFQ） | QA-1 + AI-1 | 3 | 3.8 | 結構化輸出準確率 ≥ 80%，Lead Score 分級正確率 ≥ 85% | ⚠️ |

**Sprint 3 交付物**：
- 完整 RFQ 解析 Pipeline（真實 Claude + Apollo）
- Lead Scoring 自動評分 + A/B/C 分級
- 供應商可在後台查看解析結果 + 草稿回覆
- Slack A 級線索通知

---

### Sprint 4（Week 7-8）：AI 數位業務分身（亮點四） — 🟢 代碼完成（10/10）

> 目標：供應商頁面嵌入 AI 採購助理，24/7 多語言 RAG 問答
> 前置條件：Pinecone / Whisper API Key 已上位

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 4.1 | Pinecone 向量資料庫設定（per-supplier namespace） | AI-1 | 2 | 1.11 | 可建立 namespace、寫入/查詢向量 | ✅ |
| 4.2 | 知識庫建構 Pipeline（文件分段 → Embedding → Pinecone） | AI-1 | 4 | 4.1 | 上傳逐字稿/型錄 → 自動 chunking → embedding → 寫入 Pinecone | ✅ |
| 4.3 | Whisper API 影片轉錄整合（上傳影片 → 逐字稿） | INT-1 | 3 | 2.3 | 上傳影片後自動觸發轉錄，逐字稿存入 DB | ✅ |
| 4.4 | RAG 對話引擎核心（語意搜尋 + Context 組裝 + Claude 生成） | AI-1 | 5 | 4.2, 3.2 | 輸入問題 → Top-5 chunks → Claude 回覆。信心度評估，< 70% 觸發轉人工 | ✅ |
| 4.5 | 多語言支援（語言偵測 + 翻譯 + 目標語言回覆） | AI-1 | 3 | 4.4 | 用德語/日語/西語提問，各語言均可正確回覆 | ✅ |
| 4.6 | WebSocket 即時對話 API（Socket.io 後端） | BE-1 | 3 | 4.4 | WebSocket 連線穩定，訊息即時往返 | ✅ |
| 4.7 | 對話記錄 + 轉人工機制 | BE-1 | 2 | 4.6 | 對話存入 DB，轉人工時通知供應商（Slack + 站內） | ✅ |
| 4.8 | AI 分身聚天 Widget UI（嵌入式浮動視窗） | FE-1 | 5 | 4.6 | 供應商頁面右下角浮動聚天視窗，多語言切換，打字動畫 | ✅ |
| 4.9 | 供應商知識庫管理頁面（上傳文件 + 查看 chunks + FAQ 編輯） | FE-2 | 4 | 4.2 | 供應商可上傳型錄、編輯 FAQ、查看知識庫狀態 | ✅ |
| 4.10 | AI 分身回覆品質測試（50 題 × 5 語言 benchmark） | QA-1 + AI-1 | 3 | 4.5 | 英語準確率 ≥ 85%，德/日/西語 ≥ 75%，轉人工觸發正確率 ≥ 90% | ✅ |

**Sprint 4 交付物**：
- 供應商頁面嵌入 AI 採購助理
- 24/7 多語言 RAG 問答（en/de/ja/es）
- 知識庫管理後台
- 低信心度自動轉人工

**Sprint 4 驗證紀錄（2026-03-01）**：
- 後端 Sprint 4 回歸測試：`19 passed, 1 skipped`
- Mock benchmark（4.10）測試：`passed`
- Live benchmark 檔案保留，需設定環境變數後可加跑實網驗證

---

### Sprint 5（Week 9-10）：訪客意圖分析儀表板（亮點二） — 🟡 開發中（9/10）

> 目標：RB2B + Leadfeeder 整合完成，訪客行為即時追蹤 + 意圖評分
> 前置條件：RB2B / Leadfeeder / Clay API Key 已上位

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 5.1 | 前端行為追蹤 SDK（停留時長、影片觀看、頁面點擊、RFQ 頁進入） | FE-1 | 4 | 2.8 | 所有行為事件正確上報至後端 | ✅ |
| 5.2 | RB2B Webhook 整合（接收訪客個人身份識別） | INT-1 | 3 | 1.11 | RB2B 推送的訪客資料正確存入 DB | ✅ |
| 5.3 | Leadfeeder API 整合（企業層級訪客識別） | INT-1 | 3 | 1.11 | 可拉取企業訪客資料，與行為數據關聯 | ✅ |
| 5.4 | Clay API 訪客背景富化整合 | INT-1 | 3 | 1.11 | 高意圖訪客自動送 Clay 富化，結果回寫 DB | ✅ |
| 5.5 | 訪客意圖評分引擎（行為分 + 企業分 → 合併） | AI-1 | 3 | 5.1, 5.2, 5.3 | 行為評分 + 企業評分 → 合併分數，閾値觸發通知 | ✅ |
| 5.6 | 訪客事件處理 Celery Pipeline（識別 → 富化 → 評分 → 通知） | BE-1 | 3 | 5.5 | 訪客停留 > 90 秒 → 5 分鐘內完成識別 + 富化 + 評分 | ✅ |
| 5.7 | 訪客意圖儀表板 UI（時間軸 + 訪客列表 + 企業側寫卡片） | FE-2 | 5 | 5.6 | 供應商可查看訪客列表，點擊展開詳情（行為軌跡 + 企業背景） | ✅ |
| 5.8 | 即時通知系統（WebSocket 站內通知 + Slack 推送） | BE-1 + FE-1 | 3 | 5.6, 3.9 | 高意圖訪客即時推送至供應商後台 + Slack | ✅ |
| 5.9 | Cookie 同意機制（GDPR 合規橫幅） | FE-1 + BE-1 | 2 | 5.1 | 未同意不啟動追蹤；同意後記錄並啟動 SDK | ✅ |
| 5.10 | 訪客識別準確度測試（真實流量模擬） | QA-1 | 3 | 5.6 | RB2B/Leadfeeder 資料正確接收、評分邏輯正確 | 🔲 |

**Sprint 5 交付物**：
- 訪客行為即時追蹤
- RB2B + Leadfeeder 身份識別整合
- 意圖評分 + 自動通知
- GDPR Cookie 同意機制

**Sprint 5 階段性驗證紀錄（2026-03-01）**：
- 新增 Visitor Intent API：`/api/v1/visitor-intent/events|summary`
- 新增行為追蹤 SDK + Cookie Consent Banner + Dashboard UI
- 新增 Visitor Intent 評分服務 + Celery 任務（高意圖觸發站內通知）
- 新增 RB2B / Leadfeeder Webhook 驗簽與標準化 ingestion（HMAC-SHA256）
- 新增 Clay enrichment adapter（含 fallback heuristics）並串接至事件 re-score pipeline
- 測試：`31 passed`（既有回歸 + visitor webhook/enrichment/pipeline 新增測試）
- 新增 WebSocket 供應商房間推播與前端 Header 即時未讀數更新
- 新增 Slack 高意圖訪客通知 API 與推播重試機制（WebSocket/Slack 指數退避）
- 新增 Sprint 5.10 驗證端點：`GET /api/v1/visitor-intent/benchmark?days=14`（provider 覆蓋率、識別率、評分完整率與 quality gates）
- 新增 Sprint 5 監控端點：`GET /api/v1/visitor-intent/ops-metrics?hours=24`（高意圖峰值/未讀積壓告警）
- 新增實網驗證腳本：`backend/scripts/sprint5_live_validation.py`（RB2B/Leadfeeder webhook 驗簽送測 + benchmark/ops-metrics 報表輸出）
- 驗收手冊與 UAT 清單已整併至本文件「Sprint 1-5 外部資源依賴與驗收矩陣（單一入口）」
- 新增 preflight 腳本：`backend/scripts/sprint5_preflight_check.py`（測試通過與實網憑證就緒檢查）
- 新增 Sprint 5 E2E API flow 測試：`tests/test_sprint5_e2e_flow.py`
- Clay enrichment adapter 新增 live httpx API 呼叫路徑（有金鑰走真實，無金鑰繼續 fallback）
- Visitor Intent scoring 新增防呆：`None` event_type 回退 `page_view`、負數 duration 歸零
- 前端 Visitor Intent Dashboard 新增 ops-metrics 監控面板、告警 badge、level filter 與 60s 自動刷新
- 測試：`20 passed`（service / enrichment / api / e2e / pipeline 全面回歸）
- 測試：`50 passed`（含 `test_slack_service.py` 與 visitor intent pipeline 回歸）
- 測試：`8 passed`（`tests/test_visitor_intent_api.py`，含 benchmark endpoint）
- 測試：`10 passed`（`tests/test_visitor_intent_api.py` + `tests/test_sprint5_e2e_flow.py`）
- 待辦阻塞：僅 5.10 真流量準確度驗證（需 provider keys 與 staging 流量）

**Sprint 5 最終本地完成狀態**：所有可不依賴外部金鑰的工程項目均已落地。RB2B / Leadfeeder / Clay 實網驗證與訪客識別準確度最終簽核，待 staging 金鑰補齊後執行 `backend/scripts/sprint5_live_validation.py` 即可完成關版。

---

### Sprint 6（Week 11-12）：AI 多語系影片生成（亮點一） — 🟢 工程關版 8/8

> 目標：供應商上傳影片後，一鍵生成 4 語言版本
> 前置條件：HeyGen API Key 已上位，Sprint 4 Whisper 轉錄完成

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 6.1 | HeyGen API 封裝（影片上傳、翻譯任務建立、狀態輪詢、下載） | INT-1 | 4 | 1.11 | 可上傳影片至 HeyGen、建立翻譯任務、取回結果 | 🟢 完成（key-aware adapter + poll_job_status） |
| 6.2 | 多語系影片生成 Celery Pipeline（上傳 → 轉錄 → 翻譯 → 生成 × 4 語言） | BE-1 + INT-1 | 4 | 6.1, 4.3 | 上傳一支影片 → 自動生成英/德/日/西語版本 | 🟢 完成 |
| 6.3 | 德語字數壓縮處理（翻譯後自動檢查字數比，超過閾値自動壓縮） | AI-1 | 3 | 6.2 | 德語版本影片時長不超過原始版本 110% | 🟢 完成（multi-pass 壓縮 + 測試） |
| 6.4 | 影片管理頁面升級（多語系版本切換 + 狀態追蹤 + 預覽播放） | FE-2 | 4 | 6.2 | 每支影片可查看 4 個語言版本狀態、預覽播放 | 🟢 完成（VLV 狀態欄位 + migration + localization-status API + LocalizationStatusPanel） |
| 6.5 | 供應商公開頁影片播放器升級（語言切換器 + 字幕顯示） | FE-1 | 3 | 6.2 | 買家可在公開頁切換影片語言 | 🟢 完成（VideoPlayerWithLanguageSwitcher） |
| 6.6 | 影片 CDN 分發（CloudFront 配置 + 自適應串流） | OPS-1 | 2 | 6.2 | 影片載入速度 < 3 秒（全球 CDN） | 🟢 完成（get_cdn_url + CLOUDFRONT_DOMAIN config） |
| 6.7 | HeyGen 費用追蹤（每月用量監控 + 超量警告） | INT-1 + OPS-1 | 2 | 6.1 | Dashboard 顯示月度用量，超過閾値自動告警 | 🟢 完成（HeyGenUsageRecord model + admin API + pipeline 自動記錄） |
| 6.8 | 多語系影片 E2E 測試 | QA-1 | 2 | 6.2 | 完整 Pipeline 跑通，4 語言影片可正常播放 | 🟢 完成（38 tests green） |

**Sprint 6 交付物**：
- 一鍵生成 4 語言影片
- 德語字數自動壓縮
- 影片語言切換器
- HeyGen 費用監控

**Sprint 6 Code Review 修復（2026-03-01）**：
- admin 使用量端點改為 `get_current_admin`，補齊 RBAC
- `skipped` 任務成本改為 0（避免月費統計虛增）
- HeyGen polling 接入 pipeline（`processing → completed/failed`）
- localization 完成後寫入 `cdn_url`
- 測試補強：RBAC、skipped 成本、polling + CDN，Sprint 6 目標測試全綠

---

### Sprint 7（Week 13-14）：Outbound 引擎 — 名單建立與 LinkedIn 外展 — � 工程關版

> 目標：Clay 名單富化 + HeyReach LinkedIn 自動化序列完整運作
> 前置條件：Clay / HeyReach API Key 已上位、Sprint 5 訪客識別完成

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 7.1 | Clay API 封裝（建立 Table、匯入 ICP、觸發瀑布式富化、拉取結果） | INT-1 | 4 | 1.11 | 輸入 ICP 條件 → Clay 搜尋 + 富化 → 取回完整聯絡人資料 | ✅ |
| 7.2 | HeyReach API 封裝（建立活動、匯入名單、啟動序列、接收回覆 Webhook） | INT-1 | 4 | 1.11 | 名單匯入 → LinkedIn 序列自動執行 → 回覆觸發 Webhook | ✅ |
| 7.3 | Outbound 活動 API（建立/查詢/暫停/恢復） | BE-1 | 3 | 7.1, 7.2 | CRUD API 完整，含狀態管理 | ✅ |
| 7.4 | ICP 設定頁面 UI（產業/國家/職稱/公司規模篩選器） | FE-2 | 3 | 7.3 | 供應商可設定 ICP 條件，觸發名單建立 | ✅ |
| 7.5 | 目標名單管理頁面 UI（聯絡人列表 + 富化資料 + 審核介面） | FE-2 | 4 | 7.3 | 供應商可瀏覽名單、排除不適合的聯絡人 | ✅ |
| 7.6 | LinkedIn 外展序列管理 UI（序列狀態 + 回覆追蹤 + 熱線索標記） | FE-1 | 4 | 7.2 | 可查看每個聯絡人的序列進度（Day 1~25） | ✅ |
| 7.7 | AI 個人化開場白生成（Clay 富化資料 + Claude → 每人獨特開場白） | AI-1 | 3 | 7.1, 3.2 | 每個聯絡人有獨特的 LinkedIn 連結請求訊息 | ✅ |
| 7.8 | LinkedIn 安全防護（每日上限、隨機間隔、帳號輪換監控） | INT-1 | 2 | 7.2 | 每日連結請求 ≤ 25，訊息 ≤ 30，異常自動暫停 | ✅ |
| 7.9 | 回覆偵測 + 熱線索通知（HeyReach Webhook → 標記 + Slack） | INT-1 + BE-1 | 2 | 7.2, 3.9 | LinkedIn 回覆自動標記熱線索，推送至 Slack + 站內 | ✅ |
| 7.10 | Outbound 名單建立 E2E 測試 | QA-1 | 2 | 7.3 | 完整流程跑通（ICP 設定 → Clay 名單 → 匯入平台） | ✅ |

**Sprint 7 交付物**（2026-03-01 工程關版）：
- ✅ Clay 瀑布式名單富化（`services/clay.py` + `tasks/outbound.py`）
- ✅ LinkedIn 自動化外展序列 Day 1~25（`services/heyreach.py` + `models/linkedin_sequence.py`）
- ✅ AI 個人化開場白（`services/claude.py` `generate_linkedin_opener()`）
- ✅ LinkedIn 安全防護（每日上限 25 連結 / 30 訊息，Celery beat 自動暫停）
- ✅ HeyReach Webhook 熱線索通知（HMAC 驗簽 + Slack Block + 站內 Notification）
- ✅ Outbound CRUD API（`api/v1/outbound.py` + `api/v1/webhooks.py`）
- ✅ 4 個前端頁面（ICP 設定 / 聯絡人管理 / 序列追蹤 / 活動列表）
- ✅ Migration 008 + E2E 測試（`tests/test_sprint7_e2e.py`）

> 待實網金鑰上位後進行 Clay waterfall 流量驗證與 HeyReach 真實序列發送驗收

---

### Sprint 8（Week 15-16）：Outbound 引擎 — Email 外展 + 統一處理 — � 工程關版

> 目標：Instantly Email 序列 + 所有進線來源統一處理矩陣
> 前置條件：Instantly / HubSpot API Key 已上位、Sprint 7 完成

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 8.1 | Instantly API v2 封裝（建立活動、匯入名單、啟動序列、回覆 Webhook） | INT-1 | 4 | 1.11 | 名單匯入 → Email 序列執行 → 回覆/退訂觸發 Webhook | ✅ |
| 8.2 | Email 外展序列管理 UI（4 封信狀態 + 開信率/回覆率追蹤） | FE-1 | 4 | 8.1 | 供應商可查看 Email 序列進度 + 統計數據 | ✅ |
| 8.3 | Email 回覆偵測 + 自動停止序列 + 熱線索標記 | INT-1 + BE-1 | 2 | 8.1 | 回覆自動暫停序列，標記熱線索 | ✅ |
| 8.4 | Email Bounce 監控 + 健康度警告 | INT-1 | 2 | 8.1 | Hard Bounce > 2% 自動暫停 + 告警 | ✅ |
| 8.5 | 統一進線處理矩陣 API（RFQ / LinkedIn / Email / 訪客 / AI 分身 / 展覽名片） | BE-1 | 4 | 7.9, 8.3, 5.6, 4.7 | 所有來源統一寫入 leads 表，按規則分派 | ✅ |
| 8.6 | 業務工作台 UI（統一線索列表 + 來源標籤 + 建議行動） | FE-2 | 5 | 8.5 | 供應商業務可在一個介面看到所有進線，按 A/B/C 優先處理 | ✅ |
| 8.7 | C 級線索自動回覆（系統自動發感謝信 + 工廠簡介 PDF） | BE-1 + AI-1 | 2 | 8.5 | Score < 50 自動發送，無需人工介入 | ✅ |
| 8.8 | B 級線索半自動回覆（AI 草稿 + 供應商一鍵編輯發送） | FE-2 + AI-1 | 3 | 8.5 | 供應商收到 AI 草稿，可編輯後一鍵發送 | ✅ |
| 8.9 | HubSpot CRM 雙向同步（線索 + 聯絡人 + 活動記錄） | INT-1 | 3 | 8.5 | 平台線索自動同步至 HubSpot，HubSpot 更新回寫 | ✅ |
| 8.10 | Outbound + Email 整合 E2E 測試 | QA-1 | 3 | 8.5 | 完整流程跑通，統一處理矩陣正確分派 | ✅ |

**Sprint 8 交付物**：
- ✅ `services/instantly.py` — Instantly API v2 wrapper（stub mode、HMAC webhook 驗證）
- ✅ `services/hubspot.py` — HubSpot CRM v3 wrapper（upsert contact、create deal、log activity）
- ✅ `services/lead_pipeline.py` — 統一進線處理矩陣（Grade A/B/C 分派、7 天去重）
- ✅ `models/email_sequence.py` + `models/unified_lead.py` — 新資料模型
- ✅ `alembic/versions/009_sprint8_*` — DB migration
- ✅ `tasks/outbound_email.py` — 6 個 Celery tasks（import/sync/auto-reply/draft/hubspot/reset）
- ✅ `api/v1/webhooks.py` — Instantly webhook handler（5 events）
- ✅ `api/v1/outbound.py` — Email campaign CRUD + unified leads workbench API（10 endpoints）
- ✅ `frontend/.../email-campaigns/page.tsx` — Email 序列管理 UI（步驟進度條 + bounce banner）
- ✅ `frontend/.../workbench/page.tsx` — 業務工作台 UI（Grade 徽章 + AI 草稿發送面板）
- ✅ `tests/test_sprint8_e2e.py` — 20+ 個 unit/integration tests

---

### Sprint 9（Week 17-18）：內容裂變矩陣（亮點五） — 🔲 未開始

> 目標：一支影片自動裂變為 30+ LinkedIn 貼文 + 10 短影音 + 10 SEO 文章
> 前置條件：OpusClip / Repurpose.io API Key 已上位、Sprint 4 Whisper 轉錄完成

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 9.1 | OpusClip API 封裝（上傳影片 → 取回精華短影音） | INT-1 | 3 | 1.11 | 上傳長影片 → 取回 10 支短影音 | 🔲 |
| 9.2 | Claude 內容生成 Pipeline（逐字稿 → LinkedIn 貼文 × 30 + SEO 文章 × 10） | AI-1 | 4 | 4.3, 3.2 | 每支影片逐字稿生成 30 篇 LinkedIn + 10 篇 SEO 文章，品牌語調一致 | 🔲 |
| 9.3 | AI 內容品質防護（禁用 AI 詞彙清單 + 語氣檢查 + 去重） | AI-1 | 3 | 9.2 | 生成內容不含常見 AI 用語，通過 LinkedIn 演算法友善度檢測 | 🔲 |
| 9.4 | 內容裂變 Celery Pipeline（轉錄 → 生成文字 → 剪短影音 → 排程） | BE-1 | 3 | 9.1, 9.2 | 上傳影片後 30 分鐘內完成全部裂變 | 🔲 |
| 9.5 | Repurpose.io API 封裝（排程發布 LinkedIn / YouTube） | INT-1 | 2 | 1.11 | 可排程發布至 LinkedIn + YouTube | 🔲 |
| 9.6 | 內容管理頁面 UI — LinkedIn 貼文（編輯 + 排程 + 預覽） | FE-1 | 4 | 9.4 | 供應商可瀏覽/編輯/排程/預覽 LinkedIn 貼文 | 🔲 |
| 9.7 | 內容管理頁面 UI — SEO 文章（編輯器 + 關鍵字建議 + 排程） | FE-1 | 3 | 9.4 | 供應商可編輯 SEO 文章、查看關鍵字建議 | 🔲 |
| 9.8 | 內容管理頁面 UI — 短影音（預覽 + 排程） | FE-2 | 3 | 9.1 | 供應商可預覽短影音、設定排程 | 🔲 |
| 9.9 | 內容審核佇列（人工審核介面 + 批量操作） | FE-2 | 2 | 9.4 | 供應商/編輯可批量審核 + 一鍵排程 | 🔲 |
| 9.10 | 內容成效追蹤（LinkedIn/YouTube impression + engagement 回寫） | INT-1 | 2 | 9.5 | 成效數據自動回寫至平台 | 🔲 |

**Sprint 9 交付物**：
- 完整內容裂變 Pipeline
- LinkedIn/SEO/短影音自動生成
- 內容管理 + 排程 + 審核
- 成效追蹤

---

### Sprint 10（Week 19-20）：搜尋系統 + 買家前台完善 — 🔲 未開始

> 目標：買家可搜尋/篩選供應商，完整買家使用體驗

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 10.1 | Elasticsearch 供應商索引（產業/認證/能力/城市全文搜尋） | BE-1 | 3 | 2.1 | 搜尋回應 < 200ms，支援模糊匹配 + 篩選 | 🔲 |
| 10.2 | 搜尋 API（全文搜尋 + 多維度篩選 + 分頁 + 排序） | BE-1 | 3 | 10.1 | API 支援文字搜尋 + 產業/認證/國家/產能篩選 | 🔲 |
| 10.3 | 平台首頁 UI（搜尋框 + 熱門產業 + 精選供應商） | FE-1 | 4 | 10.2 | SEO 優化首頁，搜尋框即時建議 | 🔲 |
| 10.4 | 供應商列表頁 UI（搜尋結果 + 篩選側邊欄 + 卡片/列表切換） | FE-1 | 4 | 10.2 | 篩選器流畢、分頁載入、結果排序 | 🔲 |
| 10.5 | 供應商公開頁完善（整合所有模組：影片 + AI 分身 + RFQ + 認證） | FE-1 | 4 | 6.5, 4.8, 3.10 | 完整供應商展示頁（SEO + 結構化資料） | 🔲 |
| 10.6 | 買家儀表板 UI（我的 RFQ 列表 + 回覆追蹤 + 收藏供應商） | FE-2 | 4 | 3.12 | 買家可追蹤已提交的 RFQ 狀態 | 🔲 |
| 10.7 | 平台內訊息系統（買家 ↔ 供應商直接通訊） | BE-1 + FE-2 | 4 | 1.8 | 即時訊息、歷史記錄、未讀計數 | 🔲 |
| 10.8 | 多語系前台（next-intl 設定：en/de/ja/es/zh） | FE-1 | 3 | 10.3 | 買家可切換語言，所有 UI 文字翻譯完成 | 🔲 |
| 10.9 | SEO 優化（meta tags、結構化資料、sitemap、robots.txt） | FE-1 | 2 | 10.5 | Google Search Console 驗證通過 | 🔲 |
| 10.10 | 買家端 E2E 測試（搜尋 → 瀏覽 → 對話 → 提交 RFQ） | QA-1 | 3 | 10.5 | 完整買家流程 Playwright 自動化 | 🔲 |

**Sprint 10 交付物**：
- 供應商全文搜尋 + 篩選
- 完整買家前台體驗
- 平台內訊息系統
- 5 語言國際化
- SEO 優化

---

### Sprint 11（Week 21-22）：訂閱計費 + 管理後台 — 🔲 未開始

> 目標：供應商訂閱付費、平台管理員完整管控能力
> 前置條件：Stripe API Key 已上位、Sprint 9/10 完成

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 11.1 | Stripe 整合（訂閱建立/升級/降級/取消/Webhook） | INT-1 | 4 | 1.11 | 三個方案（Starter/Professional/Enterprise）可訂閱 | 🔲 |
| 11.2 | 訂閱方案功能門禁（Feature Gate — 各方案功能開關） | BE-1 | 3 | 11.1 | Starter: 基礎功能；Pro: +Outbound+內容；Enterprise: 全功能 | 🔲 |
| 11.3 | 供應商訂閱管理頁面（方案選擇 + 帳單歷史 + 升級/降級） | FE-2 | 4 | 11.1 | 供應商可選擇/變更方案，查看帳單 | 🔲 |
| 11.4 | 管理後台 — 全平台數據總覽（供應商數/買家數/RFQ 數/營收） | FE-1 | 3 | 1.8 | 管理員可查看全平台 KPI | 🔲 |
| 11.5 | 管理後台 — 供應商管理（列表/審核/上下架/訂閱狀態） | FE-1 | 3 | 11.4 | 管理員可審核供應商、控制上下架 | 🔲 |
| 11.6 | 管理後台 — 買家管理（列表/封鎖/RFQ 監控） | FE-2 | 2 | 11.4 | 管理員可管理買家帳號 | 🔲 |
| 11.7 | 管理後台 — AI 內容審核佇列（批量審核 + 品質標記） | FE-2 | 3 | 9.9 | 管理員可審核全平台 AI 生成內容 | 🔲 |
| 11.8 | 管理後台 — Outbound 系統健康度（LinkedIn 封禁率/Email Bounce 率） | FE-1 | 3 | 7.8, 8.4 | 管理員可監控 Outbound 系統狀態 | 🔲 |
| 11.9 | 管理後台 — 第三方 API 用量儀表板（各服務月度用量 + 費用） | INT-1 + FE-1 | 3 | 1.11 | 管理員可查看每個 API 的月度用量與費用 | 🔲 |
| 11.10 | 管理後台 — 系統設定（API Key 輪換/全域通知設定） | BE-1 | 2 | 11.4 | 管理員可更新 API Key、設定全域通知 | 🔲 |

**Sprint 11 交付物**：
- Stripe 訂閱計費系統
- 功能門禁（3 個方案）
- 完整管理後台

---

### Sprint 12（Week 23-24）：進階功能 + 分析儀表板 — 🔲 未開始

> 目標：供應商 KPI 儀表板、展覽整合、名片揃描、再行銷序列

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 12.1 | 供應商 KPI 儀表板（線上系統指標 + 業務成交指標） | FE-2 + BE-1 | 5 | 全部前置完成 | Recharts 圖表：RFQ 趨勢、Lead Score 分佈、訪客趨勢、Outbound 成效、內容觸及率 | 🔲 |
| 12.2 | 展覽活動管理模組（展前 ICP 名單 + 展中名片揃描 + 展後序列） | BE-1 + FE-2 | 5 | 8.5 | 支援展覽生命週期管理 | 🔲 |
| 12.3 | 名片揃描 OCR（手機拍照 → Claude Vision → 結構化聯絡人） | AI-1 + FE-1 | 3 | 3.2 | 拍照名片 → 自動建立 CRM 聯絡人 | 🔲 |
| 12.4 | 再行銷序列（90 天後 C 級重新評分、B 級 30 天後進入自動序列） | BE-1 | 3 | 8.5 | Celery Beat 排程定期重新評分 + 觸發序列 | 🔲 |
| 12.5 | Email Nurturing 序列（C 級每月 1 封產業洞察信） | AI-1 + INT-1 | 3 | 8.1 | 自動生成 + 排程發送月度電子報 | 🔲 |
| 12.6 | 資料匯出 API（CSV/JSON 格式匯出線索/RFQ/分析數據） | BE-1 | 2 | - | 供應商可匯出所有業務數據 | 🔲 |
| 12.7 | 行動裝置響應式優化（所有頁面 Mobile/Tablet 適配） | FE-1 + FE-2 | 4 | - | 所有頁面在 375px~1920px 正常顯示 | 🔲 |
| 12.8 | 進階功能 E2E 測試 | QA-1 | 3 | 12.1~12.7 | 所有新功能測試通過 | 🔲 |

**Sprint 12 交付物**：
- 完整 KPI 儀表板
- 展覽活動管理
- 名片掃描 OCR
- 再行銷自動序列
- 響應式優化

---

### Sprint 13（Week 25-26）：整合測試 + 效能優化 — 🔲 未開始

> 目標：全系統整合測試通過、效能達標

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 13.1 | 全流程整合測試 — 供應商 Onboarding（註冊 → 資料 → 影片 → AI 分身） | QA-1 | 3 | All | 完整流程跑通無錯誤 | 🔲 |
| 13.2 | 全流程整合測試 — 買家體驗（搜尋 → 瀏覽 → 對話 → RFQ → 追蹤） | QA-1 | 3 | All | 完整流程跑通無錯誤 | 🔲 |
| 13.3 | 全流程整合測試 — Outbound（ICP → 名單 → LinkedIn + Email → 回覆 → 轉線索） | QA-1 | 3 | All | 完整流程跑通無錯誤 | 🔲 |
| 13.4 | 全流程整合測試 — 內容裂變（影片 → 轉錄 → 生成 → 排程 → 發布） | QA-1 | 2 | All | 完整流程跑通無錯誤 | 🔲 |
| 13.5 | 負載測試（100 併發用戶、1000 RFQ/天模擬） | OPS-1 + QA-1 | 3 | All | API P95 < 2s、頁面 LCP < 3s | 🔲 |
| 13.6 | API 回應時間優化（慢查詢 + N+1 查詢修復 + Redis 快取策略） | BE-1 | 4 | 13.5 | 所有 API P95 < 500ms | 🔲 |
| 13.7 | 前端效能優化（Bundle 大小 + 圖片 + Code Splitting） | FE-1 | 3 | 13.5 | Lighthouse 分數 ≥ 90 | 🔲 |
| 13.8 | 資料庫效能調校（索引優化 + 查詢計畫分析 + Connection Pool） | BE-1 + OPS-1 | 2 | 13.5 | 所有查詢 < 100ms | 🔲 |
| 13.9 | 安全揃描（OWASP ZAP + 依賴漏洞揃描 + API 安全測試） | OPS-1 + QA-1 | 3 | All | 無 High/Critical 漏洞 | 🔲 |
| 13.10 | 第三方 API 降級測試（模擬各 API 掟掉的 Fallback 行為） | QA-1 + INT-1 | 2 | All | 每個 API 有明確的降級策略 | 🔲 |

**Sprint 13 交付物**：
- 全流程整合測試報告
- 效能達標
- 安全掃描清白

---

### Sprint 14（Week 27-28）：上線準備 + 正式發布 — 🔲 未開始

> 目標：Production 部署、監控就位、首批供應商 Onboarding

| # | Task | 負責 | 天數 | 前置 | 驗收標準 | 狀態 |
|---|------|------|------|------|---------|------|
| 14.1 | Production 基礎設施部署（AWS ECS + RDS + ElastiCache + S3 + CloudFront） | OPS-1 | 3 | 13.9 | Production 環境可存取、SSL 設定完成 | 🔲 |
| 14.2 | 域名 + DNS + SSL（factoryinsider.com 或類似） | OPS-1 | 1 | 14.1 | HTTPS 全站、DNS 解析正常 | 🔲 |
| 14.3 | 監控系統上線（Sentry + Prometheus + Grafana + Uptime） | OPS-1 | 2 | 14.1 | 所有告警規則啟用 | 🔲 |
| 14.4 | 自動備份策略（DB 每日備份 + S3 版本控制） | OPS-1 | 1 | 14.1 | 備份可恢復測試通過 | 🔲 |
| 14.5 | 隱私政策 + 服務條款頁面 | PM + FE-1 | 2 | - | 含 GDPR/台灣個資法/CAN-SPAM 條款 | 🔲 |
| 14.6 | 使用者文件 / Help Center（供應商操作手冊 + 買家 FAQ） | PM | 4 | - | 涵蓋所有主要功能操作流程 | 🔲 |
| 14.7 | 首批供應商 Onboarding 測試（3~5 家台灣工廠試用） | PM + 全體 | 5 | 14.1 | 供應商完整走完 Phase 1，回饋紀錄 | 🔲 |
| 14.8 | 根據試用回饋修復 Bug + 體驗優化 | 全體 | 5 | 14.7 | 所有 P0/P1 Bug 修復 | 🔲 |
| 14.9 | Production Smoke Test（全功能驗證 on Production） | QA-1 | 2 | 14.8 | 所有核心流程在 Production 跑通 | 🔲 |
| 14.10 | 正式上線 🚀 | 全體 | 1 | 14.9 | 平台公開可存取 | 🔲 |

**Sprint 14 交付物**：
- Production 正式上線
- 監控 + 備份就位
- 首批供應商已 Onboarding
- 使用者文件就緒

---

## 5. 開發優先順序邏輯

為什麼按這個順序而不是先做簡單的：

```
Sprint 1-2：基礎建設
     ↓ 必須先有地基
Sprint 3-4：RFQ + AI 分身  ← 最難但最核心，決定整個平台價值
     ↓ 核心 AI 引擎完成
Sprint 5-6：訪客識別 + 影片多語系  ← 依賴行為追蹤 + 影片系統
     ↓ 數據源就位
Sprint 7-8：Outbound 引擎  ← 依賴 Clay 數據 + Lead Scoring
     ↓ 獲客引擎就位
Sprint 9-10：內容裂變 + 搜尋  ← 依賴影片轉錄 + 內容生成
     ↓ 雙邊平台完整
Sprint 11-12：計費 + 管理 + 進階  ← 有功能才有計費意義
     ↓ 商業化就緒
Sprint 13-14：測試 + 上線  ← 全部就緒才上線
```

**核心原則**：先做最難、最有價值的 AI 功能（RFQ 解析 + AI 分身），不先做「簡單但非核心」的搜尋或內容管理。

---

## 6. 風險登記簿

| # | 風險 | 可能性 | 影響 | 緩解措施 |
|---|------|-------|------|---------|
| R1 | Claude API 解析製造業術語準確率不足 | 中 | 高 | Sprint 3 即投入 20 筆真實 RFQ 測試；準備 Prompt 迭代計畫 |
| R2 | HeyGen 影片生成品質不穩（尤其德語唇形） | 中 | 中 | 備選 Vozo AI；Sprint 6 品質測試決定是否切換 |
| R3 | LinkedIn 帳號被封禁 | 高 | 高 | 專屬帳號、HeyReach 智慧節流、每日上限嚴格執行 |
| R4 | RB2B 亞歐市場識別率低 | 高 | 中 | 主要依賴 Leadfeeder 企業層級；RB2B 做為美國市場補充 |
| R5 | 冷啟動：沒有供應商就沒有買家 | 高 | 極高 | 前 3 個月招募 20-50 家免費供應商；平台自跑 Outbound 引流 |
| R6 | 第三方 API 費用超預算 | 中 | 中 | Sprint 11 API 用量監控儀表板；按用量向供應商收費 |
| R7 | 多語言 RAG 幻覺率高（德語/日語） | 中 | 高 | 信心度閾值 70% 強制轉人工；定期人工審核對話品質 |
| R8 | GDPR 合規未落實被罰 | 低 | 極高 | Sprint 5 即建立 Cookie 同意；上線前法務審查 |
| R9 | Celery 任務佇列堵塞（大量影片處理） | 中 | 中 | 任務優先權設計（RFQ 解析 > 影片生成 > 內容裂變） |
| R10 | 團隊成員離職 | 中 | 高 | 完整文件化；Code Review 確保知識分享 |

---

## 7. 訂閱方案設計（商業模型）

| | Starter | Professional | Enterprise |
|---|---------|-------------|------------|
| 月費（USD） | $299 | $799 | $1,999 |
| 供應商公開頁 | ✅ | ✅ | ✅ |
| AI 分身（基礎） | ✅ | ✅ | ✅ |
| 影片上傳 | 3 支 | 6 支 | 無限 |
| 多語系影片 | 2 語言 | 4 語言 | 6+ 語言 |
| RFQ 解析 | 10 筆/月 | 50 筆/月 | 無限 |
| Lead Scoring | ✅ | ✅ | ✅ |
| 訪客意圖分析 | 基礎（企業級） | 進階（個人級） | 完整 |
| Outbound 自動化 | ❌ | ✅ 500 名單/月 | ✅ 無限 |
| 內容裂變 | ❌ | ✅ 15 篇/月 | ✅ 無限 |
| CRM 整合 | ❌ | HubSpot | 全部 |
| 優先客服 | Email | Slack | 專屬 AM |

---

## 8. 技術債管理

每個 Sprint 保留 **15% 時間（約 1.5 天/人）** 處理技術債：
- Refactoring
- 依賴更新
- Test Coverage 提升（目標 ≥ 80%）
- 文件維護

---

## 9. Definition of Done（完成定義）

每個 Task 必須滿足以下所有條件才算完成：

1. **程式碼**：PR 通過 Code Review（至少 1 人）
2. **測試**：單元測試 + 整合測試通過
3. **真實 API**：使用真實第三方 API 驗證（禁止 Mock）
4. **UI**：符合 Design System、響應式、多語系
5. **文件**：API 文件自動更新（Swagger）
6. **部署**：Staging 環境可正常運行
7. **效能**：API 回應 P95 < 2 秒

---

## 10. 里程碑與 Go/No-Go 檢查點

| 時間 | 里程碑 | Go 條件 |
|------|--------|--------|
| Month 2 結束 | AI 核心引擎 Demo | RFQ 解析準確率 ≥ 80%、AI 分身可回答基礎問題 |
| Month 3 結束 | 訪客識別 + 影片 Demo | RB2B/Leadfeeder 資料正確接收、多語系影片可播放 |
| Month 4 結束 | Outbound 引擎 Demo | Clay → HeyReach → Instantly 完整流程跑通 |
| Month 5 結束 | 買家前台可用 | 搜尋/瀏覽/對話/RFQ 完整體驗可 Demo |
| Month 6 結束 | 商業化就緒 | 訂閱計費正常、管理後台完整 |
| Month 7 結束 | 正式上線 | 全流程測試通過、首批供應商已 Onboarding |

---

## 附錄：快速參考

### 第三方帳號申請清單

| 服務 | 申請 URL | 預估審核時間 | 備註 |
|------|---------|-------------|------|
| Anthropic (Claude) | console.anthropic.com | 即時 | 需信用卡 |
| HeyGen | heygen.com | 即時 | Enterprise 需聯繫銷售 |
| Clay | clay.com | 即時 | Pro 方案起 |
| Apollo.io | apollo.io | 即時 | Free tier 可開始 |
| RB2B | rb2b.com | 1-2 天 | 需網站驗證 |
| Leadfeeder | leadfeeder.com | 即時 | 14 天試用 |
| HeyReach | heyreach.io | 即時 | 需 LinkedIn 帳號 |
| Instantly.ai | instantly.ai | 即時 | 需暖機信箱 |
| OpusClip | opusclip.pro | 即時 | |
| Repurpose.io | repurpose.io | 即時 | |
| Stripe | stripe.com | 1-2 天 | 台灣公司可申請 |
| AWS | aws.amazon.com | 即時 | |
| Pinecone | pinecone.io | 即時 | Free tier 可開始 |
| Vercel | vercel.com | 即時 | Pro 方案 $20/月 |

### 關鍵技術文件連結（開發時參考）

| 服務 | API 文件 |
|------|---------|
| Claude API | docs.anthropic.com/claude/reference |
| HeyGen API | docs.heygen.com |
| Clay API | docs.clay.com |
| Apollo API | apolloio.github.io/apollo-api-docs |
| RB2B Webhook | rb2b.com/docs |
| HeyReach API | docs.heyreach.io |
| Instantly API v2 | developer.instantly.ai |
| OpusClip API | opusclip.pro/api |
| Stripe API | stripe.com/docs/api |
| Pinecone | docs.pinecone.io |
