# Factory Insider Design System v1.0

完整的設計系統規範，用於 Figma 和前端開發。

## 1. 色彩規範

### 主色系

#### 品牌色 - 藍色（信任、專業）
- **Primary-900**: `#0D3B66` (深藍，用於主要 UI)
- **Primary-700**: `#1B5E7F` (標準藍，按鈕、連結)
- **Primary-500**: `#2B7FA3` (淡藍，hover 狀態)
- **Primary-300**: `#7CBFD4` (亮藍，背景)
- **Primary-100**: `#E8F4F8` (超淡藍，背景填充)

#### 輔助色 - 綠色（成功、確認）
- **Success-700**: `#00A651`
- **Success-500**: `#00D66D`
- **Success-100**: `#D4F8E8`

#### 警告色 - 橙色（警告）
- **Warning-700**: `#E67E22`
- **Warning-500**: `#F39C12`
- **Warning-100**: `#FEF5E8`

#### 危險色 - 紅色（錯誤）
- **Error-700**: `#E74C3C`
- **Error-500**: `#E85D5D`
- **Error-100**: `#FDECEC`

#### 中性色
- **Gray-900**: `#1F2937` (文字)
- **Gray-700**: `#4B5563` (次級文字)
- **Gray-500**: `#9CA3AF` (邊框、分隔線)
- **Gray-300**: `#D1D5DB` (禁用狀態)
- **Gray-100**: `#F3F4F6` (背景)
- **White**: `#FFFFFF`

## 2. 字體規範

### 字體家族

#### 正文字體
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen",
  "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue",
  sans-serif;
```

#### 等寬字體（代碼）
```css
font-family: "Fira Code", "Source Code Pro", Menlo, monospace;
```

### 字號規範

| 名稱 | 大小 | 行高 | 用途 |
|------|------|------|------|
| **Heading 1** | 32px | 1.2 (38px) | 頁面標題 |
| **Heading 2** | 24px | 1.3 (31px) | 區段標題 |
| **Heading 3** | 20px | 1.4 (28px) | 小標題 |
| **Body Large** | 16px | 1.5 (24px) | 主要文字 |
| **Body** | 14px | 1.5 (21px) | 標準文字 |
| **Body Small** | 12px | 1.4 (17px) | 輔助文字 |
| **Caption** | 11px | 1.4 (15px) | 說明文字 |

### 字重

- **Regular**: 400
- **Medium**: 500
- **Semibold**: 600
- **Bold**: 700

### 應用示例

```
Heading 1: 32px Bold (700)
Heading 2: 24px Semibold (600)
Body: 14px Regular (400)
Caption: 11px Regular (400)
```

## 3. 間距規範

基於 8px 網格系統：

| Token | 值 | 用途 |
|-------|-----|------|
| **xs** | 4px | 小間距 |
| **sm** | 8px | 標準間距 |
| **md** | 16px | 常用間距 |
| **lg** | 24px | 大間距 |
| **xl** | 32px | 特大間距 |
| **2xl** | 48px | 超大間距 |

## 4. 圓角規範

| Token | 值 | 用途 |
|-------|-----|------|
| **none** | 0px | 直角 |
| **sm** | 4px | 輕微圓角 |
| **md** | 8px | 標準圓角 |
| **lg** | 12px | 大圓角 |
| **xl** | 16px | 特大圓角 |
| **full** | 9999px | 圓形（按鈕等） |

## 5. 陰影規範

### 低程度
```css
box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
```

### 中程度
```css
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
```

### 高程度
```css
box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
```

## 6. 核心元件規範

### 按鈕

#### 主要按鈕 (Primary)
- **背景**: Primary-700
- **文字**: White
- **內距**: 12px 24px
- **圓角**: md (8px)
- **Hover**: Primary-600
- **Active**: Primary-800
- **禁用**: Gray-300 背景，Gray-500 文字

#### 次要按鈕 (Secondary)
- **背景**: Gray-100
- **邊框**: 1px Gray-300
- **文字**: Gray-900
- **內距**: 12px 24px
- **Hover**: Gray-50
- **Active**: Gray-200

#### 危險按鈕 (Danger)
- **背景**: Error-700
- **文字**: White
- **Hover**: Error-800

### 輸入框

- **邊框**: 1px Gray-300
- **圓角**: md (8px)
- **內距**: 12px 16px
- **字號**: 14px
- **Focus**: 藍色邊框 + Primary-500 陰影
- **Placeholder**: Gray-500
- **禁用**: Gray-100 背景

### 卡片

- **背景**: White
- **邊框**: 1px Gray-200
- **圓角**: lg (12px)
- **內距**: 16px
- **陰影**: 中程度
- **Hover**: 細微陰影增加

## 7. 響應式設計

### Breakpoints

| 名稱 | 寬度 | 設備 |
|------|------|------|
| **Mobile** | 375px | 手機 |
| **Tablet** | 768px | 平板 |
| **Desktop** | 1024px | 桌機 |
| **Wide** | 1280px | 寬螢幕 |
| **Max** | 1920px | 超寬螢幕 |

### Grid System

- 基於 12 欄柵欄系統
- 最大寬度：1280px
- 邊距：24px (Desktop) / 16px (Tablet) / 16px (Mobile)

## 8. 動畫規範

### 持續時間

- **快速**: 150ms (UI 反饋)
- **標準**: 300ms (一般動畫)
- **緩慢**: 500ms (進場/離場)

### 緩動函數

```css
/* 標準 */
transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);

/* 易入 */
transition-timing-function: cubic-bezier(0.4, 0, 1, 1);

/* 易出 */
transition-timing-function: cubic-bezier(0, 0, 0.2, 1);
```

## 9. 圖表顏色

用於數據可視化：

```
Series 1: #2B7FA3 (Primary)
Series 2: #00A651 (Success)
Series 3: #F39C12 (Warning)
Series 4: #E85D5D (Error)
Series 5: #9CA3AF (Gray)
Series 6: #6366F1 (Indigo)
```

## 10. 可訪問性規範

### 色對比度

- **普通文字**: 最少 4.5:1 對比度
- **大型文字**: 最少 3:1 對比度
- **圖形**: 最少 3:1 對比度

### 焦點狀態

- 所有互動元素都必須有明確的焦點狀態
- 焦點指示器最少 2px
- 使用 Primary-700 邊框

## Figma 應用

此設計系統已在 Figma 中實現：

### Figma 文件結構

```
Factory Insider Design System
├── 📋 Tokens (色彩、字體、間距)
├── 🎨 Colors (色彩義工)
├── 🔤 Typography (字體樣式)
├── 🧩 Components (可重用元件)
│   ├── Buttons
│   ├── Input
│   ├── Cards
│   ├── Navigation
│   └── ...
├── 📱 Layouts (頁面範本)
└── 📖 Documentation (文檔)
```

### 使用指南

1. **同步元件**：所有 Figma 元件都與 Tailwind CSS 類對應
2. **設計令牌**：使用 Design Tokens 管理色彩和間距
3. **變體**：利用 Figma 變體功能管理不同狀態

---

**Figma 連結**：[待補充 - 由設計師在 Figma 建立]

**上次更新**：2026-02-28
**版本**：1.0
