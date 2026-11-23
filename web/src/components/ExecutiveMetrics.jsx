import React from "react";
import { Database, CheckCircle2, AlertCircle, KeyRound, Cpu, Layers } from "lucide-react";

export default function ExecutiveMetrics({ summary }) {
  const kpis = summary?.kpis || {};

  const cards = [
    {
      title: "Applications Researched",
      value: `${kpis.total_researched_apps || 100}`,
      sub: "10 Categories (10 apps each)",
      icon: Database,
      accent: "from-cyan-500/20 to-blue-500/10 text-cyan-400 border-cyan-500/30",
      tooltip: "100 benchmark applications investigated across 10 software verticals (IDs 1–100 strictly sequential).",
    },
    {
      title: "Evidence-Backed Platforms",
      value: kpis.evidence_backed_rate || "61.0%",
      sub: `${kpis.evidence_backed_apps || 61} of 100 with verified docs`,
      icon: CheckCircle2,
      accent: "from-emerald-500/20 to-teal-500/10 text-emerald-400 border-emerald-500/30",
      tooltip: "61 platforms with >=1 verified HTTP 200 documentation citations and atomic excerpts.",
    },
    {
      title: "Self-Serve Ready Toolkits",
      value: `${kpis.ready_to_build_count || 11}`,
      sub: "+ 25 conditionally feasible platforms",
      icon: Layers,
      accent: "from-indigo-500/20 to-violet-500/10 text-indigo-400 border-indigo-500/30",
      tooltip: "Immediate self-serve developer onboarding, documented REST/GraphQL APIs, and zero gating blockers.",
    },
    {
      title: "Dominant SaaS Authentication",
      value: "73.9%",
      sub: "OAuth 2.0 (17 of 23 documented)",
      icon: KeyRound,
      accent: "from-purple-500/20 to-pink-500/10 text-purple-400 border-purple-500/30",
      tooltip: "17 of 23 documented auth flows require OAuth 2.0 PKCE, demonstrating Composio's automated token lifecycle value.",
    },
    {
      title: "Confirmed MCP Adoption",
      value: "1.0%",
      sub: "92% Greenfield Opportunity",
      icon: Cpu,
      accent: "from-amber-500/20 to-orange-500/10 text-amber-400 border-amber-500/30",
      tooltip: "GitHub is the only verified official MCP server; 92% of target SaaS platforms represent prime Composio territory.",
    },
    {
      title: "Vendor Outreach Queue",
      value: `${kpis.quality_gate_needs_review || 39}%`,
      sub: "39 apps require partner access",
      icon: AlertCircle,
      accent: "from-rose-500/20 to-red-500/10 text-rose-400 border-rose-500/30",
      tooltip: "Portals protected by Cloudflare bot challenge walls (Salesforce) or private client logins (DealCloud).",
    },
  ];

  return (
    <section className="py-10 border-b border-slate-800/60 bg-slate-950/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {cards.map((c, i) => {
            const Icon = c.icon;
            return (
              <div
                key={i}
                title={c.tooltip}
                tabIndex={0}
                aria-label={`${c.title}: ${c.value}, ${c.sub}`}
                className={`p-4 rounded-xl bg-slate-900/60 border ${c.accent.split(" ").slice(-1)[0]} hover:bg-slate-900/90 transition-all group focus-visible:ring-2 focus-visible:ring-cyan-400`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-400">{c.title}</span>
                  <Icon className="w-4 h-4 opacity-70 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="mt-2.5">
                  <div className="text-2xl font-bold text-white tracking-tight font-mono">{c.value}</div>
                  <div className="text-[11px] font-mono text-slate-400 mt-0.5 truncate">{c.sub}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
