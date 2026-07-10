"use client";

interface Analysis {
  sleep_risk_level: string;
  suggestions: string[];
  recommended_activity: string;
  recommended_duration_minutes: number;
}

interface Props {
  analysis: Analysis;
  onReset: () => void;
}

const RISK_COLORS: Record<string, string> = {
  low: "bg-green-900/50 border-green-700 text-green-200",
  medium: "bg-yellow-900/50 border-yellow-700 text-yellow-200",
  high: "bg-red-900/50 border-red-700 text-red-200",
};

const RISK_LABELS: Record<string, string> = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
};

const ACTIVITY_LABELS: Record<string, string> = {
  breathing_exercise: "呼吸练习",
  meditation: "冥想",
  stretching: "拉伸",
  audio_relaxation: "音频放松",
};

export default function CheckinResult({ analysis, onReset }: Props) {
  return (
    <div className="space-y-6">
      <div
        className={`rounded-lg border px-4 py-3 ${
          RISK_COLORS[analysis.sleep_risk_level] || RISK_COLORS.medium
        }`}
      >
        <span className="font-medium">
          入睡风险: {RISK_LABELS[analysis.sleep_risk_level] || analysis.sleep_risk_level}
        </span>
      </div>

      <div className="rounded-lg bg-slate-700/50 border border-slate-600 p-4">
        <h3 className="text-sm font-medium text-slate-300 mb-3">建议</h3>
        <ul className="space-y-2">
          {analysis.suggestions.map((s, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-200">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400" />
              {s}
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-lg bg-slate-700/50 border border-slate-600 p-4">
        <h3 className="text-sm font-medium text-slate-300 mb-2">推荐活动</h3>
        <p className="text-lg text-white">
          {ACTIVITY_LABELS[analysis.recommended_activity] || analysis.recommended_activity}
        </p>
        <p className="text-sm text-slate-400 mt-1">
          建议时长: {analysis.recommended_duration_minutes} 分钟
        </p>
      </div>

      <button
        onClick={onReset}
        className="w-full rounded-lg bg-slate-700 px-4 py-3 text-sm font-medium text-slate-300 hover:bg-slate-600 transition"
      >
        重新填写
      </button>
    </div>
  );
}
