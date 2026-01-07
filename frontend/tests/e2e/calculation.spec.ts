import { test, expect } from '@playwright/test';

test.describe('Feriekompensasjon Calculation', () => {
  test('should calculate compensation for valid input', async ({ page }) => {
    await page.goto('/');

    // Fyll ut skjemaet med gyldige verdier ved å finne input felt basert på name attributt
    await page.locator('input[name="startdato_ferie"]').fill('2024-06-01');
    await page.locator('input[name="sluttdato_ferie"]').fill('2024-06-07');
    await page.locator('input[name="dato_legebesok"]').fill('2024-06-03');
    await page.locator('input[name="total_reisebelop"]').fill('12000');
    await page.locator('input[name="antall_personer"]').fill('2');
    await page.locator('input[name="antall_dager_sengeleie"]').fill('3');

    // Submit skjemaet
    await page.getByRole('button', { name: /Beregn kompensasjon/i }).click();

    // Vent på resultat
    await expect(page.getByText(/Total kompensasjon/i)).toBeVisible({ timeout: 10000 });

    // Sjekk at resultat inneholder en sum
    const resultat = page.locator('text=/kr/i').first();
    await expect(resultat).toBeVisible();

    // Sjekk at detaljer vises
    await expect(page.getByText(/Dagspris per person/i)).toBeVisible();
    await expect(page.getByText(/Gyldige dager/i)).toBeVisible();
  });

  test('should handle calculation with minimum values', async ({ page }) => {
    await page.goto('/');

    // Minimumsscenario: 1 person, 1 dag
    await page.locator('input[name="startdato_ferie"]').fill('2024-07-01');
    await page.locator('input[name="sluttdato_ferie"]').fill('2024-07-02');
    await page.locator('input[name="dato_legebesok"]').fill('2024-07-01');
    await page.locator('input[name="total_reisebelop"]').fill('3000');
    await page.locator('input[name="antall_personer"]').fill('1');
    await page.locator('input[name="antall_dager_sengeleie"]').fill('0');

    await page.getByRole('button', { name: /Beregn kompensasjon/i }).click();

    // Resultat skal vises
    await expect(page.getByText(/Total kompensasjon/i)).toBeVisible({ timeout: 10000 });
  });

  test('should calculate with extra day for doctor visit', async ({ page }) => {
    await page.goto('/');

    await page.locator('input[name="startdato_ferie"]').fill('2024-08-10');
    await page.locator('input[name="sluttdato_ferie"]').fill('2024-08-15');
    await page.locator('input[name="dato_legebesok"]').fill('2024-08-12');
    await page.locator('input[name="total_reisebelop"]').fill('8000');
    await page.locator('input[name="antall_personer"]').fill('1');
    await page.locator('input[name="antall_dager_sengeleie"]').fill('2');

    // Aktiver ekstra dag for legebesøk
    const checkbox = page.locator('input[name="ekstra_dag_for_legebesok"]');
    await checkbox.check();
    await expect(checkbox).toBeChecked();

    await page.getByRole('button', { name: /Beregn kompensasjon/i }).click();

    await expect(page.getByText(/Total kompensasjon/i)).toBeVisible({ timeout: 10000 });
  });

  test('should handle multiple persons', async ({ page }) => {
    await page.goto('/');

    await page.locator('input[name="startdato_ferie"]').fill('2024-09-01');
    await page.locator('input[name="sluttdato_ferie"]').fill('2024-09-10');
    await page.locator('input[name="dato_legebesok"]').fill('2024-09-05');
    await page.locator('input[name="total_reisebelop"]').fill('20000');
    await page.locator('input[name="antall_personer"]').fill('4');
    await page.locator('input[name="antall_dager_sengeleie"]').fill('3');

    await page.getByRole('button', { name: /Beregn kompensasjon/i }).click();

    await expect(page.getByText(/Total kompensasjon/i)).toBeVisible({ timeout: 10000 });

    // Med 4 personer skal dagsprisen være begrenset til maks 2000 kr
    await expect(page.getByText(/Dagspris per person/i)).toBeVisible();
  });

  test('should validate date range', async ({ page }) => {
    await page.goto('/');

    // Sluttdato før startdato (ugyldig)
    await page.locator('input[name="startdato_ferie"]').fill('2024-10-10');
    await page.locator('input[name="sluttdato_ferie"]').fill('2024-10-05');
    await page.locator('input[name="dato_legebesok"]').fill('2024-10-07');
    await page.locator('input[name="total_reisebelop"]').fill('5000');

    await page.getByRole('button', { name: /Beregn kompensasjon/i }).click();

    // Skal vise feilmelding eller ikke gi resultat
    await page.waitForTimeout(2000);
  });

  test('should use API endpoint directly', async ({ request }) => {
    const backendPort = process.env.PW_BACKEND_PORT || '5000';
    const response = await request.post(`http://localhost:${backendPort}/beregn`, {
      data: {
        startdato_ferie: '2024-06-01',
        sluttdato_ferie: '2024-06-07',
        dato_legebesok: '2024-06-03',
        total_reisebelop: 12000,
        antall_personer: 2,
        antall_dager_sengeleie: 3,
        ekstra_dag_for_legebesok: false,
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    // Sjekk at API returnerer forventet struktur
    expect(data).toHaveProperty('total_kompensasjon');
    expect(data).toHaveProperty('total_feriedager');
    expect(data).toHaveProperty('gyldige_dager');
    expect(data).toHaveProperty('dagspris_per_person');
    expect(data).toHaveProperty('dekkede_personer');

    // Sjekk at beregningen er rimelig
    expect(data.total_kompensasjon).toBeGreaterThan(0);
    expect(data.dagspris_per_person).toBeLessThanOrEqual(2000);
  });
});
