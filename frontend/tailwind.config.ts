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
          50: "#f2efff",
          100: "#e2ddff",
          500: "#5f43ff",
          700: "#4028d7",
        },
        shell: {
          50: "#ecf3ee",
          100: "#dfe8e2",
          200: "#cfdad3",
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
