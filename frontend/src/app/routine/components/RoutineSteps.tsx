import { RoutineStep } from "@/types/routine";

interface Props {
  steps: RoutineStep[];
}

export default function RoutineSteps({ steps }: Props) {
  return (
    <div className="rounded-lg bg-slate-700/50 border border-slate-600 p-4">
      <h3 className="text-sm font-medium text-slate-300 mb-3">步骤</h3>
      <ol className="space-y-4">
        {steps.map((step) => (
          <li key={step.order} className="flex gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
              {step.order}
            </span>
            <div className="min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="font-medium text-white text-sm">
                  {step.action}
                </span>
                <span className="text-xs text-slate-400">
                  {Math.round(step.duration_seconds / 60)} 分钟
                </span>
              </div>
              <p className="text-sm text-slate-300 mt-1">{step.instruction}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
