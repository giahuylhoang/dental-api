import { test, expect } from "@playwright/test";

const MOCK_USER = {
  id: "mock-admin",
  clinic_id: "default",
  email: "admin@example.com",
  full_name: "Mock Admin",
  is_active: true,
  roles: ["admin"],
  permissions: ["*.*"],
};

async function injectAuth(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.evaluate((user) => {
    localStorage.setItem("accessToken", "mock-access-token");
    localStorage.setItem("authUser", JSON.stringify(user));
  }, MOCK_USER);
}

test("/login renders LoginCard (dark theme)", async ({ page }) => {
  await page.goto("/login");
  await expect(page.locator("form")).toBeVisible();
  // LoginCard uses sidebar/85 background — check for the sign-in label and heading
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  await expect(page.getByText("Welcome back")).toBeVisible();
});

const APP_ROUTES = [
  "/dashboard",
  "/patients",
  "/patients/mock-id",
  "/schedule",
  "/lab",
  "/billing",
  "/communications",
  "/crm",
  "/plans",
  "/reports",
  "/settings",
];

for (const route of APP_ROUTES) {
  test(`mock-authenticated session loads ${route}`, async ({ page }) => {
    await injectAuth(page);
    await page.goto(route);
    // Should not redirect to /login
    await expect(page).not.toHaveURL(/\/login/);
    // Page should render something visible
    await expect(page.locator("body")).toBeVisible();
  });
}

test('/plans shows overline "Engineering Decision: Locked"', async ({ page }) => {
  await injectAuth(page);
  await page.goto("/plans");
  await expect(
    page.getByText("Engineering Decision: Locked")
  ).toBeVisible();
});

test("/communications composer area shows the locked overline", async ({ page }) => {
  await injectAuth(page);
  await page.goto("/communications");
  await expect(
    page.getByText("Engineering Decision: Locked")
  ).toBeVisible();
});

test("/settings shows ≥2 locked overlays", async ({ page }) => {
  await injectAuth(page);
  await page.goto("/settings");
  const locked = page.getByText("Engineering Decision: Locked");
  await expect(locked.first()).toBeVisible();
  expect(await locked.count()).toBeGreaterThanOrEqual(2);
});

test("/reports shows ≥1 locked overlay", async ({ page }) => {
  await injectAuth(page);
  await page.goto("/reports");
  const locked = page.getByText("Engineering Decision: Locked");
  await expect(locked.first()).toBeVisible();
  expect(await locked.count()).toBeGreaterThanOrEqual(1);
});
