import React from "react";
import { CheckCircle2, AlertTriangle, ShieldX, HelpCircle, Layers, ArrowUpRight } from "lucide-react";

export default function BuildabilityAnalysis({ summary }) {
  const dist = summary?.distributions || {};
  const verdicts = dist.buildability_verdicts || {};

  const verdictCards = [
    {
      key: "ready_to_build",
      title: "Ready to Build",
      count: verdicts.ready_to_build || 11,
      badge: "Immediate Self-Serve",
      badgeColor: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
      description: "Publicly documented REST/GraphQL APIs, verified auth, free or instant self-serve tokens, zero gating blockers.",
      examples: ["GitHub", "Netlify", "Close", "Asana", "WooCommerce", "Devin"],
    },
    {
      key: "feasible",
      title: "Feasible (Conditional)",
      count: verdicts.feasible || 25,
      badge: "Manageable Caveats",
      badgeColor: "bg-indigo-500/10 text-indigo-300 border-indigo-500/30",
      description: "Technically mature APIs available; requires handling standard pagination, per-user rate limits, or OAuth scopes.",
      examples: ["Shopify", "Stripe", "Snowflake", "Supabase", "Twilio", "Zendesk"],
    },
    {
      key: "needs_investigation",
      title: "Needs Investigation",
      count: verdicts.needs_investigation || 60,
      badge: "WAF or Gated Portals",
      badgeColor: "bg-amber-500/10 text-amber-300 border-amber-500/30",
      description: "Documentation is protected by Cloudflare bot walls (Salesforce), unhosted portals, or private enterprise logins.",
      examples: ["Salesforce", "DealCloud", "PitchBook", "Meta Ads", "Discord"],
    },
    {
      key: "significant_barriers",
      title: "Significant Barriers",
      count: verdicts.significant_barriers || 4,
      badge: "Commercial Gating",
      badgeColor: "bg-rose-500/10 text-rose-300 border-rose-500/30",
      description: "Requires certified ecosystem partner approval, custom NDA/MSA contracts, or annual enterprise subscriptions.",
      examples: ["DealCloud", "PitchBook", "Help Scout", "systeme.io"],
    },
  ];

  return (
    <section className="py-16 border-b border-slate-800/60 bg-slate-950/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
          <div>
            <span className="text-xs font-mono font-semibold text-cyan-400 tracking-wider uppercase">
              Toolkit Implementation Strategy
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-1">
              Integration Buildability & Primary Blockers
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md">
            Classification of all 100 applications according to Composio toolkit development feasibility.
          </p>
        </div>

        {/* 4 Verdict Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          {verdictCards.map((v) => (
            <div
              key={v.key}
              className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono border ${v.badgeColor}`}>
                    {v.badge}
                  </span>
                  <span className="text-2xl font-bold text-white font-mono">{v.count}</span>
                </div>

                <h3 className="text-base font-semibold text-white tracking-tight">{v.title}</h3>
                <p className="mt-2 text-xs text-slate-300 leading-relaxed">{v.description}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/70">
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
                  Exemplary Platforms:
                </span>
                <div className="flex flex-wrap gap-1">
                  {v.examples.map((ex, i) => (
                    <span key={i} className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-300">
                      {ex}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Blocker Analysis Explanatory Box */}
        <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800">
          <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Top 4 Integration Blockers Identified Across the Dataset
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs text-slate-300">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
              <span className="font-semibold text-white block mb-1">1. Cloudflare Edge WAF (39 apps)</span>
              Bot challenge walls return HTTP 403 on standard automated web requests (e.g. Salesforce, Discord).
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
              <span className="font-semibold text-white block mb-1">2. Private Enterprise Logins</span>
              Portals requiring active client tenant logins or Intapp credentials to view API specs (DealCloud).
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
              <span className="font-semibold text-white block mb-1">3. Partner Program Gates</span>
              Accounting & ads platforms requiring business verification and app approval (Meta Ads, QuickBooks, Xero).
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
              <span className="font-semibold text-white block mb-1">4. Nonstandard / Local CLI</span>
              Tools operating as local CLI binaries rather than cloud SaaS REST APIs (Sherlock, Mermaid CLI).
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
