import Link from "next/link";

export default function RoutineEmptyState() {
  return (
    <div className="text-center py-12">
      <p className="text-slate-400 mb-4">还没有睡前数据，请先完成 Check-in</p>
      <Link
        href="/checkin"
        className="inline-block rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white hover:bg-blue-500 transition"
      >
        前往 Check-in
      </Link>
    </div>
  );
}
