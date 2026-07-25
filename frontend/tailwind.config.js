/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0A0A0A',
        surface: '#111111',
        border: '#1E1E1E',
        gold: '#C9A84C',
        'gold-dim': '#8A6F2E',
        cream: '#F5F4F0',
        muted: '#6B6B6B',
        success: '#4A7C59',
        danger: '#8B2635',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'serif'],
        body: ['"DM Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}

