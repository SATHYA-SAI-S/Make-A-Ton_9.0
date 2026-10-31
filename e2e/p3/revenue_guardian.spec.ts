import { test, expect } from '@playwright/test';

test.describe('P3 Revenue Guardian E2E Flow', () => {
  test('Staff views Revenue Guardian Dashboard and Anomaly Queue', async ({ page }) => {
    await page.goto('/p3/guardian');
    await expect(page.locator('h1')).toContainText('Revenue Guardian');

    // Verify key indicators and badges
    await expect(page.getByText('Autonomous Risk Engine')).toBeVisible();
    await expect(page.getByText('Total Open Alerts')).toBeVisible();
    await expect(page.getByText('Critical Alerts')).toBeVisible();
    await expect(page.getByText('High Severity')).toBeVisible();
    await expect(page.getByText('Estimated Financial Exposure')).toBeVisible();

    // Verify trigger button
    await expect(page.getByRole('button', { name: /Run Detection Cycle/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Detection Runs/ })).toBeVisible();
  });

  test('Staff filters anomalies by status, severity, and category', async ({ page }) => {
    await page.goto('/p3/guardian');

    // Click Critical severity filter
    const criticalBtn = page.getByRole('button', { name: 'CRITICAL' });
    await criticalBtn.click();
    await expect(criticalBtn).toHaveClass(/bg-rose-600/);

    // Click Billing category filter
    const billingBtn = page.getByRole('button', { name: 'BILLING' });
    await billingBtn.click();
    await expect(billingBtn).toHaveClass(/bg-indigo-600/);
  });

  test('Staff opens Detection Runs history modal', async ({ page }) => {
    await page.goto('/p3/guardian');

    const runsBtn = page.getByRole('button', { name: /Detection Runs/ });
    await runsBtn.click();

    await expect(page.getByRole('heading', { name: 'Detection Run History' })).toBeVisible();
  });
});
