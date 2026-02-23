const { test, expect } = require("@playwright/test");

const shouldRun = process.env.E2E_TESTS === "1";

test.describe("Auth flow", () => {
  test.skip(!shouldRun, "Set E2E_TESTS=1 to run Playwright tests");

  test("signup page renders and validates form", async ({ page }) => {
    await page.goto("/signup");
    await expect(page.getByRole("heading", { name: "Create Account" })).toBeVisible();

    await page.getByRole("button", { name: "Sign Up" }).click();
    await expect(page.getByText(/Email and password are required/)).toBeVisible();
  });

  test("login page renders", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Log In" })).toBeVisible();
  });
});
