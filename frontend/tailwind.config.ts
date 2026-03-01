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
          200: "#c9c1ff",
          300: "#a99cff",
          400: "#8570ff",
          500: "#5f43ff",
          600: "#4f33f0",
          700: "#4028d7",
          800: "#3220b0",
          900: "#261a88",
        },
        joy: {
          yellow: "#ffe22a",
          green: "#56ea99",
          purple: "#d4c2ff",
          pink: "#ff6eb4",
          orange: "#ff9f43",
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
      animation: {
        "bounce-gentle": "bounce-gentle 2s ease-in-out infinite",
        "slide-up": "slide-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-down": "slide-down 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "scale-in": "scale-in 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        shimmer: "shimmer 1.8s linear infinite",
        "fade-in": "fade-in 0.3s ease forwards",
        "spin-slow": "spin 3s linear infinite",
        "pulse-gentle": "pulse-gentle 2s ease-in-out infinite",
        "shake": "shake 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97) both",
        "glow-success": "glow-success 0.6s ease forwards",
        "float": "float 3s ease-in-out infinite",
        "draw": "draw 0.6s ease forwards",
        "confetti-fall": "confetti-fall 1s ease-in forwards",
      },
      keyframes: {
        "bounce-gentle": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-down": {
          "0%": { opacity: "0", transform: "translateY(-16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.92)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "pulse-gentle": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.7", transform: "scale(0.97)" },
        },
        shake: {
          "10%, 90%": { transform: "translateX(-1px)" },
          "20%, 80%": { transform: "translateX(2px)" },
          "30%, 50%, 70%": { transform: "translateX(-3px)" },
          "40%, 60%": { transform: "translateX(3px)" },
        },
        "glow-success": {
          "0%": { boxShadow: "0 0 0 0 rgba(86, 234, 153, 0.4)" },
          "70%": { boxShadow: "0 0 0 10px rgba(86, 234, 153, 0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(86, 234, 153, 0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
        draw: {
          "0%": { strokeDashoffset: "100" },
          "100%": { strokeDashoffset: "0" },
        },
        "confetti-fall": {
          "0%": { transform: "translateY(-20px) rotate(0deg)", opacity: "1" },
          "100%": { transform: "translateY(100px) rotate(720deg)", opacity: "0" },
        },
      },
      transitionTimingFunction: {
        spring: "cubic-bezier(0.16, 1, 0.3, 1)",
        bounce: "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
      },
      boxShadow: {
        "brand-glow": "0 8px 24px rgba(95, 67, 255, 0.28)",
        "brand-glow-lg": "0 12px 40px rgba(95, 67, 255, 0.36)",
        "lift": "0 8px 24px rgba(18, 20, 26, 0.1)",
        "lift-lg": "0 16px 40px rgba(18, 20, 26, 0.14)",
        "success-glow": "0 0 20px rgba(86, 234, 153, 0.5)",
      },
    },
  },
  plugins: [],
};

export default config;
