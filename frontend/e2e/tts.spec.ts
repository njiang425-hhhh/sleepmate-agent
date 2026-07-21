import { test, expect } from "@playwright/test";
import {
  setupMockRoutes,
  mockTTSSuccess,
  mockTTSFailure,
  mockAudioSuccess,
  mockAudioFailure,
} from "./fixtures/mock-api";
import { MOCK_ROUTINE_RESPONSE } from "./fixtures/mock-data";

const ROUTINE_SCRIPT = MOCK_ROUTINE_RESPONSE.routine.script;

/** Navigate to routine page with checkinData in sessionStorage. */
async function goToRoutinePage(page: import("@playwright/test").Page) {
  await page.addInitScript((data) => {
    sessionStorage.setItem("checkinData", JSON.stringify(data));
  }, MOCK_ROUTINE_RESPONSE.routine);
  await page.goto("/routine");
  await expect(page.getByRole("heading", { name: "引导脚本" })).toBeVisible();
}

test.describe("TTS E2E", () => {
  test.beforeEach(async ({ page }) => {
    await setupMockRoutes(page);
  });

  test("正常按需生成语音", async ({ page }) => {
    const ttsHandle = await mockTTSSuccess(page, { delayMs: 400 });
    const audioHandle = await mockAudioSuccess(page);

    await goToRoutinePage(page);

    // Button should be visible before clicking
    const btn = page.getByRole("button", { name: "生成语音引导" });
    await expect(btn).toBeVisible();

    // Click and assert loading state appears
    await btn.click();
    await expect(page.getByText("正在生成语音...")).toBeVisible();
    // Button should be hidden during loading
    await expect(btn).not.toBeVisible();

    // Wait for audio player to appear
    await expect(page.getByText("AI 生成语音")).toBeVisible();

    // Verify audio element exists with correct attributes
    const audio = page.locator("audio");
    await expect(audio).toBeVisible();
    await expect(audio).toHaveAttribute("controls", "");
    await expect(audio).toHaveAttribute("preload", "none");

    // Verify src is a full URL pointing to the mock audio path
    const src = await audio.getAttribute("src");
    expect(src).toContain("/static/audio/mock-tts.mp3");

    // Loading indicator should be gone
    await expect(page.getByText("正在生成语音...")).not.toBeVisible();

    // Button should not reappear (audioRequested blocks it)
    await expect(btn).not.toBeVisible();

    // Text script should still be visible
    await expect(page.getByText(ROUTINE_SCRIPT)).toBeVisible();

    // Verify only one TTS request was made
    expect(ttsHandle.requestCount).toBe(1);

    await ttsHandle.clear();
    await audioHandle.clear();
  });

  test("TTS API 返回 503 后降级", async ({ page }) => {
    const ttsHandle = await mockTTSFailure(page, {
      delayMs: 400,
      status: 503,
    });

    await goToRoutinePage(page);

    const btn = page.getByRole("button", { name: "生成语音引导" });
    await expect(btn).toBeVisible();

    // Click to trigger TTS
    await btn.click();

    // Loading state should appear
    await expect(page.getByText("正在生成语音...")).toBeVisible();

    // Wait for error fallback
    await expect(page.getByText("音频生成失败，文字脚本仍可使用")).toBeVisible();

    // Loading should be gone
    await expect(page.getByText("正在生成语音...")).not.toBeVisible();

    // No audio player should exist
    await expect(page.locator("audio")).not.toBeVisible();
    await expect(page.getByText("AI 生成语音")).not.toBeVisible();

    // Text script should still be visible
    await expect(page.getByText(ROUTINE_SCRIPT)).toBeVisible();

    // Button should reappear for retry (audioRequested reset on error)
    await expect(btn).toBeVisible();

    // Retry: click again and verify it works
    await btn.click();
    await expect(page.getByText("正在生成语音...")).toBeVisible();

    // Verify only 2 TTS requests total (initial + retry)
    // Wait for second attempt to complete (it will also 503)
    await expect(page.getByText("音频生成失败，文字脚本仍可使用")).toBeVisible();
    expect(ttsHandle.requestCount).toBe(2);

    await ttsHandle.clear();
  });

  test("音频资源返回 404 后播放器降级", async ({ page }) => {
    const ttsHandle = await mockTTSSuccess(page, { delayMs: 400 });
    const audioHandle = await mockAudioFailure(page);

    await goToRoutinePage(page);

    const btn = page.getByRole("button", { name: "生成语音引导" });
    await btn.click();

    // Wait for TTS to succeed and audio player to render
    await expect(page.getByText("AI 生成语音")).toBeVisible();
    const audio = page.locator("audio");
    await expect(audio).toBeVisible();

    // Trigger actual load (preload="none" won't auto-fetch)
    await audio.evaluate((el: HTMLAudioElement) => {
      el.load();
    });

    // onError should fire → player hides, error message appears
    await expect(page.getByText("音频加载失败，请检查网络后重试。")).toBeVisible();
    await expect(audio).not.toBeVisible();
    await expect(page.getByText("AI 生成语音")).not.toBeVisible();

    // Text script should still be visible
    await expect(page.getByText(ROUTINE_SCRIPT)).toBeVisible();

    await ttsHandle.clear();
    await audioHandle.clear();
  });

  test("重复点击只发送一次请求", async ({ page }) => {
    const ttsHandle = await mockTTSSuccess(page, { delayMs: 500 });

    await goToRoutinePage(page);

    const btn = page.getByRole("button", { name: "生成语音引导" });
    await expect(btn).toBeVisible();

    // Click twice in rapid succession
    await btn.click();
    // Button should be hidden immediately (audioLoading=true)
    await expect(btn).not.toBeVisible();
    // Click again via evaluate since button is hidden
    await page.evaluate(() => {
      const buttons = document.querySelectorAll("button");
      for (const b of buttons) {
        if (b.textContent?.includes("生成语音引导")) {
          b.click();
          b.click();
        }
      }
    });

    // Wait for TTS to complete
    await expect(page.getByText("AI 生成语音")).toBeVisible();

    // Only one request should have been made
    expect(ttsHandle.requestCount).toBe(1);

    await ttsHandle.clear();
  });
});
