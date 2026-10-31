import { test, expect } from '@playwright/test';

test.describe('P3 Financial Forecasting & Scenario Simulator E2E Flow', () => {
  test('Staff views Financial Forecasting Simulator with Projection labels', async ({ page }) => {
    await page.goto('/p3/finance/forecast');
    await expect(page.locator('h1')).toContainText('Financial Forecasting & Scenario Simulator');

    // Verify non-destructive disclaimer banner and PROJECTION badges
    await expect(page.getByText('Simulation & Scenario Sandbox')).toBeVisible();
    await expect(page.getByText('PROJECTION MODEL')).toBeVisible();
    await expect(page.getByText(/All metrics and curves on this page represent non-destructive mathematical what-if models/)).toBeVisible();

    // Verify summary KPI strip
    await expect(page.getByText('Starting MRR')).toBeVisible();
    await expect(page.getByText('Projected Ending MRR')).toBeVisible();
    await expect(page.getByText('Annualized Growth')).toBeVisible();
    await expect(page.getByText('Projected Invoiced')).toBeVisible();
    await expect(page.getByText('Projected Collections')).toBeVisible();
    await expect(page.getByText('Projected Outstanding')).toBeVisible();
  });

  test('Staff adjusts horizon and applies quick scenario presets', async ({ page }) => {
    await page.goto('/p3/finance/forecast');

    // Click on 24M horizon
    const horizonBtn = page.getByRole('button', { name: '24M' });
    await horizonBtn.click();
    await expect(horizonBtn).toHaveClass(/bg-indigo-600/);

    // Apply Aggressive preset
    const aggressivePreset = page.getByRole('button', { name: '🚀 Aggressive' });
    await aggressivePreset.click();

    // Verify simulation controls exist
    await expect(page.getByText('New Subscription Growth')).toBeVisible();
    await expect(page.getByText('Monthly Churn Rate')).toBeVisible();
    await expect(page.getByText('Collection Efficiency Rate')).toBeVisible();

    // Verify Chart and Mathematical Explanation Table
    await expect(page.getByText('MRR Trajectory: Baseline vs Simulated Scenario')).toBeVisible();
    await expect(page.getByText('Mathematical Step Explanations (Explainable Simulator)')).toBeVisible();
  });

  test('Staff opens Save Scenario modal', async ({ page }) => {
    await page.goto('/p3/finance/forecast');

    const saveBtn = page.getByRole('button', { name: 'Save Scenario' }).first();
    await saveBtn.click();

    // Modal should be visible
    await expect(page.getByRole('heading', { name: 'Save Simulation Scenario' })).toBeVisible();
    await expect(page.getByPlaceholder('e.g. Q1 Aggressive Expansion Model')).toBeVisible();
  });
});
