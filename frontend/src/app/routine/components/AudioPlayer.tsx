"use client";

import { useState, useEffect } from "react";
import { resolveAudioURL } from "@/lib/audio-api";

interface Props {
  audioPath: string;
}

export default function AudioPlayer({ audioPath }: Props) {
  const [src, setSrc] = useState<string | null>(null);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setSrc(resolveAudioURL(audioPath));
    setHasError(false);
  }, [audioPath]);

  if (hasError) {
    return (
      <p className="text-sm text-amber-400">音频加载失败，请检查网络后重试。</p>
    );
  }

  if (!src) return null;

  return (
    <div className="rounded-lg bg-slate-700/50 border border-slate-600 p-4">
      <p className="text-xs text-slate-400 mb-2">AI 生成语音</p>
      <audio
        controls
        preload="none"
        src={src}
        onError={() => setHasError(true)}
        className="w-full"
      >
        您的浏览器不支持音频播放。
      </audio>
    </div>
  );
}
