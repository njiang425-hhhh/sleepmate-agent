import { render, screen, waitFor } from "@testing-library/react";
import DashboardPage from "@/app/dashboard/page";

const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

function mockDashboard(data: Record<string, unknown>) {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => data,
  });
}

function mockError() {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    json: async () => ({ detail: "error" }),
  });
}

describe("DashboardPage", () => {
  it("shows loading state", () => {
    mockDashboard({ record_count: 0, averages: null, latest_score: null, advice: [] });
    render(<DashboardPage />);
    expect(screen.getByText("加载中...")).toBeInTheDocument();
  });

  it("shows empty state when no records", async () => {
    mockDashboard({
      days: 7,
      record_count: 0,
      averages: null,
      latest_score: null,
      advice: ["暂无睡眠记录，请先填写睡眠日志。"],
    });
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("暂无睡眠记录")).toBeInTheDocument();
    });
  });

  it("shows dashboard cards when data exists", async () => {
    mockDashboard({
      days: 7,
      record_count: 3,
      averages: {
        sleep_latency_minutes: 20.0,
        awakenings: 1.0,
        sleep_quality: 4.0,
        stress_level: 3.0,
        screen_time_minutes: 30.0,
        score: 72.6,
      },
      latest_score: {
        date: "2026-07-10",
        score: 79,
        level: "good",
        level_label: "良好",
        breakdown: {
          latency: { score: 15, max_score: 20, label: "入睡耗时" },
          awakenings: { score: 16, max_score: 20, label: "夜间醒来" },
          quality: { score: 20, max_score: 25, label: "睡眠质量" },
          stress: { score: 16, max_score: 20, label: "压力水平" },
          screen: { score: 12, max_score: 15, label: "屏幕时间" },
        },
      },
      advice: ["睡眠质量不错，有小幅优化空间。"],
    });
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("平均入睡耗时")).toBeInTheDocument();
      expect(screen.getByText("79")).toBeInTheDocument();
      expect(screen.getByText("良好")).toBeInTheDocument();
      expect(screen.getByText("睡眠质量不错，有小幅优化空间。")).toBeInTheDocument();
    });
  });

  it("shows error on fetch failure", async () => {
    mockError();
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("加载失败")).toBeInTheDocument();
    });
  });
});
