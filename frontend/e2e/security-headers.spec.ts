import { test, expect } from "@playwright/test";

test.describe("Security Headers", () => {
  test("页面返回 X-Content-Type-Options: nosniff", async ({ page }) => {
    const response = await page.goto("/");
    expect(response).not.toBeNull();
    expect(response!.headers()["x-content-type-options"]).toBe("nosniff");
  });

  test("页面返回 X-Frame-Options: DENY", async ({ page }) => {
    const response = await page.goto("/");
    expect(response).not.toBeNull();
    expect(response!.headers()["x-frame-options"]).toBe("DENY");
  });

  test("页面返回 Referrer-Policy", async ({ page }) => {
    const response = await page.goto("/");
    expect(response).not.toBeNull();
    const referrer = response!.headers()["referrer-policy"];
    expect(referrer).toBeTruthy();
    expect(referrer).toContain("strict-origin");
  });

  test("页面返回 Permissions-Policy", async ({ page }) => {
    const response = await page.goto("/");
    expect(response).not.toBeNull();
    const pp = response!.headers()["permissions-policy"];
    expect(pp).toBeTruthy();
    expect(pp).toContain("camera=");
    expect(pp).toContain("microphone=");
  });

  test("页面返回 CSP Report-Only", async ({ page }) => {
    const response = await page.goto("/");
    expect(response).not.toBeNull();
    const csp = response!.headers()["content-security-policy-report-only"];
    expect(csp).toBeTruthy();
    expect(csp).toContain("default-src");
    expect(csp).toContain("connect-src");
    expect(csp).toContain("media-src");
  });

  test("CSP 允许 API connect-src", async ({ page }) => {
    const response = await page.goto("/");
    const csp = response!.headers()["content-security-policy-report-only"] || "";
    // Must allow connecting to the API backend
    expect(csp).toContain("http://localhost:8000");
  });

  test("CSP 允许音频 media-src", async ({ page }) => {
    const response = await page.goto("/");
    const csp = response!.headers()["content-security-policy-report-only"] || "";
    // Must allow loading audio from the API backend
    expect(csp).toContain("media-src");
    expect(csp).toContain("http://localhost:8000");
  });

  test("CSP 设置 frame-ancestors none", async ({ page }) => {
    const response = await page.goto("/");
    const csp = response!.headers()["content-security-policy-report-only"] || "";
    expect(csp).toContain("frame-ancestors 'none'");
  });

  test("Check-in 页面安全头完整", async ({ page }) => {
    const response = await page.goto("/checkin");
    expect(response).not.toBeNull();
    const headers = response!.headers();
    expect(headers["x-content-type-options"]).toBe("nosniff");
    expect(headers["x-frame-options"]).toBe("DENY");
    expect(headers["content-security-policy-report-only"]).toBeTruthy();
  });

  test("Routine 页面安全头完整", async ({ page }) => {
    const response = await page.goto("/routine");
    expect(response).not.toBeNull();
    const headers = response!.headers();
    expect(headers["x-content-type-options"]).toBe("nosniff");
    expect(headers["x-frame-options"]).toBe("DENY");
  });
});
