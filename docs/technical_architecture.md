# 技術架構

Factory Insider 平台的完整技術架構設計。

## 系統架構

### Frontend
- Next.js 14 (App Router)
- TypeScript + Tailwind CSS
- Zustand (狀態管理)
- Socket.io (實時通訊)
- next-intl (多語系)

### Backend
- FastAPI (非同步 API 框架)
- SQLAlchemy 2.0 (ORM)
- Celery + Redis (非同步任務隊列)
- Alembic (資料庫遷移)

### 資料庫
- PostgreSQL 16 (主資料庫)
- Redis 7 (快取 + 任務隊列)
- Pinecone (向量資料庫)
- Elasticsearch 8 (全文搜尋)

### 外部服務
- Anthropic Claude API (AI/LLM)
- HeyGen (多語系影片生成)
- Clay (名單富化)
- Apollo (企業背景查詢)
- 等等...

## 部署架構

### Development
- Docker Compose (本地開發)
- 包含所有必要服務（PostgreSQL、Redis、Elasticsearch）

### Staging/Production
- AWS ECS (容器編排)
- AWS RDS (管理型 PostgreSQL)
- AWS ElastiCache (管理型 Redis)
- AWS S3 (檔案存儲)
- CloudFront (CDN)

## 安全性

見 `../docs/`

## 性能優化

見相關文檔
