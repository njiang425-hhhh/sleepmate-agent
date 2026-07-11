export default function EmptyState() {
  return (
    <div className="rounded-xl bg-slate-700/50 border border-slate-600/50 p-8 text-center">
      <p className="text-lg text-slate-300 mb-2">暂无睡眠记录</p>
      <p className="text-sm text-slate-400">请先填写睡眠日志，即可查看 Dashboard 数据。</p>
    </div>
  );
}
