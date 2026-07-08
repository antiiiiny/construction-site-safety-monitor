/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0ea5e9",
          dark: "#0369a1",
          light: "#7dd3fc",
        },
        safe: {
          DEFAULT: "#22c55e",
          dark: "#15803d",
          light: "#86efac",
        },
        warning: {
          DEFAULT: "#f59e0b",
          dark: "#b45309",
          light: "#fcd34d",
        },
        danger: {
          DEFAULT: "#ef4444",
          dark: "#b91c1c",
          light: "#fca5a5",
        },
        surface: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          700: "#334155",
          800: "#1e293b",
          850: "#172033",
          900: "#0f172a",
          950: "#020617",
        },
        steel: {
          DEFAULT: "#64748b",
          light: "#94a3b8",
          dark: "#475569",
        },
        amber: {
          DEFAULT: "#f59e0b",
          dark: "#d97706",
          light: "#fbbf24",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "Avenir", "Helvetica", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};
