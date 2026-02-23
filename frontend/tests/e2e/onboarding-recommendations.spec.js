const { test, expect } = require("@playwright/test");

const shouldRun = process.env.E2E_TESTS === "1";

test.describe("Onboarding and recommendations", () => {
  test.skip(!shouldRun, "Set E2E_TESTS=1 to run Playwright tests");

  test("protected routes redirect to login", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page.getByRole("heading", { name: "Log In" })).toBeVisible();
  });
});
