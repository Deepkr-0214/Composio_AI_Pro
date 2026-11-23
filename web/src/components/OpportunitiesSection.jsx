import React, { useState } from "react";
import { Zap, Handshake, ExternalLink, ArrowRight, ShieldCheck, AlertCircle, HelpCircle, Layers } from "lucide-react";

export default function OpportunitiesSection({ opportunities }) {
  const [activeTab, setActiveTab] = useState("quick_wins");
  const top10 = opportunities?.top_10_opportunities || [];
  const outreach = opportunities?.vendor_outreach_candidates || [];

  const conditionalExamples = [
    { name: "Stripe", score: 71, category: "Finance and Fintech", reason: "Broad REST API with instant API keys, conditional on test vs live merchant account provisioning.", blocker: "KYC/business verification for live payment processing." },
    { name: "Snowflake", score: 71, category: "Developer, Infra & Data", reason: "SQL REST API with KeyPair/OAuth2, conditional on cloud data warehouse compute warehouse active status.", blocker: "Warehouse compute credit consumption." },
    { name: "Supabase", score: 68, category: "Developer, Infra & Data", reason: "PostgREST & GraphQL endpoints with API Key/JWT, conditional on project-level schema deployment.", blocker: "Database migration/schema dependencies." },
    { name: "Twilio", score: 66, category: "Communications & Messaging", reason: "REST API with Account SID/Auth Token, conditional on carrier registration & phone number provisioning.", blocker: "A2P 10DLC campaign registration for SMS." }
  ];

  const investigationExamples = [
    { name: "Salesforce", category: "CRM and Sales", reason: "Protected by Cloudflare Edge WAF (HTTP 403 bot challenge).", blocker: "Edge challenge wall blocking automated HTTP scrapers." },
    { name: "DealCloud", category: "CRM and Sales", reason: "Enterprise client portal behind Intapp SSO authentication.", blocker: "Private client credentials required to access documentation." },
    { name: "PitchBook", category: "Finance and Fintech", reason: "Commercial financial intelligence portal requiring enterprise data subscription.", blocker: "Sales engagement and enterprise licensing." },
    { name: "Meta Ads", category: "Marketing, Ads & Social", reason: "Marketing API requires Business Verification and App Review.", blocker: "App Review submission and developer verification." }
  ];

  return (
    <section id="opportunities" className="py-16 border-b border-slate-800/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <span className="text-xs font-mono font-semibold text-cyan-400 tracking-wider uppercase">
              Actionable Product Operations Strategy
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-1">
              Integration Opportunities & Roadmap Prioritization
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md">
            Empirically segmented recommendations: from immediate self-serve toolkits to commercial vendor partnerships.
          </p>
        </div>

        {/* Heuristic Disclaimer Banner */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 mb-8 flex items-start gap-3">
          <HelpCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <p className="text-xs text-slate-300 leading-relaxed">
            <strong className="text-white">Methodology Note:</strong> Priority scores (0–100) are explainable heuristics 
            evaluating documented API capability, credential self-serve accessibility, and gating friction. 
            They do not represent commercial market demand or measured engineering hours.
          </p>
        </div>

        {/* Group Selector Tabs */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 mb-8 pb-1">
          <button
            onClick={() => setActiveTab("quick_wins")}
            className={`px-3.5 py-2 rounded-lg text-xs font-mono font-semibold transition-all ${
              activeTab === "quick_wins"
                ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                : "text-slate-400 hover:text-white hover:bg-slate-900"
            }`}
          >
            Group A: Quick Wins (6 Apps)
          </button>
          <button
            onClick={() => setActiveTab("conditional")}
            className={`px-3.5 py-2 rounded-lg text-xs font-mono font-semibold transition-all ${
              activeTab === "conditional"
                ? "bg-indigo-500/10 text-indigo-300 border border-indigo-500/30"
                : "text-slate-400 hover:text-white hover:bg-slate-900"
            }`}
          >
            Group B: Conditional (30 Apps)
          </button>
          <button
            onClick={() => setActiveTab("outreach")}
            className={`px-3.5 py-2 rounded-lg text-xs font-mono font-semibold transition-all ${
              activeTab === "outreach"
                ? "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                : "text-slate-400 hover:text-white hover:bg-slate-900"
            }`}
          >
            Group C: Outreach Required (9 Apps)
          </button>
          <button
            onClick={() => setActiveTab("investigation")}
            className={`px-3.5 py-2 rounded-lg text-xs font-mono font-semibold transition-all ${
              activeTab === "investigation"
                ? "bg-rose-500/10 text-rose-300 border border-rose-500/30"
                : "text-slate-400 hover:text-white hover:bg-slate-900"
            }`}
          >
            Group D: Further Investigation (52 Apps)
          </button>
        </div>

        {/* TAB 1: Group A Quick Wins */}
        {activeTab === "quick_wins" && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-emerald-400" />
              <h3 className="text-base font-bold text-white">Group A: Immediate Quick-Win Integrations</h3>
            </div>
            <p className="text-xs text-slate-400 mb-6">
              Platforms with public REST/GraphQL APIs, verified authentication, passed quality gates, and self-serve onboarding.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {top10.slice(0, 6).map((app, idx) => (
                <div
                  key={app.app_id}
                  className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-white flex items-center gap-1.5">
                        <span className="text-cyan-400 font-mono">#{idx + 1}</span> {app.app_name}
                      </span>
                      <span className="text-xs font-mono font-bold text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                        Score: {app.priority_score}
                      </span>
                    </div>

                    <span className="text-[11px] font-mono text-slate-400 block mb-2">{app.category}</span>
                    <p className="text-xs text-slate-300 leading-relaxed mb-3">{app.main_reason}</p>
                  </div>

                  <div className="pt-3 border-t border-slate-800/70 text-[11px] font-mono text-slate-400 flex items-center justify-between">
                    <span><strong className="text-slate-300">Auth:</strong> {app.auth_methods?.join(", ") || "Self-serve token"}</span>
                    <span className="text-emerald-400 font-semibold">Ready to Build</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 2: Group B Conditional */}
        {activeTab === "conditional" && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Layers className="w-4 h-4 text-indigo-400" />
              <h3 className="text-base font-bold text-white">Group B: Conditional Feasibility Integrations</h3>
            </div>
            <p className="text-xs text-slate-400 mb-6">
              Strong API capabilities with secondary account prerequisites (e.g. merchant onboarding, carrier approval, or compute credits).
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {conditionalExamples.map((app, idx) => (
                <div
                  key={idx}
                  className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-white">{app.name}</span>
                      <span className="text-xs font-mono text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        Score: {app.score}
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-400 block mb-2">{app.category}</span>
                    <p className="text-xs text-slate-300 leading-relaxed mb-3">{app.reason}</p>
                  </div>

                  <div className="pt-3 border-t border-slate-800/70 text-[11px] font-mono text-amber-300">
                    <span className="text-slate-400 block text-[10px]">CONDITION / BLOCKER:</span>
                    {app.blocker}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: Group C Outreach */}
        {activeTab === "outreach" && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Handshake className="w-4 h-4 text-amber-400" />
              <h3 className="text-base font-bold text-white">Group C: High-Priority Vendor Outreach Candidates</h3>
            </div>
            <p className="text-xs text-slate-400 mb-6">
              High-value enterprise platforms requiring commercial partner agreements, App Review certification, or private Developer Orgs.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {outreach.map((app) => (
                <div
                  key={app.app_id}
                  className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-white">{app.app_name}</span>
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">
                        App #{app.app_id}
                      </span>
                    </div>

                    <span className="text-[10px] font-mono text-indigo-400 block mb-2">{app.category}</span>

                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 text-[11px] text-slate-300 mb-3">
                      <span className="text-[10px] font-mono text-rose-400 block mb-0.5">RESTRICTION:</span>
                      {app.confirmed_access_restriction}
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed mb-3">
                      <strong className="text-slate-200">Required Step:</strong> {app.required_approval_or_commercial_step}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-slate-800/70 text-[10px] font-mono text-slate-400">
                    {app.suggested_action}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: Group D Investigation */}
        {activeTab === "investigation" && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              <h3 className="text-base font-bold text-white">Group D: Further Investigation Candidates</h3>
            </div>
            <p className="text-xs text-slate-400 mb-6">
              Platforms where automated HTTP discovery encountered Cloudflare edge challenge walls or private SSO gates without public documentation.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {investigationExamples.map((app, idx) => (
                <div
                  key={idx}
                  className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-white">{app.name}</span>
                      <span className="text-[10px] font-mono text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
                        Needs Review
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-400 block mb-2">{app.category}</span>
                    <p className="text-xs text-slate-300 leading-relaxed mb-3">{app.reason}</p>
                  </div>

                  <div className="pt-3 border-t border-slate-800/70 text-[11px] font-mono text-slate-400">
                    <span className="text-slate-500 block text-[10px]">SCRAPING BOUNDARY:</span>
                    {app.blocker}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
