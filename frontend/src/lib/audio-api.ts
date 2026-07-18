const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function generateTTS(
  scriptText: string,
): Promise<{ audio_path: string; cached: boolean }> {
  const res = await fetch(`${API_BASE}/api/v1/audio/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script_text: scriptText }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => null);
    const msg = errData?.detail || `语音生成失败 (${res.status})`;
    throw new Error(typeof msg === "string" ? msg : "语音生成失败");
  }

  return res.json();
}

export function resolveAudioURL(audioPath: string): string {
  try {
    return new URL(audioPath, API_BASE).toString();
  } catch {
    return `${API_BASE}${audioPath}`;
  }
}
