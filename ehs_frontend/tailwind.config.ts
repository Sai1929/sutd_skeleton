import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#F5F2EC',
        card: '#FFFFFF',
        ink: '#0B1220',
        mute: '#5A6272',
        rule: '#E4DFD3',
        accent: '#1F3A8A',
        'accent-soft': '#E8ECF7',
        confirmed: '#1F7A3A',
        overridden: '#B26A00',
      },
      fontFamily: {
        serif: ['"Source Serif 4"', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        card: '4px',
        btn: '4px',
        pill: '999px',
      },
    },
  },
  plugins: [],
} satisfies Config
