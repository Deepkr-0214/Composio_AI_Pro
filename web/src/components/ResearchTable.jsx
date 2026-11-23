import React, { useState, useMemo } from "react";
import { Search, Filter, X, ChevronDown, ChevronUp, ExternalLink, ShieldCheck, AlertCircle, Key, Lock, Globe, Cpu, CheckCircle2, XCircle } from "lucide-react";

export default function ResearchTable({ apps }) {
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedAuth, setSelectedAuth] = useState("all");
  const [selectedCred, setSelectedCred] = useState("all");
  const [selectedMcp, setSelectedMcp] = useState("all");
  const [selectedBuildability, setSelectedBuildability] = useState("all");
  const [selectedGate, setSelectedGate] = useState("all");
  const [sortBy, setSortBy] = useState("priority_score");
  const [sortOrder, setSortOrder] = useState("desc");
  const [expandedAppId, setExpandedAppId] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  // Extract filter options dynamically
  const categories = useMemo(() => {
    return Array.from(new Set((apps || []).map((a) => a.category_name))).sort();
  }, [apps]);

  const authOptions = ["OAuth2", "API Key", "Bearer Token", "Personal Access Token", "Basic Auth", "unknown"];
  const credOptions = ["free_self_serve", "trial_self_serve", "paid_self_serve", "contact_sales", "enterprise_only", "unknown"];
  const mcpOptions = ["official_mcp", "community_mcp", "mcp_unverified", "unknown"];
  const buildOptions = ["ready_to_build", "feasible", "needs_investigation", "significant_barriers"];

  // Filter & Sort
  const filteredApps = useMemo(() => {
    return (apps || []).filter((a) => {
      // Search
      if (search) {
        const q = search.toLowerCase();
        const matchesName = a.app_name?.toLowerCase().includes(q);
        const matchesCat = a.category_name?.toLowerCase().includes(q);
        const matchesDesc = a.description?.toLowerCase().includes(q);
        if (!matchesName && !matchesCat && !matchesDesc) return false;
      }
      // Category
      if (selectedCategory !== "all" && a.category_name !== selectedCategory) {
        return false;
      }
      // Auth
      if (selectedAuth !== "all") {
        if (selectedAuth === "unknown") {
          if (a.auth_methods && a.auth_methods.length > 0 && a.auth_methods[0] !== "unknown") return false;
        } else if (!a.auth_methods || !a.auth_methods.includes(selectedAuth)) {
          return false;
        }
      }
      // Credential
      if (selectedCred !== "all" && a.credential_accessibility !== selectedCred) {
        return false;
      }
      // MCP
      if (selectedMcp !== "all" && a.mcp_status !== selectedMcp) {
        return false;
      }
      // Buildability
      if (selectedBuildability !== "all" && a.buildability_verdict !== selectedBuildability) {
        return false;
      }
      // Gate
      if (selectedGate !== "all" && a.quality_gate_status !== selectedGate) {
        return false;
      }
      return true;
    }).sort((a, b) => {
      let valA = a[sortBy];
      let valB = b[sortBy];
      if (typeof valA === "string") valA = valA.toLowerCase();
      if (typeof valB === "string") valB = valB.toLowerCase();
      if (valA < valB) return sortOrder === "asc" ? -1 : 1;
      if (valA > valB) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });
  }, [apps, search, selectedCategory, selectedAuth, selectedCred, selectedMcp, selectedBuildability, selectedGate, sortBy, sortOrder]);

  // Reset page when filters change
  const totalPages = Math.ceil(filteredApps.length / pageSize) || 1;
  const paginatedApps = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredApps.slice(start, start + pageSize);
  }, [filteredApps, currentPage]);

  const clearAllFilters = () => {
    setSearch("");
    setSelectedCategory("all");
    setSelectedAuth("all");
    setSelectedCred("all");
    setSelectedMcp("all");
    setSelectedBuildability("all");
    setSelectedGate("all");
    setCurrentPage(1);
  };

  const hasActiveFilters = search || selectedCategory !== "all" || selectedAuth !== "all" || 
    selectedCred !== "all" || selectedMcp !== "all" || selectedBuildability !== "all" || selectedGate !== "all";

  const toggleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  };

  const getVerdictBadge = (verdict) => {
    switch (verdict) {
      case "ready_to_build":
        return <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 whitespace-nowrap">Ready to Build</span>;
      case "feasible":
        return <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 whitespace-nowrap">Feasible</span>;
      case "needs_investigation":
        return <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20 whitespace-nowrap">Needs Investigation</span>;
      case "significant_barriers":
        return <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-rose-500/10 text-rose-400 border border-rose-500/20 whitespace-nowrap">Significant Barriers</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-400 whitespace-nowrap">{verdict}</span>;
    }
  };

  const getGateBadge = (gate) => {
    switch (gate) {
      case "passed":
        return <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Passed</span>;
      case "partial":
        return <span className="inline-flex items-center gap-1 text-[11px] font-mono text-amber-400"><span className="w-1.5 h-1.5 rounded-full bg-amber-400" /> Partial</span>;
      case "needs_review":
        return <span className="inline-flex items-center gap-1 text-[11px] font-mono text-rose-400"><span className="w-1.5 h-1.5 rounded-full bg-rose-400" /> Review</span>;
      default:
        return <span className="text-[11px] font-mono text-slate-400">{gate}</span>;
    }
  };

  return (
    <section id="table" className="py-16 border-b border-slate-800/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <span className="text-xs font-mono font-semibold text-cyan-400 tracking-wider uppercase">
              Full Ground-Truth Records
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-1">
              Searchable 100-Application Research Table
            </h2>
          </div>
          <div className="text-xs sm:text-sm text-slate-400 font-mono">
            Showing <strong className="text-white">{filteredApps.length}</strong> of 100 applications
          </div>
        </div>

        {/* Filter Controls Box */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 mb-6 space-y-3">
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by application name, category, or keyword..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setCurrentPage(1); }}
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
              />
            </div>

            {/* Category Dropdown */}
            <select
              value={selectedCategory}
              onChange={(e) => { setSelectedCategory(e.target.value); setCurrentPage(1); }}
              className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="all">All Categories (10)</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            {/* Buildability Verdict Dropdown */}
            <select
              value={selectedBuildability}
              onChange={(e) => { setSelectedBuildability(e.target.value); setCurrentPage(1); }}
              className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="all">All Buildability</option>
              <option value="ready_to_build">Ready to Build</option>
              <option value="feasible">Feasible</option>
              <option value="needs_investigation">Needs Investigation</option>
              <option value="significant_barriers">Significant Barriers</option>
            </select>

            {/* Quality Gate Dropdown */}
            <select
              value={selectedGate}
              onChange={(e) => { setSelectedGate(e.target.value); setCurrentPage(1); }}
              className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="all">All Quality Gates</option>
              <option value="passed">Gate Passed</option>
              <option value="partial">Partial Evidence</option>
              <option value="needs_review">Needs Review (WAF/Login)</option>
            </select>
          </div>

          {/* Secondary Filter Row */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80 text-xs">
            <span className="text-slate-400 text-[11px] font-mono mr-1">More Filters:</span>

            {/* Auth filter */}
            <select
              value={selectedAuth}
              onChange={(e) => { setSelectedAuth(e.target.value); setCurrentPage(1); }}
              className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 focus:outline-none"
            >
              <option value="all">Auth: All</option>
              {authOptions.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>

            {/* Credential Access filter */}
            <select
              value={selectedCred}
              onChange={(e) => { setSelectedCred(e.target.value); setCurrentPage(1); }}
              className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 focus:outline-none"
            >
              <option value="all">Access: All</option>
              {credOptions.map((o) => (
                <option key={o} value={o}>{o.replace(/_/g, " ")}</option>
              ))}
            </select>

            {/* MCP filter */}
            <select
              value={selectedMcp}
              onChange={(e) => { setSelectedMcp(e.target.value); setCurrentPage(1); }}
              className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 focus:outline-none"
            >
              <option value="all">MCP: All</option>
              {mcpOptions.map((o) => (
                <option key={o} value={o}>{o.replace(/_/g, " ")}</option>
              ))}
            </select>

            {hasActiveFilters && (
              <button
                onClick={clearAllFilters}
                className="ml-auto inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 text-[11px] font-mono transition-colors"
              >
                <X className="w-3 h-3" />
                Clear Filters
              </button>
            )}
          </div>

          {/* Active Filter Badges */}
          {hasActiveFilters && (
            <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[10px] font-mono">
              <span className="text-slate-500">Active:</span>
              {search && (
                <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 flex items-center gap-1">
                  &quot;{search}&quot;
                  <X className="w-2.5 h-2.5 cursor-pointer" onClick={() => setSearch("")} />
                </span>
              )}
              {selectedCategory !== "all" && (
                <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 flex items-center gap-1">
                  Cat: {selectedCategory}
                  <X className="w-2.5 h-2.5 cursor-pointer" onClick={() => setSelectedCategory("all")} />
                </span>
              )}
              {selectedBuildability !== "all" && (
                <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 flex items-center gap-1">
                  Verdict: {selectedBuildability}
                  <X className="w-2.5 h-2.5 cursor-pointer" onClick={() => setSelectedBuildability("all")} />
                </span>
              )}
              {selectedGate !== "all" && (
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1">
                  Gate: {selectedGate}
                  <X className="w-2.5 h-2.5 cursor-pointer" onClick={() => setSelectedGate("all")} />
                </span>
              )}
              {selectedAuth !== "all" && (
                <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 flex items-center gap-1">
                  Auth: {selectedAuth}
                  <X className="w-2.5 h-2.5 cursor-pointer" onClick={() => setSelectedAuth("all")} />
                </span>
              )}
            </div>
          )}
        </div>

        {/* Data Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
          <table className="min-w-full divide-y divide-slate-800 text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 font-mono uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-3 text-center w-12 cursor-pointer hover:text-white" onClick={() => toggleSort("app_id")}>
                  ID {sortBy === "app_id" && (sortOrder === "asc" ? "↑" : "↓")}
                </th>
                <th className="py-3 px-4 cursor-pointer hover:text-white" onClick={() => toggleSort("app_name")}>
                  Application {sortBy === "app_name" && (sortOrder === "asc" ? "↑" : "↓")}
                </th>
                <th className="py-3 px-4 cursor-pointer hover:text-white" onClick={() => toggleSort("category_name")}>
                  Category {sortBy === "category_name" && (sortOrder === "asc" ? "↑" : "↓")}
                </th>
                <th className="py-3 px-3">Auth Methods</th>
                <th className="py-3 px-3">API Surface</th>
                <th className="py-3 px-3 text-center">MCP</th>
                <th className="py-3 px-3 text-center cursor-pointer hover:text-white" onClick={() => toggleSort("priority_score")}>
                  Priority {sortBy === "priority_score" && (sortOrder === "asc" ? "↑" : "↓")}
                </th>
                <th className="py-3 px-3">Buildability</th>
                <th className="py-3 px-3 text-center">Quality Gate</th>
                <th className="py-3 px-3 text-center">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {paginatedApps.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400">
                    <AlertCircle className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                    <p className="text-sm font-semibold text-white">No applications match your filter criteria.</p>
                    <p className="text-xs text-slate-500 mt-1">Try resetting the search query or adjusting attribute dropdowns.</p>
                    <button
                      onClick={clearAllFilters}
                      className="mt-3 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-300"
                    >
                      Reset All Filters
                    </button>
                  </td>
                </tr>
              ) : (
                paginatedApps.map((a) => {
                  const isExpanded = expandedAppId === a.app_id;
                  return (
                    <React.Fragment key={a.app_id}>
                      <tr
                        onClick={() => setExpandedAppId(isExpanded ? null : a.app_id)}
                        className={`cursor-pointer transition-colors ${
                          isExpanded ? "bg-cyan-500/5 text-white" : "hover:bg-slate-900/70 text-slate-300"
                        }`}
                      >
                        <td className="py-3 px-3 text-center font-mono text-slate-500">{a.app_id}</td>
                        <td className="py-3 px-4 font-semibold text-white">{a.app_name}</td>
                        <td className="py-3 px-4 text-slate-300 truncate max-w-[160px]">{a.category_name}</td>
                        <td className="py-3 px-3 font-mono text-[11px] truncate max-w-[130px]">
                          {a.auth_methods && a.auth_methods.length > 0 && a.auth_methods[0] !== "unknown"
                            ? a.auth_methods.join(", ")
                            : <span className="text-slate-500 italic">unknown</span>}
                        </td>
                        <td className="py-3 px-3 font-mono text-[11px]">
                          {a.api_type && a.api_type.length > 0 && a.api_type[0] !== "unknown"
                            ? a.api_type.join(" / ")
                            : <span className="text-slate-500 italic">unknown</span>}
                        </td>
                        <td className="py-3 px-3 text-center font-mono text-[11px]">
                          {a.mcp_status === "official_mcp" ? (
                            <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold">Official</span>
                          ) : a.mcp_status === "community_mcp" || a.mcp_status === "mcp_unverified" ? (
                            <span className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300">Community</span>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-center font-mono font-bold text-cyan-400">
                          {a.priority_score}
                        </td>
                        <td className="py-3 px-3">
                          {getVerdictBadge(a.buildability_verdict)}
                        </td>
                        <td className="py-3 px-3 text-center">
                          {getGateBadge(a.quality_gate_status)}
                        </td>
                        <td className="py-3 px-3 text-center">
                          <button
                            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
                            title="Inspect evidence links & claim citations"
                          >
                            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </td>
                      </tr>

                      {/* Expandable Detail Drawer */}
                      {isExpanded && (
                        <tr className="bg-slate-950/90 border-b border-slate-800">
                          <td colSpan={10} className="p-6">
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                              {/* Col 1: Core Summary & Opportunity Group */}
                              <div>
                                <h4 className="text-sm font-bold text-white flex items-center gap-2 mb-2">
                                  <span>{a.app_name}</span>
                                  <span className="text-xs font-mono text-slate-400 font-normal">({a.category_name})</span>
                                </h4>
                                <p className="text-xs text-slate-300 leading-relaxed mb-4">
                                  {a.description || "Target application evaluated in empirical research dataset."}
                                </p>

                                <div className="space-y-1.5 text-xs font-mono">
                                  <div className="text-slate-400">
                                    <strong className="text-slate-300">Opportunity Group:</strong> {a.opportunity_group}
                                  </div>
                                  <div className="text-slate-400">
                                    <strong className="text-slate-300">Primary Blocker:</strong> {a.primary_blocker}
                                  </div>
                                  <div className="text-slate-400">
                                    <strong className="text-slate-300">Toolkit Buildability Score:</strong> {a.toolkit_buildability_score} / 10
                                  </div>
                                  <div className="text-slate-400">
                                    <strong className="text-slate-300">Confidence:</strong> {a.confidence.toUpperCase()}
                                  </div>
                                  <div className="text-slate-400">
                                    <strong className="text-slate-300">Status Distinction:</strong>{" "}
                                    {a.quality_gate_status === "needs_review" ? (
                                      <span className="text-rose-400">UNKNOWN (WAF / Login Blocked, not negative claim)</span>
                                    ) : (
                                      <span className="text-emerald-400">Empirically Grounded</span>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {/* Col 2: Technical Profile */}
                              <div className="space-y-2 text-xs font-mono">
                                <span className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider block mb-1">
                                  Technical Profile
                                </span>
                                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                  <span className="text-slate-400 block text-[10px]">AUTHENTICATION METHODS:</span>
                                  <span className="text-white font-semibold">
                                    {a.auth_methods && a.auth_methods.length > 0 && a.auth_methods[0] !== "unknown" 
                                      ? a.auth_methods.join(", ") 
                                      : "unknown (Unresolved by documentation scrape)"}
                                  </span>
                                </div>
                                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                  <span className="text-slate-400 block text-[10px]">CREDENTIAL ACCESSIBILITY:</span>
                                  <span className="text-white font-semibold">
                                    {a.credential_accessibility.replace(/_/g, " ")}
                                  </span>
                                </div>
                                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                  <span className="text-slate-400 block text-[10px]">API BREADTH & PROTOCOLS:</span>
                                  <span className="text-white font-semibold">
                                    {a.api_breadth} breadth ({a.api_type && a.api_type.length > 0 && a.api_type[0] !== "unknown" ? a.api_type.join(", ") : "unknown"})
                                  </span>
                                </div>
                                {a.mcp_repository_url && (
                                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                                    <span className="text-slate-400 block text-[10px]">MCP REPOSITORY:</span>
                                    <a href={a.mcp_repository_url} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline inline-flex items-center gap-1 truncate max-w-full">
                                      {a.mcp_repository_url} <ExternalLink className="w-3 h-3 shrink-0" />
                                    </a>
                                  </div>
                                )}
                              </div>

                              {/* Col 3: Atomic Evidence Citations */}
                              <div>
                                <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block mb-2">
                                  Verified Documentation Citations ({a.evidence_count})
                                </span>
                                {a.evidence_links && a.evidence_links.length > 0 ? (
                                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1 scrollbar-thin">
                                    {a.evidence_links.map((link, lIdx) => (
                                      <div key={lIdx} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px]">
                                        <a
                                          href={link.url}
                                          target="_blank"
                                          rel="noreferrer"
                                          className="font-medium text-cyan-400 hover:underline flex items-center gap-1 mb-1 truncate"
                                        >
                                          {link.title || link.url} <ExternalLink className="w-3 h-3 shrink-0" />
                                        </a>
                                        {link.excerpt && (
                                          <p className="text-slate-300 font-mono text-[10px] line-clamp-3 bg-slate-950/60 p-1.5 rounded border border-slate-800/80">
                                            &quot;{link.excerpt}&quot;
                                          </p>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800 text-xs text-slate-400 italic">
                                    No public documentation content retrieved. Blocked by Cloudflare WAF bot challenge wall (HTTP 403) or private client login.
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-4 text-xs font-mono text-slate-400">
          <div>
            Page <strong className="text-white">{currentPage}</strong> of <strong className="text-white">{totalPages}</strong> ({filteredApps.length} total results)
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 border border-slate-800 text-slate-300 transition-colors"
            >
              Previous
            </button>
            {Array.from({ length: totalPages }).map((_, idx) => (
              <button
                key={idx + 1}
                onClick={() => setCurrentPage(idx + 1)}
                className={`w-7 h-7 rounded-lg text-xs font-mono transition-colors ${
                  currentPage === idx + 1
                    ? "bg-cyan-500 text-slate-950 font-bold"
                    : "bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800"
                }`}
              >
                {idx + 1}
              </button>
            ))}
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 border border-slate-800 text-slate-300 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
