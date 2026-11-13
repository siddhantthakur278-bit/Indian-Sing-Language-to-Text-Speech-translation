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
        navy: {
          DEFAULT: "#14213D",
          light: "#1F2F54",
          dark: "#0B1324"
        },
        teal: {
          DEFAULT: "#0FA3B1",
          light: "#21B5C3",
          dark: "#0A7984"
        },
        accent: {
          orange: "#F77F00",
          yellow: "#FCBF49"
        },
        alert: {
          red: "#D62839"
        }
      },
      fontFamily: {
        sans: ['Noto Sans', 'Noto Sans Devanagari', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
