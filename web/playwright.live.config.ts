import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests/integration',
  outputDir: '../.scratch/qa/live-results',
  workers: 1,
  timeout: 90000,
  reporter: 'list',
  use: {
    baseURL: process.env.GIVAUDAN_LIVE_URL ?? 'http://127.0.0.1:5173',
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
});
