interface Props {
  script: string;
}

export default function RoutineScript({ script }: Props) {
  return (
    <div className="rounded-lg bg-slate-700/50 border border-slate-600 p-4">
      <h3 className="text-sm font-medium text-slate-300 mb-3">引导脚本</h3>
      <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-line">
        {script}
      </p>
    </div>
  );
}
