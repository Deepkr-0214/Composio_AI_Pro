import React from "react";
import { Download, FileText, Database, ShieldCheck, CheckSquare, Layers } from "lucide-react";

export default function DataExportSection() {
  const exports = [
    {
      title: "100-App Research Dataset",
      filename: "research_results.json",
      href: "./downloads/research_results.json",
      format: "JSON",
      size: "~112 KB",
      count: "100 Applications",
      desc: "Complete empirical research output including auth methods, API surfaces, MCP statuses, buildability scores, and claim-level evidence links."
    },
    {
      title: "Tabular Research Export",
      filename: "research_results.csv",
      href: "./downloads/research_results.csv",
      format: "CSV",
      size: "~28 KB",
      count: "100 Rows",
      desc: "Tabular representation with quality gate verdicts, credential tiers, API breadth, priority scores, and primary blocker classifications."
    },
    {
      title: "10-Category Benchmark Matrix",
      filename: "category_summary.json",
      href: "./downloads/category_summary.json",
      format: "JSON",
      size: "~12 KB",
      count: "10 Categories",
      desc: "Aggregated distributions, completeness percentages, average buildability scores, and auth protocol frequencies across all 10 verticals."
    },
    {
      title: "Claim Verification Dataset",
      filename: "verification_results.json",
      href: "./downloads/verification_results.json",
      format: "JSON",
      size: "~98 KB",
      count: "400 Claims",
      desc: "Four-layer verification results evaluating primary evidence grounding, contradiction checks, and source availability across 100 platforms."
    },
    {
      title: "20-App Human Audit Sample",
      filename: "audit_sample.json",
      href: "./downloads/audit_sample.json",
      format: "JSON",
      size: "~18 KB",
      count: "20 Applications",
      desc: "Stratified random sample (deterministic seed: 20261123, 2 per category) prepared for ground-truth human accuracy comparison."
    },
    {
      title: "Safe Correction Audit Trail",
      filename: "correction_log.json",
      href: "./downloads/correction_log.json",
      format: "JSON",
      size: "~6 KB",
      count: "3 Real Corrections",
      desc: "Full provenance log of automated quality gate demotions (Apify, BigCommerce, Firecrawl) with original values and trigger rationale."
    }
  ];

  return (
    <section id="export" className="py-16 border-b border-slate-800/60 bg-slate-950/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
          <div>
            <span className="text-xs font-mono font-semibold text-cyan-400 tracking-wider uppercase">
              Open Data & Reproducibility
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-1">
              Export Research Datasets & Audit Logs
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md">
            Download machine-readable JSON and tabular CSV datasets for independent verification, analytics, or ingestion into Composio.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {exports.map((item, idx) => (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                    {item.format}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    {item.size} • {item.count}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white mb-1">{item.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">{item.desc}</p>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                <span className="font-mono text-[11px] text-slate-400 truncate max-w-[160px]">
                  {item.filename}
                </span>
                <a
                  href={item.href}
                  download={item.filename}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
