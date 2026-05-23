import type { Config } from 'tailwindcss'
export default {
  content: ['./app/**/*.{ts,tsx}','./components/**/*.{ts,tsx}'],
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)', surface:'var(--surface)', text:'var(--text)', muted:'var(--muted)', accent:'var(--accent)', danger:'var(--danger)'
      }
    }
  }
} satisfies Config
