/**
 * Playwright E2E Specification for Invoicing & Payment Split Allocation Flow
 */

import { test, expect } from '@playwright/test';

test.describe('Invoicing Lifecycle & Split Allocation E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173/billing');
  });

  test('should display invoices table with status badges and filters', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Invoices Management');
    await expect(page.getByRole('button', { name: 'ALL' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'CONFIRMED' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'PAID' })).toBeVisible();
  });

  test('should open record payment modal with split allocation rows', async ({ page }) => {
    await page.getByRole('button', { name: 'Payments' }).click();
    await page.getByRole('button', { name: '+ Record Payment' }).click();

    await expect(page.locator('h3')).toContainText('Record Customer Payment');
    await expect(page.getByLabel('Customer ID')).toBeVisible();
    await expect(page.getByLabel('Method')).toBeVisible();

    // Add split allocation row
    await page.getByRole('button', { name: '+ Allocate to Invoice' }).click();
    await expect(page.locator('select').nth(1)).toBeVisible();
  });
});
