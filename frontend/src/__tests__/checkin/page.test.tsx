import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CheckinPage from "@/app/checkin/page";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

beforeEach(() => {
  jest.restoreAllMocks();
  Object.defineProperty(global, "fetch", { value: jest.fn(), writable: true });
});

describe("Checkin Page", () => {
  it("renders all form fields", () => {
    render(<CheckinPage />);
    expect(screen.getByText("睡前 Check-in")).toBeInTheDocument();
    expect(screen.getByText("平静")).toBeInTheDocument();
    expect(screen.getByText("放松")).toBeInTheDocument();
    expect(screen.getByText("焦虑")).toBeInTheDocument();
    expect(screen.getByText("兴奋")).toBeInTheDocument();
    expect(screen.getByText("疲惫")).toBeInTheDocument();
    expect(screen.getByText("压力大")).toBeInTheDocument();
    expect(screen.getByText("5分钟")).toBeInTheDocument();
    expect(screen.getByText("10分钟")).toBeInTheDocument();
    expect(screen.getByText("15分钟")).toBeInTheDocument();
    expect(screen.getByText("20分钟")).toBeInTheDocument();
    expect(screen.getByText("无")).toBeInTheDocument();
    expect(screen.getByText("雨声")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "提交" })).toBeInTheDocument();
  });

  it("shows analysis result after successful submit", async () => {
    const mockResponse = {
      status: "success",
      checkin: {
        mood: "relaxed",
        energy_level: 5,
        stress_level: 4,
        caffeine_after_3pm: false,
        screen_time_minutes: 30,
        available_minutes: 15,
        preferred_audio: "rain",
      },
      analysis: {
        sleep_risk_level: "low",
        suggestions: ["状态良好"],
        recommended_activity: "meditation",
        recommended_duration_minutes: 10,
      },
    };

    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    render(<CheckinPage />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "提交" }));

    await waitFor(() => {
      expect(screen.getByText("入睡风险: 低风险")).toBeInTheDocument();
    });
    expect(screen.getByText("状态良好")).toBeInTheDocument();
    expect(screen.getByText("冥想")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "重新填写" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "生成今晚助眠计划" })).toBeInTheDocument();
  });

  it("shows error message on API failure", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      json: async () => ({
        detail: [{ msg: "stress_level 不能超过 10" }],
      }),
    } as Response);

    render(<CheckinPage />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "提交" }));

    await waitFor(() => {
      expect(screen.getByText("stress_level 不能超过 10")).toBeInTheDocument();
    });
  });
});
