import { test, expect } from '@playwright/test';

test('trace pages render advisory safety language', async ({ page }) => {
  await page.goto('/trace');
  await expect(page.getByRole('heading', { name: /bitcoin address check/i })).toBeVisible();
  await expect(page.getByText(/Never enter seed phrases, private keys, wallet files or signing material/i)).toBeVisible();
  await expect(page.getByText(/advisory-only/i)).toBeVisible();
});
