import { test, expect } from "@playwright/test";
import { setupMockRoutes } from "./fixtures/mock-api";

test.describe("SleepMate Agent E2E", () => {
  test.beforeEach(async ({ page }) => {
    await setupMockRoutes(page);
  });

  test("完整用户流程：首页 → Check-in → Routine → 反馈保存 → Dashboard", async ({
    page,
  }) => {
    // ===== 1. 用户打开首页 =====
    await page.goto("/");
    await expect(page.locator("h1")).toHaveText("SleepMate Agent");
    await expect(page.locator("text=AI 助眠助手")).toBeVisible();

    // ===== 2. 点击开始 Check-in =====
    // 首页没有显式链接，直接导航到 /checkin
    await page.goto("/checkin");
    await expect(page.locator("h1")).toHaveText("睡前 Check-in");
    await expect(page.locator("text=记录你的睡前状态")).toBeVisible();

    // ===== 3. 填写睡前状态 =====
    // 选择心情：焦虑
    await page.getByRole("button", { name: "焦虑" }).click();
    await expect(page.getByRole("button", { name: "焦虑" })).toHaveClass(
      /bg-blue-600/
    );

    // 设置精力水平滑块
    const energySlider = page.locator('input[type="range"]').nth(0);
    await energySlider.fill("4");

    // 设置压力水平滑块
    const stressSlider = page.locator('input[type="range"]').nth(1);
    await stressSlider.fill("7");

    // 开启咖啡因开关
    const caffeineToggle = page.locator("button").filter({ has: page.locator("span.rounded-full") }).first();
    const isCaffeineOff = await caffeineToggle.evaluate(
      (el) => el.classList.contains("bg-slate-600")
    );
    if (isCaffeineOff) {
      await caffeineToggle.click();
    }

    // 设置屏幕时间
    const screenSlider = page.locator('input[type="range"]').nth(2);
    await screenSlider.fill("120");

    // 选择可用放松时间：15分钟
    await page.getByRole("button", { name: "15分钟" }).click();
    await expect(page.getByRole("button", { name: "15分钟" })).toHaveClass(
      /bg-blue-600/
    );

    // 选择偏好音频：雨声
    await page.getByRole("button", { name: "雨声" }).click();

    // 填写备注
    await page.locator("textarea").fill("今天工作压力很大");

    // ===== 4. 提交后进入分析结果 =====
    await page.getByRole("button", { name: "提交" }).click();

    // 等待分析结果出现
    await expect(page.locator("text=入睡风险")).toBeVisible();
    await expect(page.locator("text=中风险")).toBeVisible();
    await expect(page.getByRole("heading", { name: "建议" })).toBeVisible();
    await expect(
      page.getByText("建议进行 10 分钟深呼吸练习")
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "推荐活动" })).toBeVisible();

    // ===== 5. 点击生成助眠计划 → 进入 Routine 页面 =====
    await page.getByRole("button", { name: "生成今晚助眠计划" }).click();

    // 验证跳转到 routine 页面
    await expect(page).toHaveURL(/\/routine/);
    await expect(page.locator("h1")).toHaveText("今晚助眠计划");
    await expect(page.locator("text=根据你的状态量身定制")).toBeVisible();

    // ===== 6. 页面显示助眠计划 =====
    await expect(page.getByText("10 分钟呼吸放松计划")).toBeVisible();
    await expect(page.getByText("针对焦虑和高压力状态")).toBeVisible();
    await expect(page.getByRole("heading", { name: "步骤" })).toBeVisible();
    await expect(page.getByText("准备阶段", { exact: true })).toBeVisible();
    await expect(page.getByText("腹式呼吸", { exact: true })).toBeVisible();
    await expect(page.getByText("渐进式肌肉放松", { exact: true })).toBeVisible();
    await expect(page.getByText("冥想收尾", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "引导脚本" })).toBeVisible();
    await expect(page.getByRole("button", { name: "生成语音引导" })).toBeVisible();

    // ===== 7. 用户保存反馈（提交 sleep log） =====
    // 通过 API 保存睡眠反馈（mock）
    const saveResponse = await page.evaluate(async () => {
      const res = await fetch("http://localhost:8000/api/v1/sleep-log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          log_date: "2026-07-21",
          bedtime: "23:00:00",
          wake_time: "07:00:00",
          sleep_latency_minutes: 15,
          awakenings: 1,
          sleep_quality: 4,
          mood_before_sleep: "calm",
          stress_level: 3,
          caffeine_after_3pm: true,
          screen_time_minutes: 120,
          notes: "按照助眠计划练习后感觉好多了",
        }),
      });
      return res.json();
    });
    expect(saveResponse.id).toBe(1);

    // ===== 8. Dashboard 显示更新后的摘要 =====
    await page.goto("/dashboard");
    await expect(page.locator("h1")).toHaveText("睡眠 Dashboard");
    await expect(page.locator("text=最近 7 天睡眠数据概览")).toBeVisible();

    // 验证摘要卡片显示
    await expect(page.locator("text=72")).toBeVisible(); // 平均分
    await expect(page.locator("text=最近 7 天睡眠数据概览")).toBeVisible();

    // 验证最新评分
    await expect(page.locator("text=78")).toBeVisible(); // 最新评分
    await expect(page.locator("text=良好")).toBeVisible(); // 评分等级

    // 验证建议列表
    await expect(
      page.locator("text=继续保持规律的作息时间")
    ).toBeVisible();
    await expect(
      page.locator("text=建议减少睡前屏幕使用时间")
    ).toBeVisible();
  });

  test("Check-in 表单提交后可以重新填写", async ({ page }) => {
    await page.goto("/checkin");

    // 提交表单
    await page.getByRole("button", { name: "提交" }).click();
    await expect(page.locator("text=入睡风险")).toBeVisible();

    // 点击重新填写
    await page.getByRole("button", { name: "重新填写" }).click();
    await expect(page.locator("text=当前心情")).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toHaveText("提交");
  });

  test("Routine 页面无数据时显示空状态", async ({ page }) => {
    await page.goto("/routine");
    await expect(page.locator("text=今晚助眠计划")).toBeVisible();
    await expect(page.locator("text=还没有睡前数据，请先完成 Check-in")).toBeVisible();
    await expect(page.getByRole("link", { name: "前往 Check-in" })).toBeVisible();
  });

  test("Dashboard 无数据时显示空状态", async ({ page }) => {
    await page.route(
      "http://localhost:8000/api/v1/dashboard/summary*",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            days: 7,
            record_count: 0,
            averages: null,
            latest_score: null,
            advice: [],
          }),
        });
      }
    );

    await page.goto("/dashboard");
    await expect(page.locator("text=睡眠 Dashboard")).toBeVisible();
    await expect(page.locator("text=暂无睡眠记录")).toBeVisible();
  });
});
