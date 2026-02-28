# CLAUDE.md — Project Instructions

These instructions override default behavior. Follow them exactly.

---

## 1. 務必按照計畫進行 (Always Follow the Plan)

**你不是項目經理，不能改變計畫順序。development_plan.md 是唯一的真實。**

### 1.1 嚴格執行 Sprint 計畫
- 必須按 `development_plan.md` 的 Sprint 順序執行，不能跳過或重排
- 不能因為「某個任務更重要」或「想先做簡單的」就改變順序
- Sprint 1 之後才能開始 Sprint 2，以此類推
- 禁止跳過任何 Task，即使看起來可以「優化」

### 1.2 完整交付定義
每個 Task 標記為「完成」**必須同時滿足**：
```
✅ 代碼已寫入（新文件或修改現有）
✅ 所有相關單元測試已通過
✅ 與前置 Task 的整合已驗證
✅ 驗收標準明確達成
✅ 文檔已更新（若適用）
```

**不完整的交付範例（禁止）：**
- ❌ 「只寫了 API，還沒寫前端」
- ❌ 「代碼寫完了，測試待補」
- ❌ 「用 Mock 資料先跑通，真實 API 之後再接」
- ❌ 「先做簡單功能，困難的 Sprint 再說」

### 1.3 使用 TodoWrite 追踪（強制）
- **每次開始 Task 前**：調用 TodoWrite，標記為 `in_progress`
- **每完成一個 Task**：立即調用 TodoWrite 標記 `completed`
- **禁止批量標記**：不能在 Sprint 末一次性標記所有完成
- **禁止隱藏進度**：不能有「暗中進行」的 Task，所有工作都要追踪

### 1.4 遇到困難時的處理
- **禁止迴避困難**：如果某個 Task 很難，必須執行它，不能「先做容易的」
- **禁止自作聰明的解決方案**：不能用 Mock、簡化版、繞過來逃避困難
- **停止並報告**：如果真的卡住（例如 API 無法申請、技術無法實現），立即停止該 Task，明確報告：
  ```
  🛑 BLOCKED: [Task 名稱]
  原因：[具體困難]
  需要：[使用者需要採取的行動]
  ```
- **等待使用者指示**：不能自行改變計畫或用替代方案繼續

### 1.5 不能偏離計畫的例子
❌ 「Sprint 3 太難，我先做 Sprint 9 的搜尋功能」
❌ 「RFQ 解析需要真實 Claude API，我先用本地 LLaMA 模擬」
❌ 「HeyGen API 還沒申請，我先用 FFmpeg 做硬編碼版本」
❌ 「我發現更好的架構，要改變 frontend/backend 的目錄結構」
❌ 「B 級線索回覆功能複雜，我跳過先做 A 級」

### 1.6 修改計畫的唯一方式
- **只有使用者可以修改計畫**
- 我只能提出「這個計畫似乎不可行」，不能自行調整
- 使用者同意後，才能按新計畫進行
- 修改必須記錄在案（更新 development_plan.md）

## 2. 不使用模擬，全部用真實；缺乏時提出警示 (No Mocks — Real Implementations Only; Warn When Missing)

**生產代碼中，完全禁止 Mock、Stub、假數據。**

### 2.1 禁止的模式（絕對禁止）
❌ Claude API 用不了，就用本地 LLaMA 模擬
❌ HeyGen API 未申請，用 FFmpeg + 硬編碼的多語言
❌ Pinecone 向量資料庫用 SQLite 本地向量表代替
❌ PostgreSQL 改用 SQLite 因為「更簡單」
❌ Redis 改用 in-memory dict 因為「開發環境用不著」
❌ RFQ 文本解析用 regex 因為「Claude API 等不了」

**這些都是自欺欺人。實際上線時一定會出問題。**

### 2.2 真實實現的定義
- **API 調用**：直接使用 API，不能用 JSON 文件模擬響應
- **資料庫**：PostgreSQL + Redis + Pinecone，不能替代
- **AI 模型**：Claude API，不能用免費模型替代
- **文件上傳**：AWS S3，不能用本地文件系統替代
- **多語系**：HeyGen，不能用簡單的文本替代

### 2.3 缺少依賴時的處理
**必須停止開發並報告，不能繼續：**
```
⚠️ BLOCKED: [Task 名稱]
================
無法取得的依賴：[具體什麼無法使用]
原因：[為什麼不能替代]

需要的行動：
- 申請 API Key：[具體的服務名稱]
- 聯繫：[聯繫方式]
- 預計時間：[等待期間]

當前無法繼續，等待使用者提供依賴。
================
```

**絕不能**：
- 自作聰明地用替代方案繼續開發
- 先用 Mock，說「之後再接真實 API」
- 跳過這個 Task，去做其他 Task
- 用「先驗證邏輯」為名義用假數據

### 2.4 測試中的模擬例外
- **單元測試**：可以用 Mock / Fixtures（用 pytest fixtures）
- **整合測試**：必須使用真實資料庫、真實 API（或測試環境 API Key）
- **E2E 測試**：完全真實，包括第三方 API

### 2.5 定期檢查清單（每個 Sprint 初）
- [ ] 所有 API Key 已獲取並在 `.env.local` 中
- [ ] PostgreSQL / Redis / Elasticsearch 服務運行中
- [ ] 第三方 API 配額充足（HeyGen / Claude / etc）
- [ ] 沒有 Mock 代碼在生產路徑中
- [ ] 所有依賴都明確存在，不是假設

## 3. 不要取巧選擇容易與小範圍任務 (No Shortcuts — Address the Full Scope)

**你是代理，不是自由開發者。不能挑選喜歡的工作。**

### 3.1 禁止的行為
❌ 「RFQ 解析太難，我先做訪客識別」
❌ 「AI 分身 RAG 要調 Prompt，我先實現搜尋功能」
❌ 「Outbound LinkedIn 自動化遵守限制，我先做 Email」
❌ 「內容裂變涉及多個 API，我只實現 LinkedIn 發布」
❌ 「Lead Scoring 需要複雜評分邏輯，先做簡單的通知機制」

### 3.2 「完整」的定義（絕對執行）
每個 Task 的驗收標準必須 **100% 達成**，不能只做 80%：

**例如 Task 3.3：RFQ 文字解析**
```
✅ 完整 =
  - Prompt Engineering 完成（準確率 ≥ 80%）
  - 測試用 10 筆真實 RFQ
  - 結構化輸出 JSON（材料/尺寸/公差/交期）
  - 錯誤處理已實裝
  - 單元測試通過

❌ 不算完整 =
  - 「只解析材料和尺寸，公差之後再做」
  - 「用簡單 regex 先跑通，之後換 Claude」
  - 「準確率目前 60%，可以接受」
  - 「只測試了 2 筆 RFQ」
```

### 3.3 分解計畫 vs 跳過任務
- **允許**：計畫中已經分解的 Sub-Task（例如 Task 3.3, 3.4, 3.5 各自獨立）
- **不允許**：自行決定「這個 Task 太大，分成下週再做」

計畫中的順序是依賴關係決定的。不能因為「想先簡單的」就改變順序。

### 3.4 「部分完成」不算完成
如果 Task 說「RFQ 自動解析 Pipeline」，必須包括：
```
✓ RFQ 提交 API
✓ 文本解析（Claude）
✓ PDF 解析（Textract）
✓ 企業背景查詢（Apollo）
✓ Lead Score 計算
✓ 草稿回覆生成
✓ Slack 通知
✓ 整個 Pipeline 串接
```

不能只實現其中 3-4 項說「完成了」。

### 3.5 困難 Task 的處理方式
如果某個 Task 很困難：

1. **不能跳過它** — 必須執行
2. **不能簡化版** — 必須按驗收標準
3. **可以請求幫助** — 停止並報告：
   ```
   🤔 HELP NEEDED: [Task 名稱]
   困難點：[具體為什麼困難]
   嘗試過：[已嘗試的方案]
   需要：[使用者能否提供指導或資源]
   ```
4. **不能自作聰明** — 用 workaround 繼續

### 3.6 定期檢查清單（每完成 3 個 Task）
- [ ] 是否按 development_plan.md 的順序進行？
- [ ] 是否所有驗收標準都達成？
- [ ] 是否有被我「簡化」的地方？
- [ ] 是否有 TODO 註解留在代碼中表示「之後再做」？
- [ ] 是否每個 Task 都有對應的測試？

---

## 4. 代理開發特別約束 (Special Constraints for Autonomous Development)

**這些約束只適用於我全權代理執行開發時。**

### 4.1 每個 Sprint 的必須交付物
```
Sprint 開始日期：[Date]
預計完成日期：[Date]

交付清單：
□ 所有 Task 都在 TodoWrite 中追踪
□ 所有代碼已提交到 Git
□ 所有測試都通過
□ 所有驗收標準都達成或明確阻礙
□ 若有任何部分無法完成，已清楚報告原因

不接受的情況：
✗ 「大部分完成了」
✗ 「代碼寫了但沒測試」
✗ 「用了 Mock 數據」
✗ 「跳過了某個 Sub-Task」
✗ 「阻礙報告不清楚」
```

### 4.2 進度報告格式（每 3 日一次）
```
📊 Sprint X 進度報告（Week Y）

已完成（in_progress → completed）：
  ✅ Task X.1: [功能] — [驗收標準達成情況]
  ✅ Task X.2: [功能] — [驗收標準達成情況]

進行中（in_progress）：
  🔄 Task X.3: [功能] — [完成百分比]
     - [具體進度]
     - [預計完成日期]

阻礙（blocked）：
  🛑 Task X.4: [功能]
     - 原因：[具體阻礙]
     - 需要：[使用者需要提供什麼]

下週計畫：
  - [Task...]
  - [Task...]
```

### 4.3 代碼提交規範
- **每完成一個 Task** → 一個 Git commit
- **Commit message 格式**：
  ```
  feat(rfq): implement Claude-based RFQ parsing (Task 3.3)

  ✅ RFQ 文字解析準確率 ≥ 80%（驗證用 10 筆真實 RFQ）
  ✅ 結構化輸出 JSON（材料/尺寸/公差/交期）
  ✅ 單元測試通過

  Validation:
  - Tested with 10 real RFQs
  - Accuracy: 85% (exceeds 80% requirement)
  - All unit tests passing
  ```
- **禁止**：多個 Task 合併成一個 commit
- **禁止**：部分完成的 commit

### 4.4 遇到用戶無回應時
如果有 Task 被 BLOCKED，且 3 天內使用者未回應：
1. 檢查是否有其他 Task 可以平行進行
2. 如果整個 Sprint 都被阻礙，暫停報告：
   ```
   ⏸️  SPRINT X PAUSED
   原因：Task X.Y 無法進行，阻礙後續 Task
   需要使用者的行動：[具體]
   暫停日期：[Date]
   ```
3. 等待使用者反應，不能自行改變計畫

### 4.5 品質檢查（每個 Sprint 末）
```
Sprint X 完成檢查清單：

代碼品質：
  ✅ 所有代碼都有型別提示（TypeScript / Type Hints）
  ✅ 所有函數都有文檔字符串或 JSDoc
  ✅ 沒有 TODO / FIXME / HACK 註解（已完成的應該沒有）
  ✅ 沒有 console.log 或 print 調試語句
  ✅ 遵循 linting 規則

測試覆蓋：
  ✅ 所有新代碼都有單元測試
  ✅ 關鍵路徑都有整合測試
  ✅ 所有測試通過 (0 failures)
  ✅ 沒有 skip() 或 .only() 測試

真實性：
  ✅ 沒有 Mock 在生產代碼路徑
  ✅ 所有 API 調用都是真實的
  ✅ 所有資料庫操作都是真實的
  ✅ 所有驗收標準都用真實數據驗證

Git 記錄：
  ✅ 每個 Task 一個 commit
  ✅ Commit message 清楚
  ✅ 所有代碼已推送到遠程
```

### 4.6 不能改變的決定
以下這些我無權改變，即使遇到問題：
- ✗ 不能改變 development_plan.md 的 Sprint 順序
- ✗ 不能刪除某個 Task 說「不需要」
- ✗ 不能用簡化版本代替完整功能
- ✗ 不能「先做部分」說「之後再完成」
- ✗ 不能用 Mock 代替真實依賴
- ✗ 不能改變架構（frontend/backend/infra 目錄結構）

**唯一的方式是**：停止開發，清楚報告問題，等待使用者指示。

---

## General Coding Standards

- Read files before modifying them. Never propose changes to unread code.
- Prefer editing existing files over creating new ones.
- Do not add comments, docstrings, or type annotations to code you did not change.
- Do not introduce error handling for scenarios that cannot occur.
- Delete unused code entirely — do not leave backwards-compatibility stubs.
- No emojis in output unless explicitly requested.
