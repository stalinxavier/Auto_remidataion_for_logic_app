/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        sap: {
          blue: '#0070F2',
          'blue-dark': '#0040B0',
          'blue-light': '#E8F4FD',
          teal: '#0FAAAA',
          green: '#107E3E',
          orange: '#E9730C',
          red: '#BB0000',
          yellow: '#E8A000',
          purple: '#6A2B81',
          gray: '#6A6D70',
          'gray-light': '#F5F6F7',
          'gray-bg': '#EDEFF0',
        },
      },
      fontFamily: {
        sans: ['72', '72full', 'Arial', 'Helvetica', 'sans-serif'],
      },
      boxShadow: {
        card: '0 0 0 1px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.06)',
        'card-hover': '0 0 0 1px rgba(0,112,242,0.3), 0 4px 16px rgba(0,112,242,0.1)',
      },
    },
  },
  plugins: [],
}
