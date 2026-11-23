import React from "react";
import { ArrowDown, Database, ShieldCheck, Cpu, AlertTriangle, BookOpen, Layers } from "lucide-react";

export default function Hero({ summary }) {
  const kpis = summary?.kpis || {};

  return (
    <section id="overview" className="relative pt-12 pb-16 overflow-hidden border-b border-slate-800/60">
      {/* Background radial gradient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-96 bg-gradient-to-b from-indigo-900/20 via-cyan-900/10 to-transparent blur-3xl pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top Tag Badges */}
        <div className="flex flex-wrap items-center gap-2 mb-6">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            Composio AI Product Ops Assessment
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            100 Target Applications • 10 Categories
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            61% Evidence-Backed • Atomic Excerpts
          </span>
        </div>

        {/* Primary Headline */}
        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-[1.15] max-w-5xl">
          Mapping the Integration Landscape{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-indigo-300 to-violet-400">
            Across 100 Applications
          </span>
        </h1>

        {/* Subtitle / Scope Description */}
        <p className="mt-5 text-base sm:text-lg text-slate-300 max-w-3xl leading-relaxed">
          An automated research system evaluating API accessibility, authentication methods, 
          Model Context Protocol (MCP) availability, and toolkit buildability across 10 software categories.
          Delivers evidence-grounded intelligence for Composio agent toolkits with a four-layer verification protocol.
        </p>

        {/* Ground-Truth Honesty Banner */}
        <div className="mt-6 p-4 rounded-xl bg-slate-900/90 border border-amber-500/30 flex items-start gap-3 max-w-3xl shadow-lg">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs text-slate-300 leading-normal">
            <span className="font-semibold text-amber-300 font-mono uppercase tracking-wider text-[11px] block sm:inline mr-1">
              Honesty Guarantee:
            </span>
            Human audit pending — factual accuracy not yet measured. In accordance with Composio’s verification methodology, 
            we report <strong className="text-white">Automated Verification Coverage (61% verified evidence rate across 100 apps)</strong> and 
            provide a reproducible 20-app stratified audit interface rather than fabricating synthetic human precision.
          </div>
        </div>

        {/* Action CTAs */}
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <a
            href="#findings"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-cyan-300 hover:from-cyan-300 hover:to-cyan-200 transition-all shadow-md shadow-cyan-500/20"
          >
            Explore Findings
            <ArrowDown className="w-4 h-4" />
          </a>

          <a
            href="#methodology"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold text-white bg-slate-900 hover:bg-slate-800 border border-slate-700/80 transition-all"
          >
            <BookOpen className="w-4 h-4 text-cyan-400" />
            View Research Methodology
          </a>

          <a
            href="#table"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-900/60 transition-colors"
          >
            <Database className="w-4 h-4 text-slate-400" />
            Search 100-App Table →
          </a>
        </div>
      </div>
    </section>
  );
}
