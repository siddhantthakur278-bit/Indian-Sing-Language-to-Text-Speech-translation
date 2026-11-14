/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Deep obsidian galaxy background
        space: {
          950: "#05070A",
          900: "#080B12",
          850: "#0D111A",
          800: "#131926",
          700: "#1E273A",
          border: "#1F2839",
        },
        // Metallic Luxury Gold palette
        gold: {
          50: "#FCF9EC",
          100: "#F8F2D0",
          200: "#F0E19E",
          300: "#E6CD68",
          400: "#DFBA3C",
          500: "#D4AF37", // Primary Metallic Gold
          600: "#B89124",
          700: "#8F6E18",
          800: "#6B5115",
          900: "#4A370F",
          glow: "#FFDF00",
        },
        // Radiant Ruby Crimson Red palette
        ruby: {
          50: "#FFF0F2",
          100: "#FFE1E4",
          200: "#FFC2C9",
          300: "#FFA3AE",
          400: "#FF6B7F",
          500: "#E63946", // Primary Ruby Crimson
          600: "#D62839",
          700: "#B01E2D",
          800: "#80121E",
          900: "#4D0A11",
          glow: "#FF3355",
        },
        // Legacy palette support
        navy: {
          DEFAULT: "#0D111A",
          light: "#161E2E",
          dark: "#080B12",
        },
        teal: {
          DEFAULT: "#0FA3B1",
          light: "#21B5C3",
          dark: "#0A7984",
        },
        accent: {
          orange: "#F77F00",
          yellow: "#FCBF49",
        },
        alert: {
          red: "#E63946",
        },
      },
      fontFamily: {
        sans: ['Noto Sans', 'Noto Sans Devanagari', 'sans-serif'],
      },
      animation: {
        'sparkle': 'sparkle 2.5s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'gold-shimmer': 'goldShimmer 3s ease infinite',
        'ruby-glow': 'rubyGlow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        sparkle: {
          '0%, 100%': { opacity: '0.2', transform: 'scale(0.8)' },
          '50%': { opacity: '1', transform: 'scale(1.2)' },
        },
        goldShimmer: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        rubyGlow: {
          '0%': { boxShadow: '0 0 10px rgba(230, 57, 70, 0.3)' },
          '100%': { boxShadow: '0 0 25px rgba(230, 57, 70, 0.7)' },
        },
      },
    },
  },
  plugins: [],
};
