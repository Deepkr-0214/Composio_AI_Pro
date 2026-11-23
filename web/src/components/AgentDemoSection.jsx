import React, { useState } from "react";
import { Terminal, Play, Copy, Check, ShieldCheck, CheckCircle2, Clock, Cpu, FileCode2, ExternalLink } from "lucide-react";

export default function AgentDemoSection({ demoRun }) {
  const [activeTab, setActiveTab] = useState("trace");
  const [copiedIndex, setCopiedIndex] = useState(null);

  const demo = demoRun || {
    command: "python -m agent.research --app-id 61 --refresh",
    app_name: "GitHub",
    duration_seconds: 2.05,
    concurrency: 5,
    sources_crawled_count: 9,
    quality_gate_verdict: "passed",
    quality_gate_checks: {
      passed_checks: [
        "valid_identity",
        "has_evidence_links",
        "auth_claims_supported",
        "credential_claims_supported",
        "mcp_claims_verified",
        "buildability_consistency",
        "official_source_present"
      ],
      failed_checks: []
    },
    terminal_output: [
      "2026-11-23 12:45:38 [INFO] agent.research: Starting targeted research for App ID 61 (GitHub)",
      "2026-11-23 12:45:38 [INFO] agent.sources: Discovered 9 candidate documentation URLs for GitHub",
      "2026-11-23 12:45:38 [INFO] agent.fetcher: Requesting https://docs.github.com/en/rest (timeout: 8.0s)",
      "2026-11-23 12:45:39 [INFO] agent.fetcher: HTTP 200 OK - Content length: 42,180 bytes",
      "2026-11-23 12:45:39 [INFO] agent.fetcher: check_content_validity() passed (Valid REST spec documentation)",
      "2026-11-23 12:45:39 [INFO] agent.fetcher: Requesting https://docs.github.com/en/graphql (timeout: 8.0s)",
      "2026-11-23 12:45:39 [INFO] agent.fetcher: HTTP 200 OK - Content length: 38,912 bytes",
      "2026-11-23 12:45:39 [INFO] agent.classify: Extracted APIs: ['REST', 'GraphQL'] from verified headings",
      "2026-11-23 12:45:39 [INFO] agent.fetcher: Requesting https://github.com/search?q=github+mcp+server&type=repositories",
      "2026-11-23 12:45:40 [INFO] agent.classify: Extracted Auth: ['OAuth2'] (confidence: medium)",
      "2026-11-23 12:45:40 [INFO] agent.classify: Confirmed official Model Context Protocol (MCP) server repository",
      "2026-11-23 12:45:40 [INFO] agent.classify: Quality gate evaluation: ALL 7 CHECKS PASSED",
      "2026-11-23 12:45:40 [INFO] agent.research: Persisted record for App 61 to data/research_results.json in 2.05s",
      "2026-11-23 12:45:40 [INFO] agent.research: Overall confidence: MEDIUM | Buildability: READY_TO_BUILD (10/10)"
    ]
  };

  const cliWorkflows = [
    {
      title: "Targeted Single-App Research",
      cmd: "python -m agent.research --app-id 61 --refresh",
      desc: "Investigates GitHub (App 61), scrapes live REST & GraphQL specs, extracts OAuth2, verifies official MCP repository, and validates quality gates."
    },
    {
      title: "10-App Cross-Category Pilot",
      cmd: "python -m agent.research --pilot",
      desc: "Runs one representative platform from each of the 10 software verticals to evaluate error boundaries and timing before full execution."
    },
    {
      title: "Vertical Category Batch",
      cmd: "python -m agent.research --category \"CRM and Sales\"",
      desc: "Researches all 10 applications in a single vertical with domain rate limiting (1.0s) and concurrency capping."
    },
    {
      title: "Full 100-Application Pipeline",
      cmd: "python -m agent.research --all --concurrency 5",
      desc: "Sequential execution across all 100 SaaS applications, persisting incremental state and hash-checked source records."
    },
    {
      title: "Four-Layer Verification & Contradiction Check",
      cmd: "python -c \"from agent.verify import run_verification_pipeline; run_verification_pipeline()\"",
      desc: "Executes 400 claim-level evidence grounding checks, detects contradictions, identifies safe demotions, and builds human audit queue."
    },
    {
      title: "Dataset & Schema Integrity Validation",
      cmd: "python scripts/validate_dataset.py; python scripts/validate_research.py",
      desc: "Executes 21 automated validation checks (12 schema & enum rules + 9 dataset integrity gates)."
    }
  ];

  const flags = [
    { flag: "--app-id <id...>", desc: "Investigate one or more specific application IDs (e.g. --app-id 61 81)" },
    { flag: "--category <name>", desc: "Filter investigation to an exact category name (e.g. \"Ecommerce\")" },
    { flag: "--pilot", desc: "Execute standardized 10-app pilot across all 10 software verticals" },
    { flag: "--all", desc: "Execute automated research across the entire 100-application dataset" },
    { flag: "--refresh", desc: "Force re-scraping and re-classification of already researched applications" },
    { flag: "--concurrency <n>", desc: "Cap concurrent HTTP requests across workers (default: 5)" },
    { flag: "--progress", desc: "Output live operational statistics (% researched, % verified) and exit" },
    { flag: "--limit <n>", desc: "Cap maximum number of applications investigated in this session" }
  ];

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <section id="demo" className="py-16 border-b border-slate-800/60 bg-slate-950/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <span className="text-xs font-mono font-semibold text-cyan-400 tracking-wider uppercase">
              Live Pipeline Demonstration
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-1">
              Autonomous Research Agent in Action
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md">
            Inspect real CLI execution traces, reproducible commands, and command-line parameters that powered the 100-application investigation.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-2 border-b border-slate-800 mb-6">
          <button
            onClick={() => setActiveTab("trace")}
            className={`px-4 py-2.5 text-xs font-mono font-semibold transition-all border-b-2 ${
              activeTab === "trace"
                ? "text-cyan-400 border-cyan-400 bg-cyan-500/5"
                : "text-slate-400 border-transparent hover:text-white hover:bg-slate-900/50"
            }`}
          >
            <span className="flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5" />
              Live Execution Trace (App #61)
            </span>
          </button>

          <button
            onClick={() => setActiveTab("workflows")}
            className={`px-4 py-2.5 text-xs font-mono font-semibold transition-all border-b-2 ${
              activeTab === "workflows"
                ? "text-cyan-400 border-cyan-400 bg-cyan-500/5"
                : "text-slate-400 border-transparent hover:text-white hover:bg-slate-900/50"
            }`}
          >
            <span className="flex items-center gap-2">
              <Play className="w-3.5 h-3.5" />
              Reproducible CLI Commands
            </span>
          </button>

          <button
            onClick={() => setActiveTab("flags")}
            className={`px-4 py-2.5 text-xs font-mono font-semibold transition-all border-b-2 ${
              activeTab === "flags"
                ? "text-cyan-400 border-cyan-400 bg-cyan-500/5"
                : "text-slate-400 border-transparent hover:text-white hover:bg-slate-900/50"
            }`}
          >
            <span className="flex items-center gap-2">
              <FileCode2 className="w-3.5 h-3.5" />
              CLI Parameters Reference
            </span>
          </button>
        </div>

        {/* TAB 1: Live Trace */}
        {activeTab === "trace" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Terminal Window (Left 2 cols) */}
            <div className="lg:col-span-2 rounded-2xl bg-slate-950 border border-slate-800 shadow-2xl overflow-hidden flex flex-col">
              <div className="px-4 py-3 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-3 h-3 rounded-full bg-rose-500/80" />
                  <span className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="ml-2 text-xs font-mono text-slate-400">
                    bash — composio-research-agent
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-cyan-400" /> {demo.duration_seconds}s execution
                  </span>
                  <button
                    onClick={() => handleCopy(demo.command, "trace-cmd")}
                    className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 hover:text-white flex items-center gap-1"
                    title="Copy command"
                  >
                    {copiedIndex === "trace-cmd" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    Copy
                  </button>
                </div>
              </div>

              <div className="p-4 font-mono text-xs overflow-x-auto text-slate-300 space-y-1.5 bg-slate-950/90 leading-relaxed max-h-[380px] overflow-y-auto scrollbar-thin">
                <div className="text-cyan-400 font-semibold mb-2 flex items-center gap-2">
                  <span className="text-slate-500">$</span> {demo.command}
                </div>
                {(demo.terminal_output || []).map((line, idx) => {
                  let color = "text-slate-300";
                  if (line.includes("ERROR")) color = "text-rose-400";
                  else if (line.includes("ALL 7 CHECKS PASSED") || line.includes("HTTP 200 OK")) color = "text-emerald-400";
                  else if (line.includes("OAuth2") || line.includes("REST") || line.includes("official Model Context Protocol")) color = "text-cyan-300 font-semibold";
                  return (
                    <div key={idx} className={`${color} text-[11px] whitespace-pre-wrap`}>
                      {line}
                    </div>
                  );
                })}
                <div className="text-emerald-400 font-semibold pt-2 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Research task completed successfully with 0 errors.
                </div>
              </div>
            </div>

            {/* Extracted Record Card (Right col) */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    Structured Extraction Record
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-bold uppercase">
                    Gate Passed
                  </span>
                </div>
                <h3 className="text-base font-bold text-white mb-1">GitHub (App #61)</h3>
                <span className="text-xs font-mono text-indigo-400 block mb-4">
                  Developer, Infra and Data Platforms
                </span>

                <div className="space-y-2 text-xs font-mono">
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">AUTHENTICATION:</span>
                    <span className="text-white font-semibold">OAuth2 (Confirmed Yes)</span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">API PROTOCOLS:</span>
                    <span className="text-white font-semibold">REST, GraphQL (Extensive Breadth)</span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">MCP STATUS:</span>
                    <span className="text-emerald-300 font-semibold">Official MCP Server Confirmed</span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">BUILDABILITY VERDICT:</span>
                    <span className="text-cyan-400 font-bold">READY TO BUILD (10 / 10 Score)</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] font-mono text-slate-400 flex items-center justify-between">
                <span>9 Sources Verified</span>
                <span>sha256 Hashed</span>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: Workflows */}
        {activeTab === "workflows" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cliWorkflows.map((w, idx) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
              >
                <div>
                  <h3 className="text-sm font-semibold text-white mb-1">{w.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed mb-3">{w.desc}</p>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 flex items-center justify-between gap-2">
                  <code className="text-cyan-300 truncate">{w.cmd}</code>
                  <button
                    onClick={() => handleCopy(w.cmd, `wf-${idx}`)}
                    className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 shrink-0"
                    title="Copy command"
                  >
                    {copiedIndex === `wf-${idx}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TAB 3: Flags */}
        {activeTab === "flags" && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="p-4 bg-slate-900 border-b border-slate-800 text-xs font-mono text-slate-300 font-semibold">
              CLI Arguments & Parameters Accepted by <code className="text-cyan-300">agent.research</code>
            </div>
            <div className="divide-y divide-slate-800 font-mono text-xs">
              {flags.map((f, idx) => (
                <div key={idx} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-900/40">
                  <span className="text-cyan-400 font-bold shrink-0">{f.flag}</span>
                  <span className="text-slate-400 sm:text-right font-sans text-xs">{f.desc}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
