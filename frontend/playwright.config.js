const { defineConfig } = require("@playwright/test");

const baseURL = process.env.E2E_BASE_URL || "http://localhost:3001";

module.exports = defineConfig({
  testDir: "./tests/e2e",
  timeout: 30 * 1000,
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  webServer: {
    command: "npm start",
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
