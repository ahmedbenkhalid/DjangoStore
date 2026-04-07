/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './node_modules/flowbite/**/*.js'
  ],
  theme: {
    extend: {
      fontFamily: {
        readex: ['"Readex Pro"', 'sans-serif'],
        inter: ['Inter', 'sans-serif'],
      },
      colors: {
        corporate: {
          50: '#eef4ff',
          100: '#dce7ff',
          200: '#c2d5ff',
          300: '#98baff',
          400: '#6994ff',
          500: '#446ff5',
          600: '#1A56DB',
          700: '#1a42c1',
          800: '#1c379d',
          900: '#1d327d',
          950: '#161e4d',
        },
        surface: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
        },
        charcoal: {
          50: '#f6f6f7',
          100: '#e2e3e5',
          200: '#c4c5c9',
          300: '#9ea0a6',
          400: '#7b7d84',
          500: '#5f6168',
          600: '#4d4f55',
          700: '#404146',
          800: '#36373b',
          900: '#2e2f32',
          950: '#1b1c1e',
        },
      },
      fontSize: {
        base: ['1.125rem', { lineHeight: '1.75' }],
      },
    },
  },
  plugins: [
    require('flowbite/plugin')
  ],
}
