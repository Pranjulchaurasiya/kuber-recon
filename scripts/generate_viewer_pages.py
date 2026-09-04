from pathlib import Path

def create_viewer_pages():
    scratch = Path("scratch")
    scratch.mkdir(exist_ok=True)

    # 1. Benchmark Viewer
    benchmark_md = Path("reports/track04_evaluation_benchmark.md").read_text(encoding="utf-8")
    html_benchmark = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>KuberRecon — Track 04 Evaluation Benchmark</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #090D16;
      color: #E2E8F0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      padding: 40px 60px;
    }}
    .container {{
      max-width: 1400px;
      margin: 0 auto;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-b: 1px solid #1E293B;
      padding-bottom: 24px;
      margin-bottom: 32px;
    }}
    h1 {{
      font-size: 26px;
      font-weight: 800;
      color: #F8FAFC;
      letter-spacing: -0.02em;
    }}
    .tag {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(245, 158, 11, 0.15);
      border: 1px solid rgba(245, 158, 11, 0.4);
      color: #F59E0B;
      padding: 6px 14px;
      border-radius: 9999px;
      font-family: ui-monospace, monospace;
      font-size: 12px;
      font-weight: 700;
    }}
    .table-card {{
      background: #0F172A;
      border: 1px solid #1E293B;
      border-radius: 16px;
      padding: 28px;
      margin-bottom: 28px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    h2 {{
      font-size: 18px;
      font-weight: 700;
      color: #EAB308;
      margin-bottom: 16px;
      font-family: ui-monospace, monospace;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-family: ui-monospace, monospace;
      font-size: 13px;
    }}
    th, td {{
      padding: 12px 16px;
      text-align: left;
      border-bottom: 1px solid #1E293B;
    }}
    th {{
      background: #1E293B;
      color: #94A3B8;
      font-weight: 700;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.05em;
    }}
    tr:hover td {{
      background: rgba(255,255,255,0.02);
    }}
    .highlight {{
      color: #10B981;
      font-weight: 700;
    }}
    .amber {{
      color: #F59E0B;
      font-weight: 700;
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
      margin-bottom: 28px;
    }}
    .metric-card {{
      background: #0F172A;
      border: 1px solid #1E293B;
      border-radius: 14px;
      padding: 20px;
    }}
    .metric-label {{
      font-size: 11px;
      text-transform: uppercase;
      color: #94A3B8;
      font-family: ui-monospace, monospace;
      margin-bottom: 8px;
    }}
    .metric-val {{
      font-size: 24px;
      font-weight: 800;
      color: #F8FAFC;
      font-family: ui-monospace, monospace;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1>Project Evaluation Benchmark — Aligned to Track 04</h1>
        <p style="color: #94A3B8; font-size: 14px; margin-top: 6px;">
          Reproducible multi-batch evaluation across Clean, Messy, and Adversarial synthetic fixture sets.
        </p>
      </div>
      <div class="tag">● FROZEN EVALUATION BENCHMARK</div>
    </div>

    <div class="metric-grid">
      <div class="metric-card">
        <div class="metric-label">Committed Batches Evaluated</div>
        <div class="metric-val">3 Batches (824 Records)</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Observed False Auto-Matches</div>
        <div class="metric-val highlight">0 [VERIFIED ZERO]</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Unexplained Paise Delta</div>
        <div class="metric-val highlight">0 paise [EXACT DUAL]</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Ambiguous Collisions Refused</div>
        <div class="metric-val amber">100% QUARANTINED</div>
      </div>
    </div>

    <div class="table-card">
      <h2>1. Comparative Batch Benchmark Summary</h2>
      <table>
        <thead>
          <tr>
            <th>Metric / Dimension</th>
            <th>Batch 1: Clean (Target 100)</th>
            <th>Batch 2: Messy (Target 250)</th>
            <th>Batch 3: Adversarial (Target 500)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Deterministic Seed</strong></td>
            <td><code>1001</code></td>
            <td><code>2002</code></td>
            <td><code>3003</code></td>
          </tr>
          <tr>
            <td><strong>Ingested Records (Invoices + Credits)</strong></td>
            <td>125</td>
            <td>239</td>
            <td>460</td>
          </tr>
          <tr>
            <td><strong>Bank Credit Events</strong></td>
            <td>21</td>
            <td>35</td>
            <td>74</td>
          </tr>
          <tr>
            <td><strong>Exact Matches Resolved</strong></td>
            <td><span class="highlight">20</span></td>
            <td><span class="highlight">24</span></td>
            <td><span class="highlight">63</span></td>
          </tr>
          <tr>
            <td><strong>Auto-Resolved Amount</strong></td>
            <td>₹2,66,675.17</td>
            <td>₹3,94,139.45</td>
            <td>₹9,39,877.89</td>
          </tr>
          <tr>
            <td><strong>Explicit Exception Amount Held</strong></td>
            <td>₹1,485.00</td>
            <td>₹1,77,573.46</td>
            <td>₹18,985.00</td>
          </tr>
          <tr>
            <td><strong>Unexplained Paise Delta</strong></td>
            <td><span class="highlight">0 paise [ZERO DRIFT]</span></td>
            <td><span class="highlight">0 paise [ZERO DRIFT]</span></td>
            <td><span class="highlight">0 paise [ZERO DRIFT]</span></td>
          </tr>
          <tr>
            <td><strong>Observed False Auto-Matches</strong></td>
            <td><span class="highlight">0</span></td>
            <td><span class="highlight">0</span></td>
            <td><span class="highlight">0</span></td>
          </tr>
          <tr>
            <td><strong>Ambiguous Collisions Refused</strong></td>
            <td>0 (None planted)</td>
            <td>1 (100% Refused)</td>
            <td>10 (100% Refused)</td>
          </tr>
          <tr>
            <td><strong>Dense Cluster Fallback (N &gt; 24)</strong></td>
            <td>0</td>
            <td>0</td>
            <td>1 Quarantined (N=28 &gt; 24)</td>
          </tr>
          <tr>
            <td><strong>Engine Throughput</strong></td>
            <td>7,503 records/sec</td>
            <td>29,020 records/sec</td>
            <td>12,410 records/sec</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="table-card">
      <h2>2. Ground-Truth Invariant Proofs</h2>
      <p style="color: #94A3B8; font-size: 13px; line-height: 1.6; font-family: ui-monospace, monospace;">
        • <strong>0 Unexplained Paise:</strong> Ingested Bank Credits = Reconciled Matches + Quarantined Exceptions (Exact Base-10 Paise Arithmetic).<br>
        • <strong>0 Observed False Matches:</strong> Bounded Horowitz-Sahni solver halts on multiple subsets rather than guessing.<br>
        • <strong>Complexity Protection:</strong> Subsets where N &gt; 24 fail-closed to manual review without thread starvation.
      </p>
    </div>
  </div>
</body>
</html>"""
    (scratch / "viewer_benchmark.html").write_text(html_benchmark, encoding="utf-8")

    # 2. Architecture Viewer
    html_architecture = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>KuberRecon — 3-Tier Architecture & System Boundaries</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #090D16;
      color: #E2E8F0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      padding: 40px 60px;
    }
    .container {
      max-width: 1400px;
      margin: 0 auto;
    }
    .header {
      border-bottom: 1px solid #1E293B;
      padding-bottom: 24px;
      margin-bottom: 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    h1 {
      font-size: 26px;
      font-weight: 800;
      color: #F8FAFC;
      letter-spacing: -0.02em;
    }
    .tag {
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.4);
      color: #38BDF8;
      padding: 6px 14px;
      border-radius: 9999px;
      font-family: ui-monospace, monospace;
      font-size: 12px;
      font-weight: 700;
    }
    .table-card {
      background: #0F172A;
      border: 1px solid #1E293B;
      border-radius: 16px;
      padding: 28px;
      margin-bottom: 28px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    h2 {
      font-size: 18px;
      font-weight: 700;
      color: #EAB308;
      margin-bottom: 16px;
      font-family: ui-monospace, monospace;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-family: ui-monospace, monospace;
      font-size: 13px;
    }
    th, td {
      padding: 14px 16px;
      text-align: left;
      border-bottom: 1px solid #1E293B;
      vertical-align: top;
    }
    th {
      background: #1E293B;
      color: #94A3B8;
      font-weight: 700;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.05em;
    }
    .badge-green {
      display: inline-block;
      background: rgba(16, 185, 129, 0.2);
      border: 1px solid #10B981;
      color: #10B981;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
    }
    .badge-amber {
      display: inline-block;
      background: rgba(245, 158, 11, 0.2);
      border: 1px solid #F59E0B;
      color: #F59E0B;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
    }
    .badge-blue {
      display: inline-block;
      background: rgba(56, 189, 248, 0.2);
      border: 1px solid #38BDF8;
      color: #38BDF8;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1>3-Tier Architecture Boundary Matrix & Known Limitations</h1>
        <p style="color: #94A3B8; font-size: 14px; margin-top: 6px;">
          Honest distinction between tested software kernel, sandbox prototype, and future production infrastructure.
        </p>
      </div>
      <div class="tag">● CALIBRATED SYSTEM LIMITS</div>
    </div>

    <div class="table-card">
      <h2>Architectural Layer Comparison</h2>
      <table>
        <thead>
          <tr>
            <th>Architecture Layer</th>
            <th>Implementation Status</th>
            <th>Technology &amp; Execution Environment</th>
            <th>Scope &amp; Guarantees</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Tier 1: Core Financial Kernel</strong></td>
            <td><span class="badge-green">FULLY IMPLEMENTED</span></td>
            <td>Base-10 integer paise arithmetic, Horowitz–Sahni subset-sum solver, Ed25519 signatures, CAS transitions.</td>
            <td>Tested across 275 automated tests. 0 observed false auto-matches on synthetic fixtures. Dual-entry paise exact balance.</td>
          </tr>
          <tr>
            <td><strong>Tier 2: Sandbox Prototype Layer</strong></td>
            <td><span class="badge-amber">SANDBOX VERIFIED</span></td>
            <td>Local SQLite WAL storage, software demo signer, webhook-verified provider records in sandbox fixtures.</td>
            <td>Single-node process execution. Sandbox event-date validation. Simulated gateway rails when live keys absent.</td>
          </tr>
          <tr>
            <td><strong>Tier 3: Production Infrastructure</strong></td>
            <td><span class="badge-blue">FUTURE WORK</span></td>
            <td>Live Razorpay Route linked account onboarding, AWS KMS / CloudHSM key custody, multi-AZ PostgreSQL / Redis.</td>
            <td>Horizontally distributed Kubernetes pods, distributed row-level locks, live banking partner settlement clearing.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="table-card">
      <h2>System Invariant Directives</h2>
      <p style="color: #94A3B8; font-size: 13px; line-height: 1.7; font-family: ui-monospace, monospace;">
        1. <strong>Deterministic Ambiguity Refusal:</strong> The solver refuses multi-subset collisions and dense clusters rather than guessing.<br>
        2. <strong>Server-Controlled Release Evidence:</strong> Client-supplied <code>provider_records</code> are rejected (HTTP 422); releases require verified server-side evidence.<br>
        3. <strong>Paise-Exact Zero-Float Rule:</strong> All financial arithmetic executes in exact base-10 integers without IEEE 754 floating-point drift.
      </p>
    </div>
  </div>
</body>
</html>"""
    (scratch / "viewer_architecture.html").write_text(html_architecture, encoding="utf-8")
    print("Viewer pages generated successfully in scratch/")

if __name__ == "__main__":
    create_viewer_pages()
