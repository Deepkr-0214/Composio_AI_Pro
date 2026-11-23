#!/usr/bin/env python3
"""
Generate a lightweight standalone HTML audit interface for human review (Prompt 8).
Embeds the 20 sampled applications, displays first-pass vs corrected findings,
official documentation links, evidence excerpts, and provides an editable
review form with JSON/CSV export.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_FILE = ROOT / "data" / "audit_sample.json"
OUTPUT_HTML = ROOT / "data" / "audit_interface.html"


def generate_html(sample_data: dict) -> str:
    sample_json = json.dumps(sample_data["sample"], indent=2)
    meta = sample_data["metadata"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Composio Research Agent — Human Audit Worksheet</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --primary: #38bdf8;
      --accent: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 24px;
      line-height: 1.5;
    }}
    .header {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px 24px;
      margin-bottom: 24px;
    }}
    .header h1 {{
      margin: 0 0 8px 0;
      font-size: 24px;
      color: var(--primary);
    }}
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      background: rgba(56, 189, 248, 0.15);
      color: var(--primary);
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}
    .badge-warning {{
      background: rgba(245, 158, 11, 0.15);
      color: var(--warning);
      border-color: rgba(245, 158, 11, 0.3);
    }}
    .controls {{
      margin-top: 16px;
      display: flex;
      gap: 12px;
    }}
    button {{
      background: var(--primary);
      color: #0f172a;
      border: none;
      font-weight: 600;
      padding: 10px 18px;
      border-radius: 6px;
      cursor: pointer;
      transition: background 0.2s;
    }}
    button:hover {{
      background: #7dd3fc;
    }}
    .btn-secondary {{
      background: var(--border);
      color: var(--text);
    }}
    .btn-secondary:hover {{
      background: #475569;
    }}
    .app-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 24px;
    }}
    .app-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
      margin-bottom: 16px;
    }}
    .app-title {{
      font-size: 18px;
      font-weight: bold;
      color: var(--text);
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 16px;
    }}
    .sub-panel {{
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 14px;
    }}
    .sub-panel h4 {{
      margin: 0 0 10px 0;
      font-size: 14px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .field-row {{
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      padding: 4px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }}
    .field-label {{
      color: var(--muted);
    }}
    .field-val {{
      font-weight: 500;
      color: var(--text);
    }}
    .audit-form {{
      background: rgba(16, 185, 129, 0.05);
      border: 1px solid rgba(16, 185, 129, 0.2);
      border-radius: 6px;
      padding: 16px;
      margin-top: 16px;
    }}
    .audit-form h4 {{
      margin: 0 0 12px 0;
      font-size: 15px;
      color: var(--accent);
    }}
    .form-group {{
      margin-bottom: 12px;
    }}
    label {{
      display: block;
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 4px;
    }}
    input[type="text"], select, textarea {{
      width: 100%;
      background: #0f172a;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 10px;
      border-radius: 4px;
      font-size: 13px;
      box-sizing: border-box;
    }}
    textarea {{
      resize: vertical;
      height: 60px;
    }}
    a {{
      color: var(--primary);
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .excerpt-box {{
      font-size: 12px;
      background: #090d16;
      border: 1px dashed var(--border);
      padding: 10px;
      border-radius: 4px;
      color: #cbd5e1;
      margin-top: 8px;
      font-family: monospace;
    }}
  </style>
</head>
<body>

  <div class="header">
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
      <div>
        <h1>Composio Research Agent — Human Audit Worksheet</h1>
        <p style="margin: 4px 0; color: var(--muted); font-size: 14px;">
          Stratified sample of 20 applications (2 per category, seed {meta["seed"]}).
        </p>
      </div>
      <div>
        <span class="badge badge-warning">Human Review Pending</span>
      </div>
    </div>
    <div class="controls">
      <button onclick="exportJudgmentsJSON()">Export Judgments (JSON)</button>
      <button class="btn-secondary" onclick="exportJudgmentsCSV()">Export Judgments (CSV)</button>
      <button class="btn-secondary" onclick="window.print()">Print Worksheet</button>
    </div>
  </div>

  <div id="apps-container"></div>

  <script>
    const sampleApps = {sample_json};

    function renderApps() {{
      const container = document.getElementById("apps-container");
      container.innerHTML = sampleApps.map((app, idx) => {{
        const fp = app.first_pass_findings;
        const cur = app.latest_findings;
        const links = app.evidence_links.map(l => `<a href="${{l.url || l}}" target="_blank" rel="noopener">${{l.title || l.url || l}}</a>`).join(" | ") || "<em>No URLs available</em>";
        const excerpt = (app.claim_evidence && app.claim_evidence[0] && app.claim_evidence[0].supporting_excerpt) 
          ? app.claim_evidence[0].supporting_excerpt 
          : "No excerpt extracted.";

        return `
          <div class="app-card" id="card-${{app.app_id}}">
            <div class="app-header">
              <span class="app-title">[#${{app.app_id}}] ${{app.app_name}}</span>
              <span class="badge">${{app.category_name}}</span>
            </div>

            <div class="grid-2">
              <div class="sub-panel">
                <h4>Original First-Pass Findings</h4>
                <div class="field-row"><span class="field-label">Auth:</span><span class="field-val">${{(fp.auth_methods || []).join(", ") || "unknown"}}</span></div>
                <div class="field-row"><span class="field-label">API Surface:</span><span class="field-val">${{(fp.api_type || []).join(", ") || "unknown"}}</span></div>
                <div class="field-row"><span class="field-label">MCP Status:</span><span class="field-val">${{fp.mcp_status}}</span></div>
                <div class="field-row"><span class="field-label">Buildability:</span><span class="field-val">${{fp.buildability_verdict}} (${{fp.toolkit_buildability_score || "N/A"}})</span></div>
                <div class="field-row"><span class="field-label">Quality Gate:</span><span class="field-val">${{fp.quality_gate_status}}</span></div>
              </div>

              <div class="sub-panel">
                <h4>Latest Verified Findings</h4>
                <div class="field-row"><span class="field-label">Auth:</span><span class="field-val">${{(cur.auth_methods || []).join(", ") || "unknown"}}</span></div>
                <div class="field-row"><span class="field-label">API Surface:</span><span class="field-val">${{(cur.api_type || []).join(", ") || "unknown"}}</span></div>
                <div class="field-row"><span class="field-label">MCP Status:</span><span class="field-val">${{cur.mcp_status}}</span></div>
                <div class="field-row"><span class="field-label">Buildability:</span><span class="field-val">${{cur.buildability_verdict}} (${{cur.toolkit_buildability_score || "N/A"}})</span></div>
                <div class="field-row"><span class="field-label">Quality Gate:</span><span class="field-val">${{cur.quality_gate_status}}</span></div>
              </div>
            </div>

            <div style="font-size: 13px; margin-bottom: 12px;">
              <strong>Retrieved Documentation Links:</strong> ${{links}}
            </div>

            <div class="excerpt-box">
              <strong>Cited Excerpt:</strong> ${{excerpt}}
            </div>

            <div class="audit-form">
              <h4>Human Auditor Evaluation Form</h4>
              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 10px;">
                <div>
                  <label>Audit Judgment:</label>
                  <select id="judgment-${{app.app_id}}">
                    <option value="UNREVIEWED">-- Pending Human Review --</option>
                    <option value="CORRECT">Correct (Matches Verified Finding)</option>
                    <option value="INCORRECT">Incorrect (Requires Correction)</option>
                    <option value="UNVERIFIABLE">Unverifiable (No Official Docs)</option>
                  </select>
                </div>
                <div>
                  <label>Human Verified Auth:</label>
                  <input type="text" id="auth-${{app.app_id}}" placeholder="e.g. OAuth2, API Key">
                </div>
                <div>
                  <label>Human Verified API Surface:</label>
                  <input type="text" id="api-${{app.app_id}}" placeholder="e.g. REST, GraphQL">
                </div>
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 10px;">
                <div>
                  <label>Human Verified MCP Status:</label>
                  <select id="mcp-${{app.app_id}}">
                    <option value="">-- Select --</option>
                    <option value="official_mcp">Official MCP</option>
                    <option value="community_mcp">Community MCP</option>
                    <option value="unknown">Unknown / None</option>
                  </select>
                </div>
                <div>
                  <label>Human Verified Buildability:</label>
                  <select id="build-${{app.app_id}}">
                    <option value="">-- Select --</option>
                    <option value="ready_to_build">Ready to Build</option>
                    <option value="feasible">Feasible</option>
                    <option value="needs_investigation">Needs Investigation</option>
                    <option value="significant_barriers">Significant Barriers</option>
                  </select>
                </div>
                <div>
                  <label>Auditor Evidence URL:</label>
                  <input type="text" id="url-${{app.app_id}}" placeholder="https://...">
                </div>
              </div>

              <div class="form-group">
                <label>Auditor Notes & Rationales:</label>
                <textarea id="notes-${{app.app_id}}" placeholder="Document specific findings, discrepancies, or reasons for override..."></textarea>
              </div>
            </div>
          </div>
        `;
      }}).join("");
    }}

    function exportJudgmentsJSON() {{
      const results = sampleApps.map(app => {{
        const aid = app.app_id;
        return {{
          app_id: aid,
          app_name: app.app_name,
          category: app.category_name,
          judgment: document.getElementById(`judgment-${{aid}}`).value,
          verified_auth_methods: document.getElementById(`auth-${{aid}}`).value,
          verified_api_surface: document.getElementById(`api-${{aid}}`).value,
          verified_mcp_status: document.getElementById(`mcp-${{aid}}`).value,
          verified_buildability_verdict: document.getElementById(`build-${{aid}}`).value,
          evidence_url: document.getElementById(`url-${{aid}}`).value,
          auditor_notes: document.getElementById(`notes-${{aid}}`).value,
          exported_at: new Date().toISOString()
        }};
      }});

      const blob = new Blob([JSON.stringify(results, null, 2)], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "human_audit_completed.json";
      a.click();
    }}

    function exportJudgmentsCSV() {{
      const headers = ["app_id","app_name","category","judgment","verified_auth_methods","verified_api_surface","verified_mcp_status","verified_buildability_verdict","evidence_url","auditor_notes","exported_at"];
      const rows = sampleApps.map(app => {{
        const aid = app.app_id;
        return [
          aid,
          `"${{app.app_name}}"`,
          `"${{app.category_name}}"`,
          document.getElementById(`judgment-${{aid}}`).value,
          `"${{document.getElementById(`auth-${{aid}}`).value}}"`,
          `"${{document.getElementById(`api-${{aid}}`).value}}"`,
          document.getElementById(`mcp-${{aid}}`).value,
          document.getElementById(`build-${{aid}}`).value,
          `"${{document.getElementById(`url-${{aid}}`).value}}"`,
          `"${{document.getElementById(`notes-${{aid}}`).value.replace(/"/g, '""')}}"`,
          new Date().toISOString()
        ].join(",");
      }});

      const csvContent = [headers.join(","), ...rows].join("\\n");
      const blob = new Blob([csvContent], {{ type: "text/csv" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "human_audit_completed.csv";
      a.click();
    }}

    renderApps();
  </script>
</body>
</html>
"""


def main():
    with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_content = generate_html(data)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated standalone human audit interface: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
