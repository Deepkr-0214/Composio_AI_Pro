import React from "react";
import { KeyRound, Lock, Globe, AlertCircle, Info } from "lucide-react";

export default function AuthAndAccessibility({ summary }) {
  const dist = summary?.distributions || {};
  const authDist = dist.authentication_methods || {};
  const credDist = dist.credential_accessibility || {};
  const breadthDist = dist.api_breadth || {};

  // Maximum value for proportional bar calculation
  const maxAuth = Math.max(...Object.values(authDist), 1);
  const maxCred = Math.max(...Object.values(credDist), 1);

  return (
    <section className="py-16 border-b border-slate-800/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
          <div>
            <span className="text-xs font-mono font-semibold text-cyan-400 tracking-wider uppercase">
              Protocols & Onboarding Friction
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-1">
              Authentication & Credential Accessibility
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md">
            Distribution of authentication protocols, credential self-service tiers, and API breadth 
            across investigated applications.
          </p>
        </div>

        {/* 3-Column Visual Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Card 1: Authentication Methods (Multi-Label) */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <KeyRound className="w-4 h-4 text-cyan-400" />
                  Authentication Methods
                </h3>
                <span className="text-[11px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                  Multi-Label
                </span>
              </div>

              <p className="text-xs text-slate-400 mb-5">
                OAuth 2.0 dominates production SaaS (73.9% of documented flows). Many platforms support both machine-to-machine tokens and user OAuth.
              </p>

              <div className="space-y-3">
                {Object.entries(authDist).map(([method, count]) => {
                  const pct = Math.round((count / maxAuth) * 100);
                  return (
                    <div key={method}>
                      <div className="flex justify-between text-xs font-mono mb-1">
                        <span className="text-slate-300">{method}</span>
                        <span className="text-cyan-400 font-semibold">{count} apps</span>
                      </div>
                      <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800/80">
                        <div
                          className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="mt-6 pt-3 border-t border-slate-800/70 flex items-start gap-1.5 text-[11px] text-slate-400">
              <Info className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
              <span>Multi-label notice: 7 platforms support multiple auth types (e.g. Notion supports OAuth2 + PAT + Bearer).</span>
            </div>
          </div>

          {/* Card 2: Credential Accessibility Tiers */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Lock className="w-4 h-4 text-indigo-400" />
                  Credential Accessibility
                </h3>
                <span className="text-[11px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                  Onboarding Friction
                </span>
              </div>

              <p className="text-xs text-slate-400 mb-5">
                Classifies the onboarding steps required to obtain developer API keys or sandbox test credentials.
              </p>

              <div className="space-y-3">
                {Object.entries(credDist).map(([tier, count]) => {
                  const pct = Math.round((count / maxCred) * 100);
                  const formatTier = tier.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
                  return (
                    <div key={tier}>
                      <div className="flex justify-between text-xs font-mono mb-1">
                        <span className="text-slate-300 truncate max-w-[170px]" title={formatTier}>
                          {formatTier}
                        </span>
                        <span className="text-indigo-400 font-semibold">{count} apps</span>
                      </div>
                      <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800/80">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="mt-6 pt-3 border-t border-slate-800/70 flex items-start gap-1.5 text-[11px] text-slate-400">
              <AlertCircle className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
              <span>Unretrieved or WAF-blocked portals default strictly to &quot;unknown&quot; to avoid negative hallucinations.</span>
            </div>
          </div>

          {/* Card 3: API Breadth & Protocols */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Globe className="w-4 h-4 text-violet-400" />
                  API Breadth & Scope
                </h3>
                <span className="text-[11px] font-mono text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded border border-violet-500/20">
                  Surface Analysis
                </span>
              </div>

              <p className="text-xs text-slate-400 mb-5">
                Evaluates endpoint coverage across entities (extensive = 12+ domains, broad = 7-11, moderate = 4-6).
              </p>

              <div className="space-y-3">
                {Object.entries(breadthDist).map(([breadth, count]) => {
                  const formatBreadth = breadth.charAt(0).toUpperCase() + breadth.slice(1);
                  return (
                    <div key={breadth} className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                      <span className="text-xs font-mono text-slate-300">{formatBreadth}</span>
                      <span className="text-xs font-bold text-violet-300 font-mono">{count} applications</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="mt-6 pt-3 border-t border-slate-800/70 text-[11px] text-slate-400">
              Protocol split: <strong className="text-slate-200">28 REST</strong>, <strong className="text-slate-200">3 GraphQL</strong> (GitHub, Shopify, BigCommerce).
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
