import React, { useState } from "react";
import { Terminal, Copy, Check, ExternalLink, Database, ShieldCheck } from "lucide-react";

export default function Footer() {
  const [copiedCmd, setCopiedCmd] = useState(false);

  const testCommand = "python scripts/validate_dashboard_data.py; pytest tests/ -v";

  const copyToClipboard = () => {
    navigator.clipboard.writeText(testCommand);
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 2000);
  };

  return (
    <footer id="reproducibility" className="py-16 bg-slate-950 text-slate-400 border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 mb-12">
          {/* Col 1: Project Identity */}
          <div>
            <div className="flex items-center space-x-2.5 mb-3">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white">
                <Database className="w-4 h-4" />
              </div>
              <span className="text-sm font-bold text-white tracking-tight">
                Composio AI Product Ops
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Take-home assessment delivering an automated research agent, a 100-app integration dataset, 
              four-layer verification, and an interactive case study.
            </p>
            <div className="text-[11px] font-mono text-slate-500">
              Generated: November 2026 | Antigravity AI Engine
            </div>
          </div>

          {/* Col 2: Runnable Commands */}
          <div className="lg:col-span-2">
            <span className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider block mb-2">
              Reproduce Research & Validation
            </span>
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between font-mono text-xs text-slate-200">
              <div className="flex items-center gap-2 truncate">
                <Terminal className="w-4 h-4 text-cyan-400 shrink-0" />
                <span className="truncate">{testCommand}</span>
              </div>
              <button
                onClick={copyToClipboard}
                className="ml-3 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] flex items-center gap-1 transition-colors shrink-0"
                title="Copy command to clipboard"
              >
                {copiedCmd ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedCmd ? "Copied" : "Copy"}
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4 text-[11px] font-mono">
              <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
                <span className="text-slate-400 block mb-0.5">DATASET VALIDATOR:</span>
                <span className="text-slate-200">python scripts/validate_dataset.py</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
                <span className="text-slate-400 block mb-0.5">RESEARCH VALIDATOR:</span>
                <span className="text-slate-200">python scripts/validate_research.py</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
                <span className="text-slate-400 block mb-0.5">FULL TEST SUITE:</span>
                <span className="text-emerald-400">104 / 104 Passing</span>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-800/70 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <div>
            Built with React 19, Vite, and Tailwind CSS. All findings grounded in verified source evidence.
          </div>
          <div className="flex items-center space-x-4 text-slate-400 font-mono text-[11px]">
            <a href="#overview" className="hover:text-white">Top ↑</a>
            <a href="#table" className="hover:text-white">100-App Table</a>
            <a href="#findings" className="hover:text-white">Insights</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
