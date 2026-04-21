"use client";
import { BarChart3, TrendingUp, Clock, Zap } from "lucide-react";

const stats = [
  { label: "Total tasks", value: "—", change: "", icon: BarChart3, color: "text-brand-500" },
  { label: "Avg quality score", value: "—", change: "", icon: TrendingUp, color: "text-emerald-500" },
  { label: "Avg response time", value: "—", change: "", icon: Clock, color: "text-amber-500" },
  { label: "API cost (est.)", value: "—", change: "", icon: Zap, color: "text-violet-500" },
];

export default function AnalyticsPage() {
  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-900">Analytics</h1>
        <p className="text-sm text-zinc-500 mt-1">Track agent performance, usage, and ROI</p>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-surface-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-zinc-400 uppercase tracking-wide font-medium">{s.label}</span>
              <s.icon className={`w-4 h-4 ${s.color}`} />
            </div>
            <div className="text-2xl font-semibold text-zinc-900">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-surface-200 p-6">
        <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wide mb-4">Usage over time</h2>
        <div className="h-64 flex items-center justify-center text-zinc-300 text-sm">
          Charts will populate once you start running agents and the analytics tracker is active (Phase 4)
        </div>
      </div>
    </div>
  );
}
