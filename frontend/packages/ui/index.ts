/**
 * Factory Insider UI Component Library
 *
 * This file exports all shared UI components and utilities
 * from the Design System.
 */

// Design System Tokens
export const colors = {
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
}

export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "16px",
  lg: "24px",
  xl: "32px",
  "2xl": "48px",
}

export const borderRadius = {
  sm: "4px",
  md: "8px",
  lg: "12px",
  xl: "16px",
  full: "9999px",
}

export const fontSize = {
  h1: { size: "32px", lineHeight: "38px", fontWeight: 700 },
  h2: { size: "24px", lineHeight: "31px", fontWeight: 600 },
  h3: { size: "20px", lineHeight: "28px", fontWeight: 600 },
  "body-lg": { size: "16px", lineHeight: "24px", fontWeight: 400 },
  body: { size: "14px", lineHeight: "21px", fontWeight: 400 },
  "body-sm": { size: "12px", lineHeight: "17px", fontWeight: 400 },
  caption: { size: "11px", lineHeight: "15px", fontWeight: 400 },
}

// Export CSS file path for global styles
export const globalStylesPath = "./globals.css"

// Component Type Definitions
export type ColorScheme = "light" | "dark"
export type ButtonVariant = "primary" | "secondary" | "danger"
export type ButtonSize = "sm" | "md" | "lg"
export type InputSize = "sm" | "md" | "lg"

// Utility Functions
export const getColorValue = (colorKey: string): string => {
  const keys = colorKey.split(".")
  let value: any = colors
  for (const key of keys) {
    value = value[key]
  }
  return value
}

/**
 * Merge className strings with Tailwind CSS classes
 * Useful for component composition and conditional styling
 */
export const cn = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(" ")
}

export default {
  colors,
  spacing,
  borderRadius,
  fontSize,
  getColorValue,
  cn,
}
