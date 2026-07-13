import { SafetyRedirectResponse } from "@/types/routine";

interface Props {
  data: SafetyRedirectResponse;
}

export default function SafetyRedirectCard({ data }: Props) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg bg-red-900/30 border border-red-700/50 p-6">
        <p className="text-slate-200 leading-relaxed">{data.message}</p>
      </div>

      {data.immediate_actions.length > 0 && (
        <div className="rounded-lg bg-slate-700/50 border border-slate-600 p-4">
          <h3 className="text-sm font-medium text-slate-300 mb-3">
            即时行动建议
          </h3>
          <ul className="space-y-2">
            {data.immediate_actions.map((action, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-200">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-red-400" />
                {action}
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.resources.length > 0 && (
        <div className="rounded-lg bg-slate-700/50 border border-slate-600 p-4">
          <h3 className="text-sm font-medium text-slate-300 mb-3">
            求助资源
          </h3>
          <ul className="space-y-2">
            {data.resources.map((r, i) => (
              <li key={i} className="text-sm text-slate-200">
                {r.name}
                {r.phone && <span className="text-slate-400 ml-2">{r.phone}</span>}
                {r.url && (
                  <a href={r.url} className="text-blue-400 ml-2" target="_blank" rel="noopener noreferrer">
                    链接
                  </a>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
