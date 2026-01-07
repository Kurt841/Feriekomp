import type { PlaywrightTestConfig } from '@playwright/test';

const FRONTEND_PORT = process.env.PW_FRONTEND_PORT || '3000';
const BACKEND_PORT = process.env.PW_BACKEND_PORT || '5000';

const config: PlaywrightTestConfig = {
  testDir: 'tests/e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: process.env.CI
        ? `bash -c 'source ../.venv/bin/activate && cd ../backend && ENV=test PORT=${BACKEND_PORT} ALLOWED_ORIGINS=http://localhost:${FRONTEND_PORT} DEV_DATABASE_URL=sqlite:///feriekomp_test.db uvicorn feriekomp.main:app --host 0.0.0.0 --port ${BACKEND_PORT}'`
        : `npm -C .. run start:backend`,
      url: `http://127.0.0.1:${BACKEND_PORT}/health`,
      reuseExistingServer: !process.env.CI,
      env: {
        PORT: String(BACKEND_PORT),
        ENV: process.env.CI ? 'test' : 'development',
        ALLOWED_ORIGINS: `http://localhost:${FRONTEND_PORT}`,
        ...(process.env.CI && { DEV_DATABASE_URL: 'sqlite:///feriekomp_test.db' }),
      },
      cwd: __dirname,
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120000,
    },
    {
      command: 'npm run dev',
      url: `http://127.0.0.1:${FRONTEND_PORT}`,
      reuseExistingServer: !process.env.CI,
      cwd: __dirname,
      env: {
        PORT: String(FRONTEND_PORT),
        API_HOST: 'localhost',
        API_PORT: String(BACKEND_PORT),
        NEXT_PUBLIC_API_BASE_URL: `http://localhost:${BACKEND_PORT}`,
      },
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120000,
    },
  ],
}; 

export default config;
