/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#FF6B6B',   // 豬粉紅色
        secondary: '#4ECDC4', // 亮綠松色
        accent: '#FFE66D',    // 柔和黃色
        background: '#F7FFF7', // 淡綠色背景
        text: '#1A535C',      // 深青色文字
      },
      fontFamily: {
        sans: ['Noto Sans TC', 'sans-serif'],
        display: ['Comic Sans MS', 'cursive'],
      },
      animation: {
        'bounce-slow': 'bounce 3s infinite',
      }
    },
  },
  plugins: [],
} 