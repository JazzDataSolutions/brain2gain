import { defineConfig, devices } from "@playwright/test"

/**
 * CI-specific Playwright configuration for GitHub Actions
 * Optimized for Docker container environment
 */
export default defineConfig({
  testDir: "./tests",
  /* Run tests in files in parallel */
  fullyParallel: false, // Disabled for CI stability
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: true,
  /* Retry on CI */
  retries: 2,
  /* Single worker for CI */
  workers: 1,
  /* Reporter to use - HTML for artifacts */
  reporter: [
    ["html", { outputFolder: "playwright-report" }],
    ["junit", { outputFile: "test-results/junit.xml" }],
  ],

  /* Output directory for test results */
  outputDir: "test-results/",

  /* Shared settings for all the projects below */
  use: {
    /* Base URL - will be overridden by environment variable */
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://frontend-ci:3000",

    /* Collect trace when retrying the failed test */
    trace: "retain-on-failure",

    /* Screenshot on failure */
    screenshot: "only-on-failure",

    /* Video recording */
    video: "retain-on-failure",

    /* Longer timeouts for CI environment */
    actionTimeout: 30000,
    navigationTimeout: 60000,
  },

  /* Global timeout for entire test run */
  globalTimeout: 10 * 60 * 1000, // 10 minutes

  /* Timeout for each test */
  timeout: 60 * 1000, // 60 seconds

  /* Configure projects for major browsers */
  projects: [
    {
      name: "setup",
      testMatch: /.*\.setup\.ts/,
      use: {
        baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://frontend-ci:3000",
      },
    },

    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: "playwright/.auth/user.json",
        // Disable animations for faster tests
        reducedMotion: "reduce",
        // CI-specific viewport
        viewport: { width: 1280, height: 720 },
      },
      dependencies: ["setup"],
    },

    // Single browser for CI to reduce complexity and time
    // Firefox and Safari can be enabled later if needed
  ],

  /* No local dev server in CI - app is served by Docker */
  webServer: undefined,

  /* Global setup/teardown */
  globalSetup: process.env.CI
    ? undefined
    : require.resolve("./tests/global-setup.ts"),
  globalTeardown: process.env.CI
    ? undefined
    : require.resolve("./tests/global-teardown.ts"),
})
