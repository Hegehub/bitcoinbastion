import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  esbuild: { jsx: 'automatic' },
  resolve: { alias: { '@': path.resolve(__dirname, '.') } },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.tsx'],
    include: [
      'tests/homepage.test.tsx',
      'tests/navigation.test.tsx',
      'tests/command-palette.test.tsx',
      'tests/status-page.test.tsx',
      'tests/selfhost-wizard.test.tsx',
      'tests/api-client.test.ts',
      'tests/market-time-machine-ui.test.tsx',
      'tests/trace-api-contract.test.ts',
      'tests/trace-report-ui.test.tsx',
      'tests/lite-check.test.tsx',
    ],
  },
});
