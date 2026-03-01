# Factory Insider Backend

FastAPI 後端應用

## 開發環境設定

見根目錄 README.md

## 運行

```bash
python -m uvicorn app.main:app --reload
```

API 文件：http://localhost:8000/docs

## Sprint 5 實網驗證

執行訪客意圖實網驗證腳本：

```bash
python scripts/sprint5_live_validation.py --supplier-id <SUPPLIER_ID>
```

完整流程見：`development_plan.md` 的「Sprint 1-5 外部資源依賴與驗收矩陣（單一入口）」章節
