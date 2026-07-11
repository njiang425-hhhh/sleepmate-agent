interface DashboardAverages {
  sleep_latency_minutes: number;
  awakenings: number;
  sleep_quality: number;
  stress_level: number;
  screen_time_minutes: number;
  score: number;
}

interface Props {
  averages: DashboardAverages;
}

const cards = [
  { key: "sleep_latency_minutes" as const, label: "平均入睡耗时", unit: "分钟" },
  { key: "sleep_quality" as const, label: "平均睡眠质量", unit: "/ 5" },
  { key: "stress_level" as const, label: "平均压力水平", unit: "/ 10" },
  { key: "score" as const, label: "平均睡眠评分", unit: "分" },
];

export default function SummaryCards({ averages }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {cards.map((c) => (
        <div
          key={c.key}
          className="rounded-xl bg-slate-700/50 border border-slate-600/50 p-4"
        >
          <p className="text-xs text-slate-400 mb-1">{c.label}</p>
          <p className="text-2xl font-bold">
            {averages[c.key]}
            <span className="text-sm font-normal text-slate-400 ml-1">{c.unit}</span>
          </p>
        </div>
      ))}
    </div>
  );
}
