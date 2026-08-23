/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Government & Institutional Intelligence Palette
        navy: {
          DEFAULT: '#102A43', // Primary Navy
          dark: '#0B1F33',
          light: '#243B53',
          50: '#F0F4F8',
          100: '#D9E2EC',
        },
        accentBlue: {
          DEFAULT: '#1769E0',
          light: '#3B82F6',
          50: '#EFF6FF',
        },
        accentTeal: {
          DEFAULT: '#147A73',
          50: '#EDF8F8',
          100: '#D6EFEF',
        },
        successGreen: {
          DEFAULT: '#14804A',
          light: '#1B9A59',
          50: '#EDF7F1',
          100: '#D5EFE0',
        },
        warningAmber: {
          DEFAULT: '#C27A00',
          light: '#E09A2D',
          50: '#FEF8EE',
          100: '#FDF1DD',
        },
        riskHigh: {
          DEFAULT: '#C2413B',
          50: '#FDF2F2',
          100: '#F9DFDF',
        },
        riskCritical: {
          DEFAULT: '#8F1D1D',
          50: '#FBF0F0',
          100: '#F5DCDC',
        },
        // Institutional Neutrals
        appBg: '#F7F8F6',
        appCard: '#FFFFFF',
        appSurface: '#F0F2ED',
        appBorder: '#E5E7EB',
        appBorderDark: '#D1D5DB',
        
        // Text
        textMain: '#172033',
        textMuted: '#667085',
        textLight: '#98A2B3',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Manrope', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'IBM Plex Mono', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 3px rgba(16, 42, 67, 0.05)',
        cardHover: '0 4px 12px rgba(16, 42, 67, 0.08)',
        dropdown: '0 10px 25px -5px rgba(16, 42, 67, 0.1), 0 8px 10px -6px rgba(16, 42, 67, 0.05)',
      }
    },
  },
  plugins: [],
}
