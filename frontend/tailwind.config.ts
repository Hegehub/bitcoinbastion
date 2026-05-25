import type { Config } from 'tailwindcss';

export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        bb: {
          orange: 'var(--bb-orange)',
          'orange-soft': 'var(--bb-orange-soft)',
          black: 'var(--bb-black)',
          graphite: 'var(--bb-graphite)',
          gray: 'var(--bb-gray)',
          border: 'var(--bb-border)',
          bg: 'var(--bb-bg)',
          'bg-soft': 'var(--bb-bg-soft)',
          success: 'var(--bb-success)',
          warning: 'var(--bb-warning)',
          danger: 'var(--bb-danger)',
          'node-blue': 'var(--bb-node-blue)',
        },
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        text: 'var(--text)',
        muted: 'var(--muted)',
        accent: 'var(--accent)',
        danger: 'var(--danger)',
      },
      fontFamily: {
        heading: ['var(--font-heading)'],
        body: ['var(--font-body)'],
        mono: ['var(--font-mono)'],
      },
    },
  },
} satisfies Config;
