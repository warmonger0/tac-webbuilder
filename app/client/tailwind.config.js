/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        secondary: '#64748b',
        'separator-green': '#10b981', // Emerald green for visual separator
      },
      animation: {
        'pulse-glow-purple': 'pulse-glow-purple 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-glow-red': 'pulse-glow-red 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flow-line': 'flow-line 2s linear infinite',
      },
      keyframes: {
        'pulse-glow-purple': {
          '0%, 100%': {
            opacity: '1',
            boxShadow: '0 0 20px rgba(168, 85, 247, 0.8), 0 0 40px rgba(168, 85, 247, 0.4)',
          },
          '50%': {
            opacity: '0.8',
            boxShadow: '0 0 30px rgba(168, 85, 247, 1), 0 0 60px rgba(168, 85, 247, 0.6)',
          },
        },
        'pulse-glow-red': {
          '0%, 100%': {
            opacity: '1',
            boxShadow: '0 0 20px rgba(239, 68, 68, 0.8), 0 0 40px rgba(239, 68, 68, 0.4)',
          },
          '50%': {
            opacity: '0.8',
            boxShadow: '0 0 30px rgba(239, 68, 68, 1), 0 0 60px rgba(239, 68, 68, 0.6)',
          },
        },
        'flow-line': {
          '0%': {
            transform: 'translateX(-100%)',
          },
          '100%': {
            transform: 'translateX(100%)',
          },
        },
      },
    },
  },
  plugins: [],
}
