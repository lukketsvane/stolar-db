/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#101828',
        inkSoft: '#596579',
        rule: '#D8DEE8',
        paper: '#101828',
        rust: '#F0643B',
        teal: '#24A6B8',
        gold: '#F5BC42',
        highlight: '#FFF1C7',
        bg: '#FBF8F1',
      },
      fontFamily: {
        serif: ['"EB Garamond"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
};
