# 元件庫與最佳實踐

Factory Insider 前端元件開發指南。

## 按鈕元件

### 主要按鈕 (Primary)

```tsx
<button className="px-6 py-3 bg-primary-700 text-white rounded-md hover:bg-primary-600 transition-colors">
  提交
</button>
```

**Tailwind 類**：
- `bg-primary-700` - 背景色
- `text-white` - 文字顏色
- `px-6 py-3` - 內距
- `rounded-md` - 圓角
- `hover:bg-primary-600` - Hover 狀態
- `transition-colors` - 動畫

### 次要按鈕 (Secondary)

```tsx
<button className="px-6 py-3 bg-gray-100 border border-gray-300 text-gray-900 rounded-md hover:bg-gray-50">
  取消
</button>
```

### 危險按鈕 (Danger)

```tsx
<button className="px-6 py-3 bg-error-700 text-white rounded-md hover:bg-error-800">
  刪除
</button>
```

## 輸入框元件

### 基礎輸入框

```tsx
<input
  type="text"
  placeholder="請輸入..."
  className="px-4 py-3 border border-gray-300 rounded-md text-body
    focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100
    disabled:bg-gray-100 disabled:text-gray-500"
/>
```

### 帶標籤的輸入框

```tsx
<div>
  <label className="block text-body font-medium text-gray-900 mb-md">
    郵箱地址
  </label>
  <input
    type="email"
    className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-100"
  />
</div>
```

## 卡片元件

### 基礎卡片

```tsx
<div className="bg-white border border-gray-200 rounded-lg p-md shadow-md hover:shadow-lg transition-shadow">
  <h3 className="text-h3 font-semibold text-gray-900 mb-sm">標題</h3>
  <p className="text-body text-gray-700">內容</p>
</div>
```

## 表單指南

### 表單結構

```tsx
<form className="space-y-lg">
  {/* 表單域組 */}
  <fieldset className="space-y-md">
    <legend className="text-h3 font-semibold text-gray-900">
      基本資訊
    </legend>

    {/* 表單項 */}
    <div className="space-y-sm">
      <label htmlFor="name" className="block text-body font-medium">
        名稱
      </label>
      <input
        id="name"
        type="text"
        className="w-full px-4 py-3 border border-gray-300 rounded-md"
      />
      {error && (
        <p className="text-body-sm text-error-700">{error}</p>
      )}
    </div>
  </fieldset>

  {/* 操作按鈕 */}
  <div className="flex gap-md justify-end">
    <button type="reset" className="/* Secondary Button Classes */">
      重置
    </button>
    <button type="submit" className="/* Primary Button Classes */">
      提交
    </button>
  </div>
</form>
```

## 彩色系統使用

### 文字顏色

```tsx
{/* 主要文字 */}
<p className="text-gray-900">主要內容</p>

{/* 次要文字 */}
<p className="text-gray-700">次要信息</p>

{/* 禁用文字 */}
<p className="text-gray-500">禁用狀態</p>

{/* 成功 */}
<p className="text-success-700">操作成功</p>

{/* 警告 */}
<p className="text-warning-700">警告訊息</p>

{/* 錯誤 */}
<p className="text-error-700">錯誤訊息</p>
}
```

### 背景顏色

```tsx
{/* 品牌背景 */}
<div className="bg-primary-100">品牌背景</div>

{/* 中性背景 */}
<div className="bg-gray-100">次要背景</div>

{/* 成功背景 */}
<div className="bg-success-100">成功背景</div>
}
```

## 間距使用

### 基本間距 Token

```tsx
{/* 外邊距 */}
<div className="m-lg">外邊距 24px</div>

{/* 內邊距 */}
<div className="p-md">內邊距 16px</div>

{/* Gap（用於 Flex/Grid） */}
<div className="flex gap-md">
  <div>Item 1</div>
  <div>Item 2</div>
</div>
}
```

## 響應式設計

### 工作流程

```tsx
{/* 行動版 (375px) → 平板 (768px) → 桌機 (1024px) */}
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
  {items.map((item) => (
    <Card key={item.id} {...item} />
  ))}
</div>

{/* 字號自適應 */}
<h1 className="text-h3 md:text-h2 lg:text-h1">響應式標題</h1>

{/* 內距自適應 */}
<div className="p-sm md:p-md lg:p-lg">響應式內距</div>
}
```

## 動畫與轉換

### Transition

```tsx
{/* 顏色轉換 */}
<button className="bg-primary-700 hover:bg-primary-600 transition-colors duration-standard">
  Hover 效果
</button>

{/* 所有屬性 */}
<div className="transition-all duration-300">過渡所有</div>
}
```

### Transform

```tsx
{/* Scale */}
<button className="hover:scale-105 transition-transform">
  縮放
</button>

{/* Translate */}
<div className="hover:-translate-y-1 transition-transform">
  上移
</div>
}
```

## 可訪問性檢查清單

- [ ] 所有互動元素都有焦點狀態
- [ ] 圖像有 `alt` 文字
- [ ] 表單標籤正確關聯輸入框
- [ ] 色對比度滿足 WCAG AA 標準
- [ ] 鍵盤導航可用
- [ ] 使用語義 HTML（`<button>` vs `<div>`）
- [ ] ARIA 標籤用於複雜元件

## 常見陷阱

❌ **不要**：
```tsx
// 不要使用內聯樣式
<div style={{ color: "#1B5E7F" }}>內容</div>

// 不要創建新的顏色類
<div className="text-custom-blue">內容</div>

// 不要忽視響應式設計
<div className="p-lg">總是大內距</div>
```

✅ **應該**：
```tsx
// 使用設計系統顏色
<div className="text-primary-700">內容</div>

// 使用預定義的 Tailwind 類
<div className="text-primary-700">內容</div>

// 考慮不同螢幕大小
<div className="p-sm md:p-md lg:p-lg">自適應內距</div>
```

## 元件命名約定

- 使用 PascalCase（例如 `UserProfile`、`InputField`）
- 加上功能前綴（例如 `FormInput`、`CardContent`）
- 避免過度抽象（命名應自說明其用途）

## 版本控制

Design System 遵循語義版本控制：
- **Major** (X.0.0)：破壞性更改（移除元件、顏色等）
- **Minor** (0.X.0)：新增元件或功能
- **Patch** (0.0.X)：修復和微調

---

**下次更新**：2026-03-28
**維護者**：UX/Design Team
