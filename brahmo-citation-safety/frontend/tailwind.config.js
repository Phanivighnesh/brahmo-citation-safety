/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#1a3a5c", light: "#2d5f8a" },
      },
    },
  },
  plugins: [],
}
