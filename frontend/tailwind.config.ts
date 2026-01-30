import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#050505", // Deep Black
        surface: "#0f1115",    // Card Dark
        "surface-hover": "#1a1d23",
        primary: "#00E396",    // Trading Green
        danger: "#FF4560",     // Trading Red
        accent: "#7928CA",     // Purple
        "text-main": "#EAEAEA",
        "text-dim": "#888888",
        border: "#2A2A2A",
      },
    },
  },
  plugins: [],
};
export default config;