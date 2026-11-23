import React, { useState } from "react";
import { BarChart3, Check, Filter, Layers, ChevronRight } from "lucide-react";

export default function CategoryComparison({ categories }) {
  if (!categories || Object.keys(categories).length === 0) return null;

  const catList = Object.values(categories);
  const [selectedCat, setSelectedCat] = useState(catList[0]?.category_name || "");

  const activeCategory = categories[selectedCat] || catList[0];

  return (
    <section id="categories" className="py-16 border-b border-slate-800/60 bg-slate-950/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <span className="text-xs font-mono font-semibold text-cyan-400 tracking-wider uppercase">
              Cross-Category Benchmarks
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-1">
              10-Category Integration Comparison
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md">
            Compare developer documentation completeness, average buildability scores, and dominant protocols 
            across all 10 software verticals.
          </p>
        </div>

        {/* Category Pill Selectors */}
        <div className="flex items-center gap-2 overflow-x-auto pb-3 mb-6 scrollbar-thin">
          {catList.map((c) => {
            const isSelected = selectedCat === c.category_name;
            return (
              <button
                key={c.category_name}
                onClick={() => setSelectedCat(c.category_name)}
                className={`whitespace-nowrap px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isSelected
                    ? "bg-cyan-500 text-slate-950 font-semibold shadow-md shadow-cyan-500/20"
                    : "bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-800"
                }`}
              >
                {c.category_name}
              </button>
            );
          })}
        </div>

        {/* Selected Category Highlight Card */}
        {activeCategory && (
          <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 mb-8 shadow-xl">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded text-[11px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                    Category Deep Dive
                  </span>
                  <span className="text-xs text-slate-400 font-mono">10 Assigned Apps</span>
                </div>
                <h3 className="text-xl font-bold text-white mt-1.5">{activeCategory.category_name}</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Dominant Authentication: <strong className="text-slate-200">{activeCategory.dominant_auth}</strong>
                </p>
              </div>

              {/* Stat Pills */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                  <div className="text-[11px] text-slate-400 font-mono">Completeness</div>
                  <div className="text-lg font-bold text-emerald-400">{activeCategory.completeness_rate}</div>
                  <div className="text-[10px] text-slate-500">Quality gate pass/partial</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                  <div className="text-[11px] text-slate-400 font-mono">Buildability Score</div>
                  <div className="text-lg font-bold text-cyan-400">{activeCategory.average_buildability_score} / 10</div>
                  <div className="text-[10px] text-slate-500">Avg across 10 apps</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                  <div className="text-[11px] text-slate-400 font-mono">Confirmed REST / GQL</div>
                  <div className="text-lg font-bold text-indigo-400">
                    {activeCategory.confirmed_rest_count} <span className="text-xs font-normal text-slate-400">REST</span> / {activeCategory.confirmed_graphql_count} <span className="text-xs font-normal text-slate-400">GQL</span>
                  </div>
                  <div className="text-[10px] text-slate-500">Public API surfaces</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                  <div className="text-[11px] text-slate-400 font-mono">Buildable Now</div>
                  <div className="text-lg font-bold text-violet-400">{activeCategory.ready_to_build_count}</div>
                  <div className="text-[10px] text-slate-500">+ {activeCategory.conditional_count} conditional</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Full 10-Category Interactive Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
          <table className="min-w-full divide-y divide-slate-800 text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 font-mono uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-3 text-center">Assigned</th>
                <th className="py-3 px-3 text-center">Gate Passed</th>
                <th className="py-3 px-3 text-center">Partial</th>
                <th className="py-3 px-3 text-center">Needs Review</th>
                <th className="py-3 px-3 text-center">Completeness</th>
                <th className="py-3 px-3 text-center">Avg Build Score</th>
                <th className="py-3 px-3 text-center">REST / GQL</th>
                <th className="py-3 px-3 text-center">Buildable Now</th>
                <th className="py-3 px-4">Dominant Auth</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {catList.map((c) => {
                const isSelected = selectedCat === c.category_name;
                return (
                  <tr
                    key={c.category_name}
                    onClick={() => setSelectedCat(c.category_name)}
                    className={`cursor-pointer transition-colors ${
                      isSelected ? "bg-cyan-500/10 text-white" : "hover:bg-slate-900/70 text-slate-300"
                    }`}
                  >
                    <td className="py-3 px-4 font-medium flex items-center gap-1.5">
                      {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />}
                      {c.category_name}
                    </td>
                    <td className="py-3 px-3 text-center font-mono">{c.assigned_apps}</td>
                    <td className="py-3 px-3 text-center font-mono text-emerald-400">{c.quality_gate_passed}</td>
                    <td className="py-3 px-3 text-center font-mono text-amber-400">{c.quality_gate_partial}</td>
                    <td className="py-3 px-3 text-center font-mono text-rose-400">{c.quality_gate_needs_review}</td>
                    <td className="py-3 px-3 text-center font-mono font-semibold">{c.completeness_rate}</td>
                    <td className="py-3 px-3 text-center font-mono font-bold text-cyan-400">
                      {c.average_buildability_score}
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-slate-400">
                      {c.confirmed_rest_count} / {c.confirmed_graphql_count}
                    </td>
                    <td className="py-3 px-3 text-center font-mono font-semibold text-indigo-300">
                      {c.ready_to_build_count}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400 truncate max-w-[140px]">
                      {c.dominant_auth}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
