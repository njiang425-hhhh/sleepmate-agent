export const MOCK_CHECKIN_REQUEST = {
  mood: "anxious",
  energy_level: 4,
  stress_level: 7,
  caffeine_after_3pm: true,
  screen_time_minutes: 120,
  available_minutes: 15,
  preferred_audio: "rain",
  notes: "今天工作压力很大",
};

export const MOCK_CHECKIN_RESPONSE = {
  status: "success",
  checkin: MOCK_CHECKIN_REQUEST,
  analysis: {
    sleep_risk_level: "medium",
    suggestions: [
      "建议进行 10 分钟深呼吸练习",
      "睡前 1 小时避免使用电子设备",
      "可以尝试渐进式肌肉放松",
    ],
    recommended_activity: "breathing_exercise",
    recommended_duration_minutes: 10,
  },
};

export const MOCK_ROUTINE_RESPONSE = {
  type: "success" as const,
  routine: {
    title: "10 分钟呼吸放松计划",
    duration_minutes: 10,
    strategy: "针对焦虑和高压力状态的渐进式放松方案",
    steps: [
      {
        order: 1,
        action: "准备阶段",
        duration_seconds: 60,
        instruction: "找一个安静的地方坐下，闭上眼睛，调整呼吸节奏",
      },
      {
        order: 2,
        action: "腹式呼吸",
        duration_seconds: 180,
        instruction: "双手放在腹部，吸气时腹部隆起，呼气时腹部收缩，保持 4-7-8 节奏",
      },
      {
        order: 3,
        action: "渐进式肌肉放松",
        duration_seconds: 240,
        instruction: "从脚趾开始，依次收紧再放松每个肌肉群，感受紧张与放松的对比",
      },
      {
        order: 4,
        action: "冥想收尾",
        duration_seconds: 120,
        instruction: "保持平静的呼吸，想象自己在一个宁静的地方，让思绪慢慢平静下来",
      },
    ],
    script:
      "欢迎来到今晚的放松练习。首先，找一个舒适的位置坐下或躺下...\n\n现在开始腹式呼吸。吸气...4...5...6...7...屏住...然后缓慢呼气...\n\n接下来进行渐进式肌肉放松。先收紧你的脚趾...感受紧张...然后放松...\n\n最后，让自己的思绪平静下来。你现在已经准备好进入甜美的梦乡。",
  },
  safety_notice: "如果在练习过程中感到不适，请立即停止并寻求专业帮助。",
  meta: {
    history_available: true,
    history_record_count: 5,
    generation_mode: "mock" as const,
    generated_at: "2026-07-21T22:00:00Z",
  },
};

export const MOCK_SLEEP_LOG_REQUEST = {
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
};

export const MOCK_SLEEP_LOG_RESPONSE = {
  id: 1,
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
  created_at: "2026-07-21T07:30:00Z",
};

export const MOCK_DASHBOARD_RESPONSE = {
  days: 7,
  record_count: 5,
  averages: {
    sleep_latency_minutes: 18.5,
    awakenings: 1.2,
    sleep_quality: 3.8,
    stress_level: 4.5,
    screen_time_minutes: 95.0,
    score: 72,
  },
  latest_score: {
    date: "2026-07-21",
    score: 78,
    level: "good",
    level_label: "良好",
    breakdown: {
      sleep_latency: { score: 16, max_score: 20, label: "入睡速度" },
      sleep_duration: { score: 18, max_score: 20, label: "睡眠时长" },
      sleep_quality: { score: 15, max_score: 20, label: "睡眠质量" },
      mood: { score: 14, max_score: 20, label: "情绪状态" },
      lifestyle: { score: 15, max_score: 20, label: "生活习惯" },
    },
  },
  advice: [
    "继续保持规律的作息时间",
    "建议减少睡前屏幕使用时间",
    "可以尝试睡前冥想来提高睡眠质量",
  ],
};
