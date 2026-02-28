# Database Migration Guide

使用 Alembic 管理資料庫 Schema

## 前置要求

- PostgreSQL 16+ 運行中
- 環境變數設定正確 (DATABASE_URL)

## 初始化遷移

### 首次設定

```bash
# 進入 backend 目錄
cd backend

# 激活虛擬環境
source venv/bin/activate  # Mac/Linux
# 或
venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 建立初始遷移

```bash
# 自動生成遷移腳本（基於模型定義）
alembic revision --autogenerate -m "Initial schema creation"

# 應用遷移
alembic upgrade head
```

## 常用命令

### 檢視遷移歷史

```bash
# 查看當前版本
alembic current

# 查看遷移歷史
alembic history
```

### 應用遷移

```bash
# 升級到最新版本
alembic upgrade head

# 升級到特定版本
alembic upgrade <revision>

# 升級 N 個版本
alembic upgrade +2
```

### 回滾遷移

```bash
# 回滾到上一個版本
alembic downgrade -1

# 回滾到特定版本
alembic downgrade <revision>

# 回滾到初始狀態
alembic downgrade base
```

### 建立新遷移

```bash
# 建立空遷移腳本（手動編輯）
alembic revision -m "Add new_column to users table"

# 自動生成遷移（基於模型變更）
alembic revision --autogenerate -m "Add new_column to users table"
```

## 遷移檔案位置

- `alembic/versions/` - 所有遷移腳本

## 遷移腳本結構

```python
"""Description of migration

Revision ID: abc123
Revises: xyz789
Create Date: 2026-02-28 12:00:00

"""

def upgrade() -> None:
    # 升級操作 (新增表、欄位等)
    pass

def downgrade() -> None:
    # 回滾操作 (刪除表、欄位等)
    pass
```

## Docker Compose 環境

如果使用 Docker Compose，遷移會在容器啟動時自動運行。

```bash
# 啟動所有服務
docker compose up

# 手動執行遷移
docker compose exec backend alembic upgrade head

# 查看遷移狀態
docker compose exec backend alembic current
```

## 常見問題

### Q: 如何安全地修改已發布的遷移？

A: 不要修改已發布的遷移。建立新的遷移來撤銷和重新應用變更。

```bash
alembic revision --autogenerate -m "Fix previous migration"
```

### Q: 資料庫和模型定義不同步

A: 使用 autogenerate 重新同步：

```bash
alembic revision --autogenerate -m "Sync with current models"
```

### Q: 需要刪除所有表並重新建立

A: 謹慎操作！在生產環境前測試。

```bash
# 回滾到初始狀態
alembic downgrade base

# 重新升級
alembic upgrade head
```

## 最佳實踐

1. **每個邏輯變更一個遷移** - 不要在一個遷移中混合多個變更
2. **編寫清晰的遷移訊息** - 描述你在做什麼
3. **測試遷移** - 在 dev/staging 環境先測試
4. **勿修改已發布遷移** - 建立新遷移來修正錯誤
5. **保留 downgrade 邏輯** - 萬一需要回滾

---

更多資訊: https://alembic.sqlalchemy.org/
