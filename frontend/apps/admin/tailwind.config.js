/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "../../packages/ui/**/*.{js,ts,jsx,tsx,css}",
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
    },
  },
  plugins: [],
}
