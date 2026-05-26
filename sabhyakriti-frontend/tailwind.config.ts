import type { Config } from 'tailwindcss';
import forms from '@tailwindcss/forms';

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        saffron: {
          50: '#fff4ee',
          100: '#ffe6d5',
          200: '#ffc9aa',
          300: '#ffa174',
          400: '#ff7040',
          500: '#FF6B2B',
          600: '#f04a0a',
          700: '#c73708',
          800: '#9e2e0f',
          900: '#7f2810',
          950: '#451106',
          DEFAULT: '#FF6B2B',
        },
        teal: {
          50: '#eef8fa',
          100: '#d5eef4',
          200: '#b0dce9',
          300: '#7ac3d9',
          400: '#3ea1c0',
          500: '#2584a6',
          600: '#22698d',
          700: '#1B4B5A',
          800: '#1a4050',
          900: '#1b3744',
          950: '#0c2230',
          DEFAULT: '#1B4B5A',
        },
        brand: {
          primary: '#FF6B2B',
          secondary: '#1B4B5A',
          background: '#FAFAFA',
          text: '#1A1A1A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'spin-slow': 'spin 3s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [forms],
};

export default config;
