interface ScoreBreakdownItem {
  score: number;
  max_score: number;
  label: string;
}

interface Props {
  breakdown: Record<string, ScoreBreakdownItem>;
}

const order = ["latency", "quality", "awakenings", "stress", "screen"];

export default function ScoreBreakdown({ breakdown }: Props) {
  return (
    <div className="rounded-xl bg-slate-700/50 border border-slate-600/50 p-5">
      <p className="text-sm font-medium text-slate-300 mb-4">评分明细</p>
      <div className="space-y-3">
        {order.map((key) => {
          const item = breakdown[key];
          if (!item) return null;
          const pct = (item.score / item.max_score) * 100;
          return (
            <div key={key}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">{item.label}</span>
                <span className="text-slate-300">
                  {item.score} / {item.max_score}
                </span>
              </div>
              <div className="h-2 rounded-full bg-slate-600 overflow-hidden">
                <div
                  className="h-full rounded-full bg-blue-500 transition-all"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
