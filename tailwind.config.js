/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '15': '3.75rem',
        '17': '4.25rem',
        '18': '4.5rem',
        '19': '4.75rem',
        '27': '6.75rem',
        '33': '8.25rem',
        '34': '8.5rem',
        '37': '9.25rem',
        '45': '11.25rem',
        '52': '13rem',
        '55': '13.75rem',
        '70': '17.5rem',
        '75': '18.75rem',
        '81': '20.25rem',
        '88': '22rem',
        '96': '24rem',
      },
    },
  },
  plugins: [],
} 