import { RoutineSuccessResponse } from "@/types/routine";
import RoutineSteps from "./RoutineSteps";
import RoutineScript from "./RoutineScript";

interface Props {
  data: RoutineSuccessResponse;
}

export default function RoutineCard({ data }: Props) {
  const { routine, safety_notice, meta } = data;
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

      <div className="rounded-lg bg-slate-700/30 border border-slate-600/50 p-3">
        <p className="text-xs text-slate-400">{safety_notice}</p>
      </div>
    </div>
  );
}
