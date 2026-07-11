interface Props {
  advice: string[];
}

export default function AdviceList({ advice }: Props) {
  return (
    <div className="rounded-xl bg-slate-700/50 border border-slate-600/50 p-5">
      <p className="text-sm font-medium text-slate-300 mb-3">建议</p>
      <ul className="space-y-2">
        {advice.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
            <span className="mt-1 h-1.5 w-1.5 rounded-full bg-blue-400 shrink-0" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
