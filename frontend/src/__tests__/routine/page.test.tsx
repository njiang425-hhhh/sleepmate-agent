import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RoutinePage from "@/app/routine/page";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

jest.mock("next/link", () => {
  const React = require("react");
  return React.forwardRef(function Link({ children, href, ...props }: any, ref: any) {
    return React.createElement("a", { ...props, href, ref }, children);
  });
});

const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockSessionStorage: Record<string, string> = {};
const sessionStorageMock = {
  getItem: jest.fn((key: string) => mockSessionStorage[key] || null),
  setItem: jest.fn((key: string, value: string) => {
    mockSessionStorage[key] = value;
  }),
  removeItem: jest.fn((key: string) => {
    delete mockSessionStorage[key];
  }),
  clear: jest.fn(() => {
    Object.keys(mockSessionStorage).forEach((k) => delete mockSessionStorage[k]);
  }),
};
Object.defineProperty(window, "sessionStorage", { value: sessionStorageMock });

const CHECKIN_DATA = {
  mood: "relaxed",
  energy_level: 5,
  stress_level: 4,
  caffeine_after_3pm: false,
  screen_time_minutes: 30,
  available_minutes: 15,
  preferred_audio: "rain",
};

const SUCCESS_RESPONSE = {
  type: "success",
  routine: {
    title: "平静入睡放松计划",
    duration_minutes: 10,
    strategy: "通用的睡前放松计划",
    steps: [
      { order: 1, action: "准备就位", duration_seconds: 60, instruction: "躺好" },
      { order: 2, action: "深呼吸", duration_seconds: 300, instruction: "慢慢呼吸" },
    ],
    script: "请找一个舒适的姿势，闭上眼睛。让我们开始深呼吸练习。",
  },
  safety_notice: "本计划仅供参考，不替代专业医疗建议。",
  meta: {
    history_available: false,
    history_record_count: 0,
    generation_mode: "mock",
    generated_at: "2026-07-13T00:00:00Z",
  },
};

const CLARIFICATION_RESPONSE = {
  type: "supportive_clarification",
  message: "我听到了你的感受。",
  resources: [],
  meta: {
    history_available: false,
    history_record_count: 0,
    generation_mode: "rule_based",
    generated_at: "2026-07-13T00:00:00Z",
  },
};

const SAFETY_RESPONSE = {
  type: "safety_redirect",
  message: "感谢你的信任。",
  resources: [],
  immediate_actions: ["拨打急救电话", "联系信任的人"],
  meta: {
    history_available: false,
    history_record_count: 0,
    generation_mode: "rule_based",
    generated_at: "2026-07-13T00:00:00Z",
  },
};

beforeEach(() => {
  mockFetch.mockReset();
  sessionStorageMock.clear();
  sessionStorageMock.getItem.mockClear();
  sessionStorageMock.setItem.mockClear();
  sessionStorageMock.removeItem.mockClear();
  jest.restoreAllMocks();
});

function setupCheckinData() {
  sessionStorageMock.setItem("checkinData", JSON.stringify(CHECKIN_DATA));
}

function mockSuccess(data = SUCCESS_RESPONSE) {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => data,
  });
}

function mockError() {
  mockFetch.mockRejectedValueOnce(new Error("网络错误"));
}

describe("RoutinePage", () => {
  it("shows empty state when no checkin data", async () => {
    render(<RoutinePage />);
    await waitFor(() => {
      expect(screen.getByText(/还没有睡前数据/)).toBeInTheDocument();
    });
    expect(screen.getByText("前往 Check-in")).toBeInTheDocument();
  });

  it("shows loading state then success", async () => {
    setupCheckinData();
    let resolvePromise: (v: unknown) => void;
    mockFetch.mockReturnValueOnce(
      new Promise((resolve) => {
        resolvePromise = resolve;
      }),
    );
    render(<RoutinePage />);
    await waitFor(() => {
      expect(screen.getByText(/正在生成你的助眠计划/)).toBeInTheDocument();
    });
    resolvePromise!({ ok: true, json: async () => SUCCESS_RESPONSE });
    await waitFor(() => {
      expect(screen.getByText("平静入睡放松计划")).toBeInTheDocument();
    });
    expect(screen.getByText("准备就位")).toBeInTheDocument();
    expect(screen.getByText("深呼吸")).toBeInTheDocument();
  });

  it("shows success response", async () => {
    setupCheckinData();
    mockSuccess();
    render(<RoutinePage />);
    await waitFor(() => {
      expect(screen.getByText("平静入睡放松计划")).toBeInTheDocument();
    });
    expect(screen.getByText("通用的睡前放松计划")).toBeInTheDocument();
    expect(screen.getByText(/本计划仅供参考/)).toBeInTheDocument();
  });

  it("shows supportive clarification", async () => {
    setupCheckinData();
    mockSuccess(CLARIFICATION_RESPONSE);
    render(<RoutinePage />);
    await waitFor(() => {
      expect(screen.getByText("我听到了你的感受。")).toBeInTheDocument();
    });
  });

  it("shows safety redirect with actions", async () => {
    setupCheckinData();
    mockSuccess(SAFETY_RESPONSE);
    render(<RoutinePage />);
    await waitFor(() => {
      expect(screen.getByText("感谢你的信任。")).toBeInTheDocument();
    });
    expect(screen.getByText("拨打急救电话")).toBeInTheDocument();
    expect(screen.getByText("联系信任的人")).toBeInTheDocument();
  });

  it("shows error and retry button", async () => {
    setupCheckinData();
    mockError();
    render(<RoutinePage />);
    await waitFor(() => {
      expect(screen.getByText("网络错误")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "重试" })).toBeInTheDocument();
  });

  it("retry button triggers new request", async () => {
    setupCheckinData();
    mockError();
    render(<RoutinePage />);
    await waitFor(() => {
      expect(screen.getByText("网络错误")).toBeInTheDocument();
    });
    mockSuccess();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "重试" }));
    await waitFor(() => {
      expect(screen.getByText("平静入睡放松计划")).toBeInTheDocument();
    });
  });

  it("does not render raw HTML tags", async () => {
    setupCheckinData();
    mockSuccess();
    render(<RoutinePage />);
    await waitFor(() => {
      expect(screen.getByText("平静入睡放松计划")).toBeInTheDocument();
    });
    const scriptEl = screen.getByText(/请找一个舒适的姿势/);
    expect(scriptEl.innerHTML).not.toContain("<script>");
  });

  it("removes sessionStorage on success", async () => {
    setupCheckinData();
    mockSuccess();
    sessionStorageMock.removeItem.mockClear();
    render(<RoutinePage />);
    await waitFor(() => {
      expect(screen.getByText("平静入睡放松计划")).toBeInTheDocument();
    });
    expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("checkinData");
  });

  it("preserves sessionStorage on error for retry", async () => {
    setupCheckinData();
    mockError();
    sessionStorageMock.removeItem.mockClear();
    render(<RoutinePage />);
    await waitFor(() => {
      expect(screen.getByText("网络错误")).toBeInTheDocument();
    });
    expect(sessionStorageMock.removeItem).not.toHaveBeenCalledWith("checkinData");
  });
});
