/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.{html,js}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        accent: {
          DEFAULT: '#e94560',
          hover: '#d63d56',
        },
        surface: {
          light: '#ffffff',
          dark: '#16213e',
        },
        canvas: {
          light: '#f0f2f5',
          dark: '#1a1a2e',
        },
        viewer: {
          light: '#e8eaf0',
          dark: '#0f0f23',
        },
      },
    },
  },
  plugins: [],
}
