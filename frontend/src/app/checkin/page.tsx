"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import CheckinForm from "./components/CheckinForm";
import CheckinResult from "./components/CheckinResult";

interface CheckinData {
  mood: string;
  energy_level: number;
  stress_level: number;
  caffeine_after_3pm: boolean;
  screen_time_minutes: number;
  available_minutes: number;
  preferred_audio: string;
  notes?: string;
}

interface Analysis {
  sleep_risk_level: string;
  suggestions: string[];
  recommended_activity: string;
  recommended_duration_minutes: number;
}

interface CheckinResponse {
  status: string;
  checkin: CheckinData;
  analysis: Analysis;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function CheckinPage() {
  const router = useRouter();
  const [result, setResult] = useState<CheckinResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (data: CheckinData) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/checkin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        const msg = errData?.detail?.[0]?.msg || "请求失败，请检查输入";
        throw new Error(msg);
      }
      const json: CheckinResponse = await res.json();
      setResult(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : "网络错误");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  const handleGenerateRoutine = () => {
    if (result?.checkin) {
      sessionStorage.setItem("checkinData", JSON.stringify(result.checkin));
      router.push("/routine");
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white">
      <div className="mx-auto max-w-lg px-4 py-12">
        <h1 className="text-3xl font-bold mb-2">睡前 Check-in</h1>
        <p className="text-slate-400 mb-8">记录你的睡前状态，获取个性化建议</p>

        {error && (
          <div className="mb-6 rounded-lg bg-red-900/50 border border-red-700 px-4 py-3 text-red-200">
            {error}
          </div>
        )}

        {result ? (
          <CheckinResult
            analysis={result.analysis}
            onReset={handleReset}
            onGenerateRoutine={handleGenerateRoutine}
          />
        ) : (
          <CheckinForm onSubmit={handleSubmit} loading={loading} />
        )}
      </div>
    </main>
  );
}
