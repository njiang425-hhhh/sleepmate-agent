export default function RoutineLoading() {
  return (
    <div className="text-center py-12">
      <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-400 border-t-transparent mb-4" />
      <p className="text-slate-400">正在生成你的助眠计划...</p>
    </div>
  );
}
