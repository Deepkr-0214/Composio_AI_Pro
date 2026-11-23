import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar.jsx";
import Hero from "./components/Hero.jsx";
import ExecutiveMetrics from "./components/ExecutiveMetrics.jsx";
import KeyFindings from "./components/KeyFindings.jsx";
import CategoryComparison from "./components/CategoryComparison.jsx";
import AuthAndAccessibility from "./components/AuthAndAccessibility.jsx";
import BuildabilityAnalysis from "./components/BuildabilityAnalysis.jsx";
import ResearchTable from "./components/ResearchTable.jsx";
import AgentWorkflow from "./components/AgentWorkflow.jsx";
import AgentDemoSection from "./components/AgentDemoSection.jsx";
import VerificationSection from "./components/VerificationSection.jsx";
import CorrectionExamples from "./components/CorrectionExamples.jsx";
import OpportunitiesSection from "./components/OpportunitiesSection.jsx";
import DataExportSection from "./components/DataExportSection.jsx";
import MethodologySection from "./components/MethodologySection.jsx";
import Footer from "./components/Footer.jsx";
import { Loader2, AlertCircle } from "lucide-react";

export default function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [apps, setApps] = useState([]);
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState({});
  const [insights, setInsights] = useState([]);
  const [verification, setVerification] = useState(null);
  const [opportunities, setOpportunities] = useState(null);
  const [demoRun, setDemoRun] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [
          appsRes,
          summaryRes,
          categoriesRes,
          insightsRes,
          verificationRes,
          opportunitiesRes,
          demoRunRes,
        ] = await Promise.all([
          fetch("./data/apps.json").then((r) => r.json()),
          fetch("./data/summary.json").then((r) => r.json()),
          fetch("./data/categories.json").then((r) => r.json()),
          fetch("./data/insights.json").then((r) => r.json()),
          fetch("./data/verification.json").then((r) => r.json()),
          fetch("./data/opportunities.json").then((r) => r.json()),
          fetch("./data/demo_run.json").then((r) => r.json()).catch(() => null),
        ]);

        setApps(appsRes);
        setSummary(summaryRes);
        setCategories(categoriesRes);
        setInsights(insightsRes);
        setVerification(verificationRes);
        setOpportunities(opportunitiesRes);
        setDemoRun(demoRunRes);
        setLoading(false);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
        setError("Failed to load research datasets from /data/. Please verify that prepare_dashboard_data.py has been run.");
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-300">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin mb-4" />
        <h2 className="text-base font-semibold text-white">Loading Research Dataset...</h2>
        <p className="text-xs text-slate-500 font-mono mt-1">Ingesting 100 applications across 10 categories</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
        <div className="max-w-md w-full p-6 rounded-2xl bg-slate-900 border border-rose-500/30 text-center">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
          <h2 className="text-base font-bold text-white mb-2">Data Load Error</h2>
          <p className="text-xs text-slate-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* 1. Sticky Navigation */}
      <Navbar />

      <main className="flex-grow">
        {/* 2. Hero Section */}
        <Hero summary={summary} />

        {/* 3. Executive Metrics */}
        <ExecutiveMetrics summary={summary} />

        {/* 4. Key Findings */}
        <KeyFindings insights={insights} />

        {/* 5. Category Comparison */}
        <CategoryComparison categories={categories} />

        {/* 6. Authentication & Accessibility */}
        <AuthAndAccessibility summary={summary} />

        {/* 7. Integration Buildability & Blockers */}
        <BuildabilityAnalysis summary={summary} />

        {/* 8. Searchable 100-Application Research Table */}
        <ResearchTable apps={apps} />

        {/* 9. Automated Research Agent Architecture */}
        <AgentWorkflow />

        {/* 10. Autonomous Agent Demonstration & CLI Traces */}
        <AgentDemoSection demoRun={demoRun} />

        {/* 11. Verification & Accuracy Section */}
        <VerificationSection verification={verification} summary={summary} />

        {/* 12. Real Correction Examples */}
        <CorrectionExamples verification={verification} />

        {/* 13. Integration Opportunities: Quick Wins vs Outreach */}
        <OpportunitiesSection opportunities={opportunities} />

        {/* 14. Data Export: Open Datasets & Audit Logs */}
        <DataExportSection />

        {/* 15. Methodology & Limitations */}
        <MethodologySection />
      </main>

      {/* 16. Reproducibility & Footer */}
      <Footer />
    </div>
  );
}
