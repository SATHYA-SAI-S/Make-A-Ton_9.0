import { test, expect } from '@playwright/test';

test.describe('P3 Financial Reports & Audit UI E2E Flow', () => {
  test('Staff navigates to Financial Reports and toggles report types', async ({ page }) => {
    await page.goto('/p3/reports');
    await expect(page.locator('h1')).toContainText('Financial Reports & Accounting Ledgers');

    // Verify presence of download actions
    await expect(page.getByRole('button', { name: /Download CSV/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Download PDF/ })).toBeVisible();

    // Verify report buttons
    await expect(page.getByText('Monthly Financial Pack')).toBeVisible();
    await expect(page.getByText('Revenue Ledger')).toBeVisible();
    await expect(page.getByText('Outstanding AR')).toBeVisible();
    await expect(page.getByText('Payments Ledger')).toBeVisible();
    await expect(page.getByText('Subscriptions')).toBeVisible();

    // Switch report
    await page.getByText('Revenue Ledger').click();
    await expect(page.getByText('Detailed breakdown of issued invoices')).toBeVisible({ timeout: 5000 });
  });

  test('Staff navigates to Audit Ledger and filters views', async ({ page }) => {
    await page.goto('/p3/audit');
    await expect(page.locator('h1')).toContainText('Immutable Audit Log & Compliance Ledger');

    // Verify preset tabs
    await expect(page.getByRole('button', { name: /All Audit Records/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Price Modification History/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Plan Configuration Changes/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Invoice Cancellations/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Subscription Lifecycles/ })).toBeVisible();

    // Switch to Price Modification tab
    await page.getByRole('button', { name: /Price Modification History/ }).click();
    await expect(page.locator('table')).toBeVisible();
  });
});
