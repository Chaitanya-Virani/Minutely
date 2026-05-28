import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        accent: {
          indigo: "#6366F1",
          teal: "#14B8A6",
          amber: "#F59E0B",
        },
      },
      backgroundImage: {
        "gradient-indigo": "linear-gradient(135deg, #6366F1 0%, #818CF8 100%)",
        "gradient-teal": "linear-gradient(135deg, #14B8A6 0%, #2DD4BF 100%)",
        "gradient-amber": "linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)",
      },
      boxShadow: {
        glow: "0 0 32px -8px rgba(99, 102, 241, 0.35)",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
