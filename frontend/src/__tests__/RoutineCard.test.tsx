import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RoutineCard from "@/app/routine/components/RoutineCard";
import { RoutineSuccessResponse } from "@/types/routine";

const mockFetch = jest.fn();
global.fetch = mockFetch;

const SUCCESS_DATA: RoutineSuccessResponse = {
  type: "success",
  routine: {
    title: "平静入睡放松计划",
    duration_minutes: 10,
    strategy: "通用的睡前放松计划",
    steps: [
      { order: 1, action: "准备就位", duration_seconds: 60, instruction: "躺好" },
    ],
    script: "请找一个舒适的姿势，闭上眼睛。",
  },
  safety_notice: "本计划仅供参考。",
  meta: {
    history_available: false,
    history_record_count: 0,
    generation_mode: "mock",
    generated_at: "2026-07-13T00:00:00Z",
  },
};

beforeEach(() => {
  mockFetch.mockReset();
});

describe("RoutineCard TTS integration", () => {
  it("shows generate audio button for success response", () => {
    render(<RoutineCard data={SUCCESS_DATA} />);
    expect(screen.getByRole("button", { name: "生成语音引导" })).toBeInTheDocument();
  });

  it("button has type=button", () => {
    render(<RoutineCard data={SUCCESS_DATA} />);
    const button = screen.getByRole("button", { name: "生成语音引导" });
    expect(button).toHaveAttribute("type", "button");
  });

  it("clicking button triggers TTS API call", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ audio_path: "/static/audio/test.mp3", cached: false }),
    });

    render(<RoutineCard data={SUCCESS_DATA} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "生成语音引导" }));

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/audio/tts",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows loading state after click", async () => {
    let resolvePromise: (v: unknown) => void;
    mockFetch.mockReturnValueOnce(
      new Promise((resolve) => {
        resolvePromise = resolve;
      }),
    );

    render(<RoutineCard data={SUCCESS_DATA} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "生成语音引导" }));

    await waitFor(() => {
      expect(screen.getByText("正在生成语音...")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "生成语音引导" })).not.toBeInTheDocument();

    resolvePromise!({ ok: true, json: async () => ({ audio_path: "/static/audio/x.mp3", cached: false }) });
  });

  it("shows audio player label after success", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ audio_path: "/static/audio/result.mp3", cached: false }),
    });

    const { container } = render(<RoutineCard data={SUCCESS_DATA} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "生成语音引导" }));

    await waitFor(() => {
      expect(screen.getByText("AI 生成语音")).toBeInTheDocument();
    });
    expect(container.querySelector("audio")).toBeInTheDocument();
  });

  it("shows error message on failure", async () => {
    mockFetch.mockRejectedValueOnce(new Error("网络错误"));

    render(<RoutineCard data={SUCCESS_DATA} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "生成语音引导" }));

    await waitFor(() => {
      expect(screen.getByText("音频生成失败，文字脚本仍可使用")).toBeInTheDocument();
    });
  });

  it("shows script text alongside audio", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ audio_path: "/static/audio/x.mp3", cached: false }),
    });

    const { container } = render(<RoutineCard data={SUCCESS_DATA} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "生成语音引导" }));

    await waitFor(() => {
      expect(screen.getByText("AI 生成语音")).toBeInTheDocument();
    });
    expect(container.querySelector("audio")).toBeInTheDocument();
    expect(screen.getByText(/请找一个舒适的姿势/)).toBeInTheDocument();
  });

  it("button is disabled during loading", async () => {
    mockFetch.mockReturnValueOnce(new Promise(() => {}));

    render(<RoutineCard data={SUCCESS_DATA} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "生成语音引导" }));

    await waitFor(() => {
      expect(screen.getByText("正在生成语音...")).toBeInTheDocument();
    });
  });
});
