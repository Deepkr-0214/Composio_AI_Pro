import React, { useState } from "react";
import { ChevronDown, ChevronUp, BookOpen, Shield, HelpCircle, AlertTriangle } from "lucide-react";

export default function MethodologySection() {
  const [openAccordion, setOpenAccordion] = useState(0);

  const sections = [
    {
      title: "1. Six-Tier Evidence Hierarchy",
      icon: BookOpen,
      content: (
        <div className="space-y-2 text-xs text-slate-300">
          <p>The research agent strictly adheres to a descending hierarchy of source credibility:</p>
          <ul className="list-disc pl-5 space-y-1 text-slate-400">
            <li><strong className="text-white">Tier 1: Official Developer Documentation & API Specs</strong> (e.g. docs.github.com, developers.hubspot.com). Primary source for endpoints, auth, and rate limits.</li>
            <li><strong className="text-white">Tier 2: Official Authentication & Security Guides</strong>. Primary source for OAuth2 flows, PKCE, and token scopes.</li>
            <li><strong className="text-white">Tier 3: Official Developer Portals & Getting Started Guides</strong>. High-level onboarding, self-serve credentials.</li>
            <li><strong className="text-white">Tier 4: Verified Vendor GitHub Repositories</strong>. Official open-source SDKs and core schemas.</li>
            <li><strong className="text-white">Tier 5: Model Context Protocol (MCP) Registries</strong>. Verified vendor or trusted community MCP servers.</li>
            <li><strong className="text-white">Tier 6: Third-Party & Community Guides</strong>. Used only when primary sources are blocked, and always flagged as unverified.</li>
          </ul>
        </div>
      ),
    },
    {
      title: "2. Classification Taxonomies & Rubrics",
      icon: Shield,
      content: (
        <div className="space-y-2 text-xs text-slate-300">
          <p>Applications are evaluated across 5 objective dimensions:</p>
          <ul className="list-disc pl-5 space-y-1 text-slate-400">
            <li><strong className="text-white">10 Authentication Types:</strong> OAuth2, API Key, Bearer Token, Personal Access Token (PAT), Basic Auth, Service Account, JWT, HMAC, Session Based, Unknown.</li>
            <li><strong className="text-white">10 Credential Accessibility Tiers:</strong> Free Self-Serve, Trial Self-Serve, Paid Self-Serve, Admin Approval, App Review, Partner Approval, Contact Sales, Enterprise Only, No Hosted Credentials, Unknown.</li>
            <li><strong className="text-white">5 API Breadth Tiers:</strong> Extensive (12+ domains), Broad (7-11), Moderate (4-6), Narrow (1-3), Unknown.</li>
            <li><strong className="text-white">5 MCP Statuses:</strong> Official MCP, Community MCP, In Progress, Unverified Claim, Unknown.</li>
            <li><strong className="text-white">5 Buildability Verdicts:</strong> Ready to Build (8-10), Feasible (6-7), Needs Investigation (4-5), Significant Barriers (2-3), Not Feasible (1).</li>
          </ul>
        </div>
      ),
    },
    {
      title: "3. Defensive Crawling & Anti-Bot Traps",
      icon: HelpCircle,
      content: (
        <div className="space-y-2 text-xs text-slate-300">
          <p>
            Modern developer portals frequently return HTTP 200 with non-documentation payloads. 
            The fetcher runs <code className="text-cyan-300 font-mono">check_content_validity()</code> on all responses:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-slate-400">
            <li><strong className="text-white">Empty Shells:</strong> Rejects pages with &lt;40 characters of text or "Please enable JavaScript".</li>
            <li><strong className="text-white">SPA Containers:</strong> Detects empty single-page app roots (&lt;div id=&quot;root&quot;&gt;&lt;/div&gt;) lacking server-rendered HTML.</li>
            <li><strong className="text-white">Cloudflare WAF:</strong> Detects Turnstile challenge walls (&quot;Attention Required! | Cloudflare&quot;) and classifies them as blocked.</li>
            <li><strong className="text-white">Login Walls:</strong> Detects &quot;Sign in to continue to Developer Portal&quot; and flags for enterprise review.</li>
          </ul>
        </div>
      ),
    },
    {
      title: "4. Known Boundaries & Limitations",
      icon: AlertTriangle,
      content: (
        <div className="space-y-2 text-xs text-slate-300">
          <p>Explicit project boundaries and research constraints:</p>
          <ul className="list-disc pl-5 space-y-1 text-slate-400">
            <li><strong className="text-white">WAF Boundaries:</strong> 39% of targeted portals cannot be scraped without authenticated browser sessions or corporate IP allowlisting.</li>
            <li><strong className="text-white">Multi-Tenant Subdomains:</strong> Platforms like Zendesk and Jira require customer tenant subdomains (<code className="text-slate-300 font-mono">&#123;subdomain&#125;.zendesk.com</code>).</li>
            <li><strong className="text-white">CLI vs Cloud REST:</strong> Tools like Sherlock CLI and Mermaid CLI lack cloud REST endpoints and must be containerized as local CLI tools.</li>
            <li><strong className="text-white">Ground-Truth Accuracy:</strong> Human review remains pending; factual accuracy is not artificially scored.</li>
          </ul>
        </div>
      ),
    },
  ];

  return (
    <section id="methodology" className="py-16 border-b border-slate-800/60 bg-slate-950/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
          <div>
            <span className="text-xs font-mono font-semibold text-cyan-400 tracking-wider uppercase">
              Rigor & Governance
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-1">
              Methodology, Evidence Rules & Limitations
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md">
            How data was extracted, validated, and reconciled under strict anti-hallucination guardrails.
          </p>
        </div>

        <div className="space-y-3">
          {sections.map((sec, idx) => {
            const isOpen = openAccordion === idx;
            const Icon = sec.icon;
            return (
              <div
                key={idx}
                className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden transition-all"
              >
                <button
                  onClick={() => setOpenAccordion(isOpen ? -1 : idx)}
                  className="w-full p-4 text-left flex items-center justify-between hover:bg-slate-900 transition-colors"
                >
                  <span className="text-sm font-semibold text-white flex items-center gap-2">
                    <Icon className="w-4 h-4 text-cyan-400" />
                    {sec.title}
                  </span>
                  {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                </button>
                {isOpen && (
                  <div className="p-4 pt-0 border-t border-slate-800/60 bg-slate-950/40">
                    {sec.content}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
