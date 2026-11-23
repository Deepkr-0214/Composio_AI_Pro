import React from "react";
import { TrendingUp, ShieldAlert, Cpu, Layers, Sparkles, AlertCircle } from "lucide-react";

export default function KeyFindings({ insights }) {
  if (!insights || insights.length === 0) return null;

  const iconMap = {
    "INSIGHT-01": TrendingUp,
    "INSIGHT-02": Layers,
    "INSIGHT-03": ShieldAlert,
    "INSIGHT-04": Cpu,
    "INSIGHT-05": Sparkles,
  };

  const badgeColors = {
    "INSIGHT-01": "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
    "INSIGHT-02": "bg-indigo-500/10 text-indigo-300 border-indigo-500/30",
    "INSIGHT-03": "bg-rose-500/10 text-rose-300 border-rose-500/30",
    "INSIGHT-04": "bg-amber-500/10 text-amber-300 border-amber-500/30",
    "INSIGHT-05": "bg-cyan-500/10 text-cyan-300 border-cyan-500/30",
  };

  return (
    <section id="findings" className="py-16 border-b border-slate-800/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
          <div>
            <span className="text-xs font-mono font-semibold text-cyan-400 tracking-wider uppercase">
              Actionable Research Intelligence
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-1">
              Five Evidence-Backed Strategic Insights
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 max-w-lg">
            Empirical patterns extracted across 100 applications to guide Composio toolkit prioritization, 
            authentication infrastructure, and vendor outreach.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {insights.map((ins, idx) => {
            const Icon = iconMap[ins.insight_id] || Sparkles;
            const badgeClass = badgeColors[ins.insight_id] || "bg-cyan-500/10 text-cyan-300 border-cyan-500/30";

            return (
              <div
                key={ins.insight_id}
                className={`p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between ${
                  idx === 0 || idx === 1 ? "md:col-span-1" : ""
                }`}
              >
                <div>
                  {/* Top Badge & Metric */}
                  <div className="flex items-center justify-between mb-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono border ${badgeClass}`}>
                      {ins.insight_id}
                    </span>
                    <Icon className="w-5 h-5 text-slate-400" />
                  </div>

                  {/* Headline */}
                  <h3 className="text-base font-semibold text-white tracking-tight leading-snug">
                    {ins.headline}
                  </h3>

                  {/* Highlight Metric Pill */}
                  <div className="mt-3 inline-flex items-baseline gap-1.5 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800/80">
                    <span className="text-sm font-bold text-cyan-300 font-mono">{ins.metric}</span>
                    <span className="text-[11px] text-slate-400 font-mono">/ {ins.denominator}</span>
                  </div>

                  {/* Detailed Explanation */}
                  <p className="mt-3.5 text-xs sm:text-sm text-slate-300 leading-relaxed">
                    {ins.explanation}
                  </p>

                  {/* Supporting Applications */}
                  {ins.supporting_apps && ins.supporting_apps.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-800/70">
                      <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-1.5">
                        Exemplary Platforms:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {ins.supporting_apps.map((app, aIdx) => (
                          <span
                            key={aIdx}
                            className="px-2 py-0.5 rounded bg-slate-800 text-[11px] text-slate-200 font-mono"
                          >
                            {app}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Stated Limitation */}
                {ins.limitation && (
                  <div className="mt-4 pt-3 border-t border-slate-800/70 flex items-start gap-1.5 text-[11px] text-slate-400">
                    <AlertCircle className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                    <span><strong className="text-slate-300">Boundary:</strong> {ins.limitation}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
