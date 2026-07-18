"use client";

import { useState } from "react";
import { RoutineSuccessResponse } from "@/types/routine";
import { generateTTS } from "@/lib/audio-api";
import RoutineSteps from "./RoutineSteps";
import RoutineScript from "./RoutineScript";
import AudioPlayer from "./AudioPlayer";

interface Props {
  data: RoutineSuccessResponse;
}

export default function RoutineCard({ data }: Props) {
  const { routine, safety_notice, meta } = data;
  const [audioPath, setAudioPath] = useState<string | null>(null);
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [audioRequested, setAudioRequested] = useState(false);

  const handleGenerateAudio = async () => {
    if (audioLoading || audioRequested) return;
    setAudioLoading(true);
    setAudioRequested(true);
    setAudioError(null);
    try {
      const result = await generateTTS(routine.script);
      setAudioPath(result.audio_path);
    } catch {
      setAudioError("音频生成失败，文字脚本仍可使用");
    } finally {
      setAudioLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-lg bg-blue-900/30 border border-blue-700/50 p-4">
        <h2 className="text-xl font-bold text-white mb-1">{routine.title}</h2>
        <p className="text-sm text-blue-300">{routine.strategy}</p>
        <div className="flex gap-4 mt-2 text-xs text-slate-400">
          <span>时长: {routine.duration_minutes} 分钟</span>
          <span>
            历史数据: {meta.history_available ? `${meta.history_record_count} 天` : "无"}
          </span>
          <span>模式: {meta.generation_mode}</span>
        </div>
      </div>

      <RoutineSteps steps={routine.steps} />
      <RoutineScript script={routine.script} />

      {!audioPath && !audioLoading && !audioRequested && (
        <button
          type="button"
          onClick={handleGenerateAudio}
          className="w-full rounded-lg bg-purple-600 px-4 py-3 text-sm font-medium text-white hover:bg-purple-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          生成语音引导
        </button>
      )}

      {audioLoading && (
        <div className="rounded-lg bg-slate-700/50 border border-slate-600 p-4 text-center">
          <p className="text-sm text-slate-300">正在生成语音...</p>
        </div>
      )}

      {audioPath && <AudioPlayer audioPath={audioPath} />}

      {audioError && (
        <p className="text-sm text-amber-400">{audioError}</p>
      )}

      <div className="rounded-lg bg-slate-700/30 border border-slate-600/50 p-3">
        <p className="text-xs text-slate-400">{safety_notice}</p>
      </div>
    </div>
  );
}
