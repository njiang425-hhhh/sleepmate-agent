"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { CheckinData } from "@/types/checkin";
import { RoutineGenerateResponse } from "@/types/routine";
import { generateRoutine } from "@/lib/routine-api";
import RoutineLoading from "./components/RoutineLoading";
import RoutineEmptyState from "./components/RoutineEmptyState";
import RoutineCard from "./components/RoutineCard";
import SupportiveClarificationCard from "./components/SupportiveClarificationCard";
import SafetyRedirectCard from "./components/SafetyRedirectCard";

export default function RoutinePage() {
  const [checkinData, setCheckinData] = useState<CheckinData | null>(null);
  const [response, setResponse] = useState<RoutineGenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [missingData, setMissingData] = useState(false);
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async (data: CheckinData) => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    setLoading(true);
    setError(null);
    try {
      const result = await generateRoutine(data);
      setResponse(result);
      sessionStorage.removeItem("checkinData");
    } catch (e) {
      setError(e instanceof Error ? e.message : "网络错误");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const raw = sessionStorage.getItem("checkinData");
    if (!raw) {
      setMissingData(true);
      return;
    }
    try {
      const data: CheckinData = JSON.parse(raw);
      setCheckinData(data);
      fetchData(data);
    } catch {
      setMissingData(true);
    }
  }, [fetchData]);

  const handleRetry = () => {
    if (checkinData) {
      fetchedRef.current = false;
      fetchData(checkinData);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white">
      <div className="mx-auto max-w-lg px-4 py-12">
        <h1 className="text-3xl font-bold mb-2">今晚助眠计划</h1>
        <p className="text-slate-400 mb-4">根据你的状态量身定制</p>
        <p className="text-xs text-slate-500 mb-8">本计划仅供放松参考，不替代专业医疗建议。如有持续睡眠问题，请咨询医生。</p>

        {missingData && <RoutineEmptyState />}

        {loading && <RoutineLoading />}

        {error && (
          <div className="space-y-4">
            <div className="rounded-lg bg-red-900/50 border border-red-700 px-4 py-3 text-red-200">
              {error}
            </div>
            <button
              onClick={handleRetry}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-500 transition"
            >
              重试
            </button>
          </div>
        )}

        {response && response.type === "success" && (
          <RoutineCard data={response} />
        )}

        {response && response.type === "supportive_clarification" && (
          <SupportiveClarificationCard data={response} />
        )}

        {response && response.type === "safety_redirect" && (
          <SafetyRedirectCard data={response} />
        )}
      </div>
    </main>
  );
}
