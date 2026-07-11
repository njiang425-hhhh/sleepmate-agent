"use client";

import { useState, useEffect } from "react";
import SummaryCards from "./components/SummaryCards";
import LatestScoreCard from "./components/LatestScoreCard";
import ScoreBreakdown from "./components/ScoreBreakdown";
import AdviceList from "./components/AdviceList";
import EmptyState from "./components/EmptyState";

interface ScoreBreakdownItem {
  score: number;
  max_score: number;
  label: string;
}

interface LatestScore {
  date: string;
  score: number;
  level: string;
  level_label: string;
  breakdown: Record<string, ScoreBreakdownItem>;
}

interface DashboardAverages {
  sleep_latency_minutes: number;
  awakenings: number;
  sleep_quality: number;
  stress_level: number;
  screen_time_minutes: number;
  score: number;
}

interface DashboardResponse {
  days: number;
  record_count: number;
  averages: DashboardAverages | null;
  latest_score: LatestScore | null;
  advice: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/dashboard/summary?days=7`)
      .then((res) => {
        if (!res.ok) throw new Error("加载失败");
        return res.json();
      })
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "网络错误"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <p className="text-slate-400 text-center">加载中...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white">
        <div className="mx-auto max-w-2xl px-4 py-12">
          <div className="rounded-lg bg-red-900/50 border border-red-700 px-4 py-3 text-red-200">
            {error}
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white">
      <div className="mx-auto max-w-2xl px-4 py-12">
        <h1 className="text-3xl font-bold mb-2">睡眠 Dashboard</h1>
        <p className="text-slate-400 mb-8">最近 7 天睡眠数据概览</p>

        {data && data.record_count === 0 ? (
          <EmptyState />
        ) : data ? (
          <div className="space-y-6">
            {data.averages && <SummaryCards averages={data.averages} />}
            {data.latest_score && <LatestScoreCard latestScore={data.latest_score} />}
            {data.latest_score && (
              <ScoreBreakdown breakdown={data.latest_score.breakdown} />
            )}
            {data.advice.length > 0 && <AdviceList advice={data.advice} />}
          </div>
        ) : null}
      </div>
    </main>
  );
}
