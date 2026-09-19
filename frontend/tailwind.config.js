/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"SF Pro Text"',
          '"SF Pro Display"',
          "Inter",
          "system-ui",
          "sans-serif",
        ],
        mono: [
          '"SF Mono"',
          "Menlo",
          "Monaco",
          "Consolas",
          '"Liberation Mono"',
          "monospace",
        ],
      },
      colors: {
        surface: {
          DEFAULT: '#fbfbfd',
          card: '#ffffff',
          elevated: '#f2f2f7',
          sidebar: '#f2f2f7',
          hover: '#e5e5ea',
          border: 'rgba(0, 0, 0, 0.08)',
        },
        apple: {
          blue: '#007aff',
          'blue-hover': '#0062cc',
          green: '#34c759',
          orange: '#ff9500',
          red: '#ff3b30',
          purple: '#af52de',
          teal: '#30b0c7',
          gray: '#8e8e93',
          lightgray: '#e5e5ea',
          ultralight: '#f2f2f7',
        },
        content: {
          primary: '#1d1d1f',
          secondary: '#59595e',
          tertiary: '#8e8e93',
          quaternary: '#c7c7cc',
        },
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#007aff',
          600: '#0062cc',
          700: '#0051a8',
        },
      },
      boxShadow: {
        'xs': '0 1px 2px 0 rgba(0, 0, 0, 0.04)',
        'sm': '0 1px 3px 0 rgba(0, 0, 0, 0.06), 0 1px 2px -1px rgba(0, 0, 0, 0.06)',
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.04), 0 0 0 1px rgba(0, 0, 0, 0.05)',
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02)',
        'popover': '0 10px 30px -4px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.08)',
        'stripe': '0 2px 5px -1px rgba(50, 50, 93, 0.05), 0 1px 3px -1px rgba(0, 0, 0, 0.08)',
        'linear': '0 0 0 1px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04)',
        'window': '0 30px 90px -10px rgba(0, 0, 0, 0.28), 0 0 0 1px rgba(255, 255, 255, 0.45)',
        'dock': '0 16px 40px -6px rgba(0, 0, 0, 0.22), 0 0 0 1px rgba(255, 255, 255, 0.4)',
        'glass-card': '0 8px 24px -4px rgba(0, 0, 0, 0.04), 0 0 0 1px rgba(255, 255, 255, 0.6)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'shimmer': 'shimmer 1.8s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
    },
  },
  plugins: [],
}
