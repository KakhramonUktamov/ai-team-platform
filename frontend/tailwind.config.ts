import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: { 50: "#f0f4ff", 100: "#dbe4ff", 200: "#bac8ff", 400: "#748ffc", 500: "#4c6ef5", 600: "#3b5bdb", 700: "#364fc7", 800: "#1e3a8a", 900: "#0f1d45" },
        surface: { 50: "#fafafa", 100: "#f4f4f5", 200: "#e4e4e7", 300: "#d4d4d8" },
      },
      fontFamily: {
        sans: ['"DM Sans"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
