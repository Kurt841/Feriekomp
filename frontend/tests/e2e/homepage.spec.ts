import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('should load the homepage successfully', async ({ page }) => {
    await page.goto('/');

    // Sjekk at hovedoverskriften er synlig
    await expect(page.getByRole('heading', { name: /Feriekompensasjon Kalkulator/i })).toBeVisible();

    // Sjekk at ikon er synlig
    const icon = page.locator('svg').first();
    await expect(icon).toBeVisible();
  });

  test('should display the form with all required fields', async ({ page }) => {
    await page.goto('/');

    // Sjekk at alle nødvendige felt eksisterer ved å bruke placeholder eller text
    await expect(page.getByText(/Startdato for ferien/i)).toBeVisible();
    await expect(page.getByText(/Sluttdato for ferien/i)).toBeVisible();
    await expect(page.getByText(/Dato for legebesøk/i)).toBeVisible();
    await expect(page.getByText(/Total reisebeløp/i)).toBeVisible();
    await expect(page.getByText(/Antall personer/i)).toBeVisible();
    await expect(page.getByText(/Antall dager sengeleie/i)).toBeVisible();

    // Sjekk at submit-knappen finnes
    await expect(page.getByRole('button', { name: /Beregn kompensasjon/i })).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('/');

    // Prøv å sende inn skjemaet uten å fylle ut noe
    await page.getByRole('button', { name: /Beregn kompensasjon/i }).click();

    // HTML5 validering skal forhindre innsending
    // Vi kan sjekke at ingen resultat vises
    await expect(page.getByText(/Total kompensasjon/i)).not.toBeVisible();
  });

  test('should check backend health endpoint', async ({ request }) => {
    const backendPort = process.env.PW_BACKEND_PORT || '5000';
    const response = await request.get(`http://localhost:${backendPort}/health`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
    expect(data).toHaveProperty('timestamp');
  });
});
