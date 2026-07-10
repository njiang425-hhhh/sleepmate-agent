"use client";

import { useState, FormEvent } from "react";

interface FormData {
  mood: string;
  energy_level: number;
  stress_level: number;
  caffeine_after_3pm: boolean;
  screen_time_minutes: number;
  available_minutes: number;
  preferred_audio: string;
  notes: string;
}

interface Props {
  onSubmit: (data: Omit<FormData, "notes"> & { notes?: string }) => void;
  loading: boolean;
}

const MOODS = [
  { value: "calm", label: "平静" },
  { value: "relaxed", label: "放松" },
  { value: "anxious", label: "焦虑" },
  { value: "excited", label: "兴奋" },
  { value: "tired", label: "疲惫" },
  { value: "stressed", label: "压力大" },
] as const;

const AUDIOS = [
  { value: "none", label: "无" },
  { value: "rain", label: "雨声" },
  { value: "ocean", label: "海浪" },
  { value: "white_noise", label: "白噪音" },
  { value: "forest", label: "森林" },
  { value: "piano", label: "钢琴" },
] as const;

const TIMES = [5, 10, 15, 20] as const;

export default function CheckinForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<FormData>({
    mood: "calm",
    energy_level: 5,
    stress_level: 5,
    caffeine_after_3pm: false,
    screen_time_minutes: 30,
    available_minutes: 10,
    preferred_audio: "rain",
    notes: "",
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const payload = { ...form };
    if (!payload.notes) {
      const { notes, ...rest } = payload;
      onSubmit(rest);
    } else {
      onSubmit(payload);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">当前心情</label>
        <div className="grid grid-cols-3 gap-2">
          {MOODS.map((m) => (
            <button
              key={m.value}
              type="button"
              onClick={() => setForm({ ...form, mood: m.value })}
              className={`rounded-lg px-3 py-2 text-sm transition ${
                form.mood === m.value
                  ? "bg-blue-600 text-white"
                  : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          精力水平: {form.energy_level}
        </label>
        <input
          type="range"
          min={1}
          max={10}
          value={form.energy_level}
          onChange={(e) => setForm({ ...form, energy_level: Number(e.target.value) })}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-slate-500">
          <span>低</span>
          <span>高</span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          压力水平: {form.stress_level}
        </label>
        <input
          type="range"
          min={1}
          max={10}
          value={form.stress_level}
          onChange={(e) => setForm({ ...form, stress_level: Number(e.target.value) })}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-slate-500">
          <span>低</span>
          <span>高</span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-300">下午 3 点后摄入咖啡因</label>
        <button
          type="button"
          onClick={() => setForm({ ...form, caffeine_after_3pm: !form.caffeine_after_3pm })}
          className={`relative h-6 w-11 rounded-full transition ${
            form.caffeine_after_3pm ? "bg-blue-600" : "bg-slate-600"
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition ${
              form.caffeine_after_3pm ? "translate-x-5" : ""
            }`}
          />
        </button>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          今日屏幕时间（分钟）: {form.screen_time_minutes}
        </label>
        <input
          type="range"
          min={0}
          max={300}
          step={10}
          value={form.screen_time_minutes}
          onChange={(e) => setForm({ ...form, screen_time_minutes: Number(e.target.value) })}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-slate-500">
          <span>0</span>
          <span>300</span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">可用放松时间</label>
        <div className="grid grid-cols-4 gap-2">
          {TIMES.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setForm({ ...form, available_minutes: t })}
              className={`rounded-lg px-3 py-2 text-sm transition ${
                form.available_minutes === t
                  ? "bg-blue-600 text-white"
                  : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}
            >
              {t}分钟
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">偏好音频</label>
        <div className="grid grid-cols-3 gap-2">
          {AUDIOS.map((a) => (
            <button
              key={a.value}
              type="button"
              onClick={() => setForm({ ...form, preferred_audio: a.value })}
              className={`rounded-lg px-3 py-2 text-sm transition ${
                form.preferred_audio === a.value
                  ? "bg-blue-600 text-white"
                  : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}
            >
              {a.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">备注（可选）</label>
        <textarea
          value={form.notes}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
          className="w-full rounded-lg bg-slate-700 border border-slate-600 px-3 py-2 text-sm text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none"
          rows={3}
          placeholder="今天有什么想说的..."
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition"
      >
        {loading ? "分析中..." : "提交"}
      </button>
    </form>
  );
}
