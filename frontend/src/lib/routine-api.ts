import { CheckinData } from "@/types/checkin";
import { RoutineGenerateResponse } from "@/types/routine";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function generateRoutine(
  checkin: CheckinData,
  historyDays: number = 7,
): Promise<RoutineGenerateResponse> {
  const res = await fetch(`${API_BASE}/api/v1/routine/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ checkin, history_days: historyDays }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => null);
    const msg = errData?.detail || `请求失败 (${res.status})`;
    throw new Error(typeof msg === "string" ? msg : "请求失败");
  }

  return res.json();
}
