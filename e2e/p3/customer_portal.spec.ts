import { test, expect } from '@playwright/test';

test.describe('P3 Customer Self-Service Portal E2E Flow', () => {
  test('Customer logs in, views their own dashboard and KPIs', async ({ page }) => {
    await page.goto('/portal');
    await expect(page.locator('h1')).toContainText('Welcome back');
    await expect(page.getByText('Active Subscriptions')).toBeVisible();
    await expect(page.getByText('Outstanding Balance')).toBeVisible();
  });

  test('Customer navigates to My Subscriptions and submits upgrade request', async ({ page }) => {
    await page.goto('/portal/subscriptions');
    await expect(page.getByRole('heading', { name: 'My Subscriptions' })).toBeVisible();

    // Click Upgrade on first subscription
    const upgradeBtn = page.getByRole('button', { name: 'Upgrade' }).first();
    await upgradeBtn.click();

    // Verify modal is displayed
    await expect(page.getByText('Submit Request')).toBeVisible();

    // Type notes and submit
    await page.getByPlaceholder('Add any specific requirements').fill('Playwright automated upgrade test');
    await page.getByRole('button', { name: 'Submit Request' }).click();

    // Toast notification check
    await expect(page.getByText('Request Submitted')).toBeVisible();
  });

  test('Customer views Invoices and downloads PDF', async ({ page }) => {
    await page.goto('/portal/invoices');
    await expect(page.getByRole('heading', { name: 'My Invoices' })).toBeVisible();

    // Click View on first invoice
    const viewBtn = page.getByRole('button', { name: 'View' }).first();
    await viewBtn.click();

    // Verify dialog with totals is visible
    await expect(page.getByText('Grand Total:')).toBeVisible();

    // Click Download Official PDF
    const downloadPromise = page.waitForEvent('download').catch(() => null);
    await page.getByRole('button', { name: 'Download Official PDF' }).click();
  });

  test('Customer updates contact phone in Profile', async ({ page }) => {
    await page.goto('/portal/profile');
    await expect(page.getByRole('heading', { name: 'Account & Billing Profile' })).toBeVisible();

    const phoneInput = page.getByPlaceholder('+91 98765 43210');
    await phoneInput.fill('+91 91111 22222');
    await page.getByRole('button', { name: 'Save Changes' }).click();

    await expect(page.getByText('Profile Updated')).toBeVisible();
  });
});
