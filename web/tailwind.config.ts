import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        cream: "#FBF7EF",
        ink: "#1F2A24",
        cedar: { 50: "#EAF3EE", 100: "#CFE4D8", 600: "#1F6B47", 700: "#17553A", 800: "#0F3F2A" },
        date: { 100: "#F6E3CF", 600: "#A8581C" },
      },
      borderRadius: { card: "14px" },
    },
  },
  plugins: [],
} satisfies Config;
