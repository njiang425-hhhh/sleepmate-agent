import { Page, Route } from "@playwright/test";
import {
  MOCK_CHECKIN_RESPONSE,
  MOCK_ROUTINE_RESPONSE,
  MOCK_SLEEP_LOG_RESPONSE,
  MOCK_DASHBOARD_RESPONSE,
} from "./mock-data";

const API_BASE = "http://localhost:8000";

// Valid minimal silent MP3 (MPEG1 Layer3, 128kbps, 44100Hz, mono, 1 frame)
// Same as FakeTTSProvider.SILENT_MP3 in the backend
const SILENT_MP3 = Buffer.from([
  0xff, 0xfb, 0x90, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
]);

// ── Base route setup (non-TTS APIs) ──

export async function setupMockRoutes(page: Page) {
  await page.route(`${API_BASE}/api/v1/checkin`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_CHECKIN_RESPONSE),
    });
  });

  await page.route(`${API_BASE}/api/v1/routine/generate`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_ROUTINE_RESPONSE),
    });
  });

  await page.route(`${API_BASE}/api/v1/sleep-log`, async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(MOCK_SLEEP_LOG_RESPONSE),
      });
    } else {
      await route.fallback();
    }
  });

  await page.route(
    `${API_BASE}/api/v1/dashboard/summary*`,
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_DASHBOARD_RESPONSE),
      });
    }
  );

  await page.route(`${API_BASE}/api/v1/sleep-log/recent*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "success",
        count: 5,
        logs: [MOCK_SLEEP_LOG_RESPONSE],
      }),
    });
  });
}

// ── TTS-specific configurable mocks ──

export interface TTSRouteHandle {
  requestCount: number;
  clear: () => Promise<void>;
}

/**
 * Mock TTS API success with configurable delay.
 * Returns a handle to inspect requestCount and clean up.
 */
export async function mockTTSSuccess(
  page: Page,
  opts: { delayMs?: number; cached?: boolean } = {}
): Promise<TTSRouteHandle> {
  const { delayMs = 400, cached = false } = opts;
  let requestCount = 0;

  const handler = async (route: Route) => {
    requestCount++;
    await new Promise((r) => setTimeout(r, delayMs));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        audio_path: "/static/audio/mock-tts.mp3",
        cached,
      }),
    });
  };

  await page.route(`${API_BASE}/api/v1/audio/tts`, handler);

  return {
    get requestCount() {
      return requestCount;
    },
    clear: () => page.unroute(`${API_BASE}/api/v1/audio/tts`, handler),
  };
}

/**
 * Mock TTS API failure (503).
 */
export async function mockTTSFailure(
  page: Page,
  opts: { delayMs?: number; status?: number; detail?: string } = {}
): Promise<TTSRouteHandle> {
  const {
    delayMs = 400,
    status = 503,
    detail = "语音服务暂时不可用，请稍后重试",
  } = opts;
  let requestCount = 0;

  const handler = async (route: Route) => {
    requestCount++;
    await new Promise((r) => setTimeout(r, delayMs));
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify({ detail }),
    });
  };

  await page.route(`${API_BASE}/api/v1/audio/tts`, handler);

  return {
    get requestCount() {
      return requestCount;
    },
    clear: () => page.unroute(`${API_BASE}/api/v1/audio/tts`, handler),
  };
}

/**
 * Mock audio file URL success (returns valid silent MP3).
 */
export async function mockAudioSuccess(page: Page): Promise<TTSRouteHandle> {
  let requestCount = 0;

  const handler = async (route: Route) => {
    requestCount++;
    await route.fulfill({
      status: 200,
      contentType: "audio/mpeg",
      body: SILENT_MP3,
    });
  };

  await page.route(`${API_BASE}/static/audio/**`, handler);

  return {
    get requestCount() {
      return requestCount;
    },
    clear: () => page.unroute(`${API_BASE}/static/audio/**`, handler),
  };
}

/**
 * Mock audio file URL failure (returns 404).
 */
export async function mockAudioFailure(page: Page): Promise<TTSRouteHandle> {
  let requestCount = 0;

  const handler = async (route: Route) => {
    requestCount++;
    await route.fulfill({
      status: 404,
      contentType: "text/plain",
      body: "Not Found",
    });
  };

  await page.route(`${API_BASE}/static/audio/**`, handler);

  return {
    get requestCount() {
      return requestCount;
    },
    clear: () => page.unroute(`${API_BASE}/static/audio/**`, handler),
  };
}
