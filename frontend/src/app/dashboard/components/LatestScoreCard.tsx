interface LatestScore {
  date: string;
  score: number;
  level: string;
  level_label: string;
  breakdown: Record<string, { score: number; max_score: number; label: string }>;
}

interface Props {
  latestScore: LatestScore;
}

const levelColors: Record<string, string> = {
  excellent: "bg-green-500/20 text-green-400 border-green-500/30",
  good: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  fair: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  poor: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  very_poor: "bg-red-500/20 text-red-400 border-red-500/30",
};

export default function LatestScoreCard({ latestScore }: Props) {
  const colorClass = levelColors[latestScore.level] || levelColors.fair;

  return (
    <div className="rounded-xl bg-slate-700/50 border border-slate-600/50 p-6 text-center">
      <p className="text-sm text-slate-400 mb-2">最近睡眠评分</p>
      <p className="text-5xl font-bold mb-2">{latestScore.score}</p>
      <span
        className={`inline-block rounded-full px-3 py-1 text-sm font-medium border ${colorClass}`}
      >
        {latestScore.level_label}
      </span>
      <p className="text-xs text-slate-500 mt-2">{latestScore.date}</p>
      <p className="text-xs text-slate-400 mt-1">
        SleepMate 综合睡眠状态评分（非医学量表，不用于诊断）
      </p>
    </div>
  );
}
