import React, { useState } from "react";
import { Terminal, Shield, RefreshCw, Cpu, Database, CheckSquare, Layers, Search, ArrowRight, Copy, Check } from "lucide-react";

export default function AgentWorkflow() {
  const [copiedIndex, setCopiedIndex] = useState(null);

  const steps = [
    {
      num: "01",
      title: "Application Registry",
      subtitle: "data/apps.json",
      desc: "Curates 100 benchmark SaaS applications across 10 software verticals with sequential IDs 1 to 100 and strict category assignments.",
      cmd: "python scripts/validate_dataset.py",
      icon: Database,
    },
    {
      num: "02",
      title: "Documentation Discovery",
      subtitle: "agent/sources.py",
      desc: "Resolves canonical developer portals, API reference endpoints, OAuth guides, and MCP registries via known_docs_map and URL generators.",
      cmd: "python -m agent.research --app-id 61",
      icon: Search,
    },
    {
      num: "03",
      title: "Evidence Retrieval",
      subtitle: "agent/fetcher.py",
      desc: "Executes bounded async HTTP scraping (8.0s timeout), respects robots.txt disallows, enforces 1.0s rate limits, and rejects anti-bot trap shells.",
      cmd: "python -m agent.research --category \"CRM and Sales\"",
      icon: Shield,
    },
    {
      num: "04",
      title: "Structured Classification",
      subtitle: "agent/classify.py",
      desc: "Extracts 10 auth types, 10 credential accessibility tiers, 5 API breadth levels, and MCP status using regex and heading hierarchy.",
      cmd: "python -m agent.research --pilot",
      icon: Cpu,
    },
    {
      num: "05",
      title: "Verification Engine",
      subtitle: "agent/verify.py",
      desc: "Executes 4-layer verification checking HTTP status, excerpt containment, multi-domain corroboration, and contradiction detection.",
      cmd: "python -c \"from agent.verify import run_verification_pipeline; run_verification_pipeline()\"",
      icon: CheckSquare,
    },
    {
      num: "06",
      title: "Correction Tracking",
      subtitle: "data/correction_log.json",
      desc: "Applies safe automated demotions (e.g. passed to partial), logs complete provenance with timestamps, and preserves immutable first-pass snapshots.",
      cmd: "python scripts/validate_research.py",
      icon: Layers,
    },
    {
      num: "07",
      title: "Analytics & Scoring",
      subtitle: "scripts/analyze_research.py",
      desc: "Computes 0–100 integration priority scores across 6 weighted dimensions, 10-category benchmark matrix, and 5 opportunity groups.",
      cmd: "python scripts/analyze_research.py",
      icon: RefreshCw,
    },
    {
      num: "08",
      title: "Case Study Dashboard",
      subtitle: "web/ (React 19 + Vite)",
      desc: "Prepares machine-readable JSON data endpoints and renders an interactive recruiter-ready case study with live filters and data exports.",
      cmd: "cd web && npm run build",
      icon: Terminal,
    },
  ];

  const handleCopy = (cmd, idx) => {
    navigator.clipboard.writeText(cmd);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <section id="agent" className="py-16 border-b border-slate-800/60 bg-slate-950/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-4">
          <div>
            <span className="text-xs font-mono font-semibold text-cyan-400 tracking-wider uppercase">
              End-to-End Pipeline Engineering
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-1">
              Automated Research & Verification Sequence
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md">
            The complete 8-stage automated pipeline: from application registration and defensive crawling to verification and dashboard publication.
          </p>
        </div>

        {/* 8-Stage Sequential Workflow Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
          {steps.map((st, i) => {
            const Icon = st.icon;
            return (
              <div
                key={st.num}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                      STAGE {st.num}
                    </span>
                    <Icon className="w-4 h-4 text-slate-400 group-hover:text-cyan-400 transition-colors" />
                  </div>
                  <h3 className="text-sm font-semibold text-white tracking-tight">{st.title}</h3>
                  <span className="text-[10px] font-mono text-indigo-400 block mb-2">{st.subtitle}</span>
                  <p className="text-xs text-slate-400 leading-relaxed mb-4">{st.desc}</p>
                </div>

                <div className="pt-3 border-t border-slate-800/80">
                  <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[10px] text-slate-300 flex items-center justify-between gap-1.5">
                    <span className="truncate text-cyan-300">{st.cmd}</span>
                    <button
                      onClick={() => handleCopy(st.cmd, i)}
                      className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white shrink-0"
                      title="Copy command"
                    >
                      {copiedIndex === i ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Technical Principles Callout */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6 rounded-2xl bg-slate-900/30 border border-slate-800">
          <div>
            <h4 className="text-xs font-mono font-semibold text-indigo-300 uppercase tracking-wider mb-2">
              Defensive Web Crawling
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              Standard HTTP requests strictly honor <code className="text-cyan-300 font-mono">robots.txt</code>. 
              No CAPTCHA solving or IP spoofing is attempted. Blocked portals are preserved as <code className="text-rose-300 font-mono">needs_review</code>.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-mono font-semibold text-indigo-300 uppercase tracking-wider mb-2">
              Immutable Snapshots & Resumability
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              First-pass findings are permanently saved to <code className="text-cyan-300 font-mono">batch1_first_pass.json</code> and <code className="text-cyan-300 font-mono">batch2_first_pass.json</code> before any corrections are applied.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-mono font-semibold text-indigo-300 uppercase tracking-wider mb-2">
              Zero Negative Hallucinations
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              When a developer portal returns HTTP 403 or requires client sign-in, the agent records <code className="text-amber-300 font-mono">unknown</code> rather 
              than hallucinating that the platform lacks an API.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
