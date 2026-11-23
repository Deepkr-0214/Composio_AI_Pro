import React, { useState } from "react";
import { Terminal, ShieldAlert, Menu, X, ArrowUpRight, Database, Download, Play } from "lucide-react";

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { label: "Overview", href: "#overview" },
    { label: "Insights", href: "#insights" },
    { label: "Categories", href: "#categories" },
    { label: "100-App Table", href: "#table" },
    { label: "Architecture", href: "#agent" },
    { label: "Live Demo", href: "#demo" },
    { label: "Verification", href: "#verification" },
    { label: "Opportunities", href: "#opportunities" },
    { label: "Data Export", href: "#export" },
    { label: "Methodology", href: "#methodology" },
  ];

  return (
    <nav className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-semibold text-white tracking-tight flex items-center gap-1.5 text-base">
                Composio
                <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  AI Product Ops
                </span>
              </span>
              <span className="block text-[11px] text-slate-400 font-mono">
                100-App Empirical Research
              </span>
            </div>
          </div>

          {/* Desktop Nav Links */}
          <div className="hidden xl:flex items-center space-x-1">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-900 transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* Right Status Badge & Actions */}
          <div className="hidden sm:flex items-center space-x-2.5">
            <div
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/30"
              title="Ground-truth human accuracy is pending external audit. No artificial accuracy claims are displayed."
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              Human Audit Pending
            </div>

            <a
              href="#demo"
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition-all"
            >
              <Play className="w-3 h-3 text-cyan-400" />
              <span>Demo</span>
            </a>

            <a
              href="#export"
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/60 transition-all"
            >
              <Download className="w-3 h-3 text-slate-400" />
              <span>Export</span>
            </a>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex xl:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-900 focus:outline-none"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileMenuOpen && (
        <div className="xl:hidden border-b border-slate-800 bg-slate-950 px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-md text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-900"
            >
              {link.label}
            </a>
          ))}
          <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span className="font-mono text-amber-400">Status: Human Audit Pending</span>
            <div className="flex items-center gap-3">
              <a href="#demo" onClick={() => setMobileMenuOpen(false)} className="text-cyan-400 hover:underline">
                Demo
              </a>
              <a href="#export" onClick={() => setMobileMenuOpen(false)} className="text-cyan-400 hover:underline">
                Export Data
              </a>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
