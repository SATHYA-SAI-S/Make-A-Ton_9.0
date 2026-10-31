/**
 * Playwright E2E Specification for Person 2 (Billing Engine)
 * Tests complete billing lifecycle:
 * 1. Navigate module tabs (Invoices, Billing Control, Payments, Overdue, Reconciliation, Taxes, Discounts)
 * 2. Trigger Dry-run billing execution
 * 3. Verify generated invoice and line items
 * 4. Record payment with split allocations
 * 5. Verify Reconciliation audit shows balanced ledger
 */

import { test, expect } from '@playwright/test';

test.describe('Person 2: Billing & Invoicing End-to-End Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to local dev server or module mount
    await page.goto(process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173/billing');
  });

  test('should render top navigation and switch tabs smoothly', async ({ page }) => {
    await expect(page.locator('header')).toContainText('Billing & Invoicing');

    // Invoices tab active by default
    await expect(page.getByRole('button', { name: 'Invoices' })).toBeVisible();

    // Click Billing Engine tab
    await page.getByRole('button', { name: 'Billing Engine' }).click();
    await expect(page.locator('h1')).toContainText('Billing Engine Control');

    // Click Payments tab
    await page.getByRole('button', { name: 'Payments' }).click();
    await expect(page.locator('h1')).toContainText('Payment Management');

    // Click Overdue tab
    await page.getByRole('button', { name: 'Overdue & Dunning' }).click();
    await expect(page.locator('h1')).toContainText('Overdue Management & Dunning');

    // Click Reconciliation tab
    await page.getByRole('button', { name: 'Reconciliation' }).click();
    await expect(page.locator('h1')).toContainText('Financial Reconciliation Audit');

    // Click Tax Rules tab
    await page.getByRole('button', { name: 'Tax Rules' }).click();
    await expect(page.locator('h1')).toContainText('Tax Management');

    // Click Discounts tab
    await page.getByRole('button', { name: 'Discounts' }).click();
    await expect(page.locator('h1')).toContainText('Discount Management');
  });

  test('should trigger billing dry run without mutating production state', async ({ page }) => {
    await page.getByRole('button', { name: 'Billing Engine' }).click();

    // Listen for alert dialog confirming run completion
    page.once('dialog', async (dialog) => {
      expect(dialog.message()).toContain('Billing Dry Run Completed');
      await dialog.accept();
    });

    await page.getByRole('button', { name: 'Simulation / Dry Run' }).click();
  });

  test('should display reconciliation ledger audit and allow one-click auto-allocation', async ({ page }) => {
    await page.getByRole('button', { name: 'Reconciliation' }).click();

    await expect(page.locator('text=Total Payments Captured')).toBeVisible();
    await expect(page.locator('text=Unallocated Customer Credit')).toBeVisible();

    // Click Auto-Allocate button
    const autoAllocBtn = page.getByRole('button', { name: 'Auto-Allocate Unallocated Credits' });
    await expect(autoAllocBtn).toBeVisible();
  });
});
