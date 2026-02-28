# API 端點列表

詳細的 API 端點文檔。

## 基本資訊

- Base URL: `http://localhost:8000` (開發)
- 版本: `v1`
- 認證: JWT Bearer Token

## 認證端點

### 註冊
```
POST /api/v1/auth/register
```

### 登入
```
POST /api/v1/auth/login
```

### Token 刷新
```
POST /api/v1/auth/refresh
```

### 獲取當前用戶
```
GET /api/v1/auth/me
```

## 供應商端點

### 列表
```
GET /api/v1/suppliers?skip=0&limit=10&search=...&industry=...
```

### 建立
```
POST /api/v1/suppliers
```

### 詳情
```
GET /api/v1/suppliers/{id}
```

### 更新
```
PUT /api/v1/suppliers/{id}
```

### 公開頁
```
GET /api/v1/suppliers/{slug}
```

## 更多端點...

見根目錄 README.md 的 API 端點概覽
