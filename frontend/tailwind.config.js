/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0f172a',
          900: '#172036',
          800: '#1e293b',
        },
        slateglass: {
          700: '#334155',
          600: '#475569',
          500: '#64748b',
        },
        accent: {
          cyan: '#06b6d4',
          teal: '#14b8a6',
          purple: '#8b5cf6',
          success: '#22c55e',
          warning: '#f59e0b',
          danger: '#ef4444',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(148, 163, 184, 0.16), 0 20px 45px rgba(15, 23, 42, 0.45), 0 0 40px rgba(6, 182, 212, 0.12)',
        cyan: '0 0 30px rgba(6, 182, 212, 0.18)',
        purple: '0 0 35px rgba(139, 92, 246, 0.2)',
      },
      backgroundImage: {
        'panel-gradient': 'linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.72))',
        'hero-gradient': 'radial-gradient(circle at top left, rgba(6, 182, 212, 0.22), transparent 35%), radial-gradient(circle at top right, rgba(139, 92, 246, 0.18), transparent 30%)',
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
        pulseGlow: 'pulseGlow 3s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 0 rgba(6, 182, 212, 0.12)' },
          '50%': { boxShadow: '0 0 24px rgba(6, 182, 212, 0.22)' },
        },
      },
    },
  },
  plugins: [],
};
