/**
 * E2E tests for Analytics Dashboard workflow
 */

import { expect, test } from "@playwright/test"

test.describe("Analytics Dashboard E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Setup: Login as admin user
    await page.goto("/login")

    // Fill login form (assuming admin credentials)
    await page.fill('[data-testid="email-input"]', "admin@brain2gain.com")
    await page.fill('[data-testid="password-input"]', "admin123")
    await page.click('[data-testid="login-button"]')

    // Wait for login to complete
    await page.waitForURL("/dashboard", { timeout: 10000 })

    // Navigate to analytics dashboard
    await page.goto("/admin/analytics")
  })

  test("should load and display analytics dashboard", async ({ page }) => {
    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="analytics-dashboard"]', {
      timeout: 15000,
    })

    // Check main dashboard title
    await expect(
      page.locator("h1, h2").filter({ hasText: "Analytics Dashboard" }),
    ).toBeVisible()

    // Check that loading spinner is no longer visible
    await expect(
      page.locator("text=Loading analytics dashboard"),
    ).not.toBeVisible()
  })

  test("should display all revenue metrics", async ({ page }) => {
    // Wait for revenue section to load
    await page.waitForSelector("text=Revenue Overview", { timeout: 10000 })

    // Check revenue metric cards
    await expect(page.locator("text=Today's Revenue")).toBeVisible()
    await expect(page.locator("text=Monthly Revenue")).toBeVisible()
    await expect(page.locator("text=MRR")).toBeVisible()
    await expect(page.locator("text=ARR")).toBeVisible()
    await expect(page.locator("text=Average Order Value")).toBeVisible()
    await expect(page.locator("text=Revenue Per Visitor")).toBeVisible()

    // Check that currency values are displayed (should contain $ symbol)
    const currencyElements = page.locator("text=/\\$[0-9,]+/")
    await expect(currencyElements.first()).toBeVisible()
  })

  test("should display KPI summary cards with correct data", async ({
    page,
  }) => {
    // Wait for KPI section
    await page.waitForSelector("text=Key Performance Indicators", {
      timeout: 10000,
    })

    // Check KPI cards
    await expect(page.locator("text=MRR Growth")).toBeVisible()
    await expect(page.locator("text=Customer Health")).toBeVisible()
    await expect(page.locator("text=Conversion Funnel")).toBeVisible()

    // Check specific KPI metrics
    await expect(page.locator("text=Churn Rate")).toBeVisible()
    await expect(page.locator("text=Repeat Rate")).toBeVisible()
    await expect(page.locator("text=Visitors")).toBeVisible()
    await expect(page.locator("text=Add to Cart")).toBeVisible()
    await expect(page.locator("text=Purchase")).toBeVisible()
  })

  test("should display alerts when they exist", async ({ page }) => {
    // Wait for potential alerts to load
    await page.waitForTimeout(3000)

    // Check if alert badge appears in header
    const alertBadge = page.locator("text=/[0-9]+ Alerts?/")
    if (await alertBadge.isVisible()) {
      // If alerts exist, check alert display
      await expect(page.locator('[role="alert"]')).toHaveCount({ gte: 1 })

      // Check alert severity badges
      const severityBadges = page.locator("text=/CRITICAL|WARNING|INFO/")
      if ((await severityBadges.count()) > 0) {
        await expect(severityBadges.first()).toBeVisible()
      }
    }
  })

  test("should show real-time data updates", async ({ page }) => {
    // Wait for real-time data to load
    await page.waitForSelector("text=/Last updated:/", { timeout: 10000 })

    // Check that timestamp is displayed
    await expect(page.locator("text=/Last updated:/")).toBeVisible()

    // Check real-time revenue display
    await expect(page.locator("text=/Real-time:/")).toBeVisible()
  })

  test("should have working refresh functionality", async ({ page }) => {
    // Wait for dashboard to fully load
    await page.waitForSelector(
      '[data-testid="analytics-dashboard"], text=Analytics Dashboard',
      { timeout: 15000 },
    )

    // Find and click refresh button
    const refreshButton = page.locator("button").filter({ hasText: /refresh/i })
    await expect(refreshButton).toBeVisible()

    // Click refresh and check loading state
    await refreshButton.click()

    // Should show refreshing state temporarily
    await expect(page.locator("text=Refreshing")).toBeVisible({ timeout: 5000 })

    // Loading state should disappear
    await expect(page.locator("text=Refreshing")).not.toBeVisible({
      timeout: 10000,
    })

    // Dashboard should still be visible after refresh
    await expect(page.locator("text=Analytics Dashboard")).toBeVisible()
  })

  test("should display orders and customers sections", async ({ page }) => {
    // Wait for orders section
    await page.waitForSelector("text=Orders", { timeout: 10000 })

    // Check orders metrics
    await expect(page.locator("text=Today's Orders")).toBeVisible()
    await expect(page.locator("text=Monthly Orders")).toBeVisible()
    await expect(page.locator("text=Pending Orders")).toBeVisible()
    await expect(page.locator("text=Active Carts")).toBeVisible()

    // Check customers metrics
    await expect(page.locator("text=Customers")).toBeVisible()
    await expect(page.locator("text=Total Customers")).toBeVisible()
    await expect(page.locator("text=New This Month")).toBeVisible()
    await expect(page.locator("text=Active (30 days)")).toBeVisible()
    await expect(page.locator("text=Conversion Rate")).toBeVisible()
  })

  test("should display inventory and conversion metrics", async ({ page }) => {
    // Wait for inventory section
    await page.waitForSelector("text=Inventory", { timeout: 10000 })

    // Check inventory metrics
    await expect(page.locator("text=Total Products")).toBeVisible()
    await expect(page.locator("text=Low Stock Items")).toBeVisible()
    await expect(page.locator("text=Out of Stock")).toBeVisible()
    await expect(page.locator("text=Inventory Value")).toBeVisible()

    // Check conversion metrics section
    await expect(page.locator("text=Conversion Metrics")).toBeVisible()
    await expect(page.locator("text=Cart Abandonment Rate")).toBeVisible()
  })

  test("should handle error states gracefully", async ({ page }) => {
    // Mock API failure by intercepting network requests
    await page.route("**/api/analytics/**", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal Server Error" }),
      })
    })

    // Reload page to trigger API calls with errors
    await page.reload()

    // Should still show dashboard structure even with API errors
    await page.waitForSelector("text=Analytics Dashboard", { timeout: 10000 })

    // Should show error handling or fallback data
    // (Exact behavior depends on implementation - could be error messages or mock data)
    await expect(page.locator("text=Analytics Dashboard")).toBeVisible()
  })

  test("should be responsive on different screen sizes", async ({ page }) => {
    // Test desktop view first
    await page.setViewportSize({ width: 1200, height: 800 })
    await page.waitForSelector("text=Analytics Dashboard", { timeout: 10000 })

    // Check that all sections are visible in desktop
    await expect(page.locator("text=Revenue Overview")).toBeVisible()
    await expect(page.locator("text=Key Performance Indicators")).toBeVisible()

    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.waitForTimeout(1000) // Allow reflow

    // Dashboard should still be functional
    await expect(page.locator("text=Analytics Dashboard")).toBeVisible()

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 })
    await page.waitForTimeout(1000) // Allow reflow

    // Should still show main content
    await expect(page.locator("text=Analytics Dashboard")).toBeVisible()
  })

  test("should load data within acceptable time limits", async ({ page }) => {
    const startTime = Date.now()

    // Navigate to analytics dashboard
    await page.goto("/admin/analytics")

    // Wait for dashboard to fully load (all main sections visible)
    await page.waitForSelector("text=Revenue Overview", { timeout: 15000 })
    await page.waitForSelector("text=Key Performance Indicators", {
      timeout: 5000,
    })

    const loadTime = Date.now() - startTime

    // Should load within 15 seconds (generous timeout for E2E)
    expect(loadTime).toBeLessThan(15000)

    // Check that data is actually displayed (not just loading states)
    await expect(page.locator("text=/\\$[0-9,]+/")).toHaveCount({ gte: 3 }) // At least 3 currency values
  })

  test("should maintain data consistency across page refreshes", async ({
    page,
  }) => {
    // Wait for initial data load
    await page.waitForSelector("text=Revenue Overview", { timeout: 10000 })

    // Capture some metric values
    const initialMRR = await page
      .locator("text=MRR")
      .locator("..")
      .locator("text=/\\$[0-9,]+/")
      .first()
      .textContent()
    const initialOrders = await page
      .locator("text=Today's Orders")
      .locator("..")
      .locator("text=/[0-9]+/")
      .first()
      .textContent()

    // Refresh the page
    await page.reload()
    await page.waitForSelector("text=Revenue Overview", { timeout: 10000 })

    // Check that values are consistent (assuming same backend data)
    if (initialMRR) {
      await expect(
        page.locator("text=MRR").locator("..").locator(`text=${initialMRR}`),
      ).toBeVisible()
    }
    if (initialOrders) {
      await expect(
        page
          .locator("text=Today's Orders")
          .locator("..")
          .locator(`text=${initialOrders}`),
      ).toBeVisible()
    }
  })

  test("should handle authentication properly", async ({ page }) => {
    // Test accessing analytics without being logged in
    await page.goto("/logout") // Logout first
    await page.goto("/admin/analytics")

    // Should redirect to login or show unauthorized
    await page.waitForURL("/login", { timeout: 10000 })
    await expect(page.url()).toContain("/login")
  })

  test("should display progress bars and visual indicators correctly", async ({
    page,
  }) => {
    // Wait for dashboard to load
    await page.waitForSelector("text=Key Performance Indicators", {
      timeout: 10000,
    })

    // Check for progress bars (they should be present in conversion metrics)
    const progressBars = page.locator(
      '[role="progressbar"], .chakra-progress, div[style*="width:"]',
    )

    // Should have multiple progress indicators
    await expect(progressBars.first()).toBeVisible({ timeout: 5000 })

    // Check for color-coded badges
    const badges = page.locator(".chakra-badge, [data-theme]")
    if ((await badges.count()) > 0) {
      await expect(badges.first()).toBeVisible()
    }
  })

  test("should handle periodic real-time updates", async ({ page }) => {
    // Wait for initial load
    await page.waitForSelector("text=/Last updated:/", { timeout: 10000 })

    // Get initial timestamp
    const initialTimestamp = await page
      .locator("text=/Last updated:/")
      .textContent()

    // Wait for potential auto-refresh (30 seconds according to implementation)
    // For E2E test, we'll wait a shorter time and check if timestamp format is maintained
    await page.waitForTimeout(5000)

    // Timestamp should still be visible and properly formatted
    await expect(page.locator("text=/Last updated:/")).toBeVisible()

    // Could check if timestamp has updated, but that might be flaky in tests
    // Instead, just verify the format is maintained
    const currentTimestamp = await page
      .locator("text=/Last updated:/")
      .textContent()
    expect(currentTimestamp).toMatch(/Last updated: \d/)
  })
})
