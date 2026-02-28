/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./apps/*/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./apps/*/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./packages/ui/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          900: "#0D3B66",
          700: "#1B5E7F",
          500: "#2B7FA3",
          300: "#7CBFD4",
          100: "#E8F4F8",
        },
        success: {
          700: "#00A651",
          500: "#00D66D",
          100: "#D4F8E8",
        },
        warning: {
          700: "#E67E22",
          500: "#F39C12",
          100: "#FEF5E8",
        },
        error: {
          700: "#E74C3C",
          500: "#E85D5D",
          100: "#FDECEC",
        },
        gray: {
          900: "#1F2937",
          700: "#4B5563",
          500: "#9CA3AF",
          300: "#D1D5DB",
          100: "#F3F4F6",
        },
      },
      spacing: {
        xs: "4px",
        sm: "8px",
        md: "16px",
        lg: "24px",
        xl: "32px",
        "2xl": "48px",
      },
      borderRadius: {
        none: "0px",
        sm: "4px",
        md: "8px",
        lg: "12px",
        xl: "16px",
        full: "9999px",
      },
      fontSize: {
        h1: ["32px", { lineHeight: "38px", fontWeight: "700" }],
        h2: ["24px", { lineHeight: "31px", fontWeight: "600" }],
        h3: ["20px", { lineHeight: "28px", fontWeight: "600" }],
        "body-lg": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        body: ["14px", { lineHeight: "21px", fontWeight: "400" }],
        "body-sm": ["12px", { lineHeight: "17px", fontWeight: "400" }],
        caption: ["11px", { lineHeight: "15px", fontWeight: "400" }],
      },
      fontWeight: {
        regular: "400",
        medium: "500",
        semibold: "600",
        bold: "700",
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        md: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        lg: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
      },
      screens: {
        sm: "375px",
        md: "768px",
        lg: "1024px",
        xl: "1280px",
        "2xl": "1920px",
      },
      transitionDuration: {
        fast: "150ms",
        standard: "300ms",
        slow: "500ms",
      },
      transitionTimingFunction: {
        standard: "cubic-bezier(0.4, 0, 0.2, 1)",
        in: "cubic-bezier(0.4, 0, 1, 1)",
        out: "cubic-bezier(0, 0, 0.2, 1)",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
}
