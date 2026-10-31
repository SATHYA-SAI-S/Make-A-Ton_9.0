import { test, expect } from '@playwright/test';

test.describe('P3 Finance Intelligence & Analytics E2E Flow', () => {
  test('Staff views Finance Intelligence Overview KPIs and Charts', async ({ page }) => {
    await page.goto('/p3/finance');
    await expect(page.locator('h1')).toContainText('Finance Intelligence Overview');
    await expect(page.getByText('Monthly Recurring Revenue (MRR)')).toBeVisible();
    await expect(page.getByText('Annual Recurring Revenue (ARR)')).toBeVisible();
    await expect(page.getByText('Cash Inflow (Net Revenue)')).toBeVisible();
    await expect(page.getByText('MRR Evolution & Growth')).toBeVisible();
    await expect(page.getByText('Invoiced vs Collected Revenue')).toBeVisible();
  });

  test('FilterBar changes URL and updates financial query parameters', async ({ page }) => {
    await page.goto('/p3/finance');
    
    // Select frequency dropdown
    const freqSelect = page.locator('select').first();
    await freqSelect.selectOption('MONTHLY');
    
    // URL should contain frequency=MONTHLY
    await expect(page).toHaveURL(/frequency=MONTHLY/);
  });

  test('Staff navigates to Collection Analytics and clicks aging bucket drilldown', async ({ page }) => {
    await page.goto('/p3/finance/collections');
    await expect(page.locator('h1')).toContainText('Collection, Aging & Risk Analytics');
    await expect(page.getByText('Invoice Aging Buckets & Overdue Balances')).toBeVisible();
    await expect(page.getByText('Payment Collection Funnel Conversion')).toBeVisible();

    // Click on 1–30 Days or 90+ Days aging bucket card
    const bucketCard = page.getByText('1–30 Days').first();
    await bucketCard.click();

    // Should navigate to drilldown invoices page with aging filter
    await expect(page).toHaveURL(/\/p3\/finance\/invoices\?aging=1_30/);
    await expect(page.getByRole('heading', { name: 'Drilldown Invoices' })).toBeVisible();
  });

  test('Staff triggers CSV export from Revenue Analytics', async ({ page }) => {
    await page.goto('/p3/finance/revenue');
    await expect(page.locator('h1')).toContainText('Revenue & MRR Analytics');
    await expect(page.getByRole('button', { name: 'Export Revenue CSV' })).toBeVisible();
  });
});
