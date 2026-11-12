import { defineConfig, devices } from '@playwright/test';

const port = Number(process.env.GIVAUDAN_TEST_PORT ?? 5173);
if (!Number.isInteger(port) || port < 1 || port > 65535)
  throw new Error(
    'GIVAUDAN_TEST_PORT doit être un port entier entre 1 et 65535.',
  );
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: './tests/e2e',
  outputDir: '../.scratch/qa/playwright-results',
  fullyParallel: true,
  workers: 2,
  reporter: 'list',
  use: {
    baseURL,
    launchOptions: { executablePath: process.env.GIVAUDAN_TEST_CHROMIUM },
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: 'mobile',
      use: { ...devices['Pixel 7'], viewport: { width: 360, height: 800 } },
    },
  ],
  webServer: {
    command: `npm run dev -- --host 127.0.0.1 --port ${port}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI && !process.env.GIVAUDAN_TEST_PORT,
  },
});
