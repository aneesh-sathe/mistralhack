import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#edf0ff",
          100: "#dde3ff",
          500: "#3553de",
          700: "#263b9f",
        },
        shell: {
          50: "#f9eef6",
          100: "#f3dfed",
          200: "#e8c8de",
        },
      },
      fontFamily: {
        display: [
          "\"SF Pro Display\"",
          "\"SF Pro Text\"",
          "-apple-system",
          "BlinkMacSystemFont",
          "\"Segoe UI\"",
          "sans-serif",
        ],
        sans: [
          "\"SF Pro Text\"",
          "\"SF Pro Display\"",
          "-apple-system",
          "BlinkMacSystemFont",
          "\"Segoe UI\"",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
