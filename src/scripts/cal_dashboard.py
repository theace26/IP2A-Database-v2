# src/scripts/cal_dashboard.py
from __future__ import annotations

import json
from pathlib import Path

IN_JSON = Path("cal_dashboard.json")
OUT_HTML = Path("cal_dashboard.html")


def main() -> int:
    payload = json.loads(IN_JSON.read_text(encoding="utf-8"))
    decisions = payload.get("decisions", [])

    # Basic counts
    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    cat_counts = {"DATA": 0, "STRUCTURAL": 0, "RELATIONAL": 0, "TOPOLOGICAL": 0}
    blocked = 0

    for d in decisions:
        risk_counts[d["risk_level"]] = risk_counts.get(d["risk_level"], 0) + 1
        for c in d.get("categories", []):
            cat_counts[c] = cat_counts.get(c, 0) + 1
        if not d.get("allowed", True):
            blocked += 1

    rows = []
    for d in decisions:
        rows.append(
            "<tr>"
            f"<td><code>{d['migration']}</code></td>"
            f"<td><b>{d['risk_level']}</b></td>"
            f"<td>{', '.join(d.get('categories', [])) or '—'}</td>"
            f"<td>{'Yes' if d.get('legacy') else 'No'}</td>"
            f"<td>{'Yes' if d.get('breaking_ok') else 'No'}</td>"
            f"<td>{'✅' if d.get('allowed') else '⛔'}</td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>IP2A Change Advisory Dashboard</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 24px; }}
    .pill {{ display:inline-block; padding: 4px 10px; border:1px solid #ccc; border-radius: 999px; margin-right: 8px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f6f6f6; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  </style>
</head>
<body>
  <h1>Change Advisory Dashboard</h1>
  <p>
    <span class="pill">Branch: <code>{payload.get('branch')}</code></span>
    <span class="pill">Policy Env: <code>{payload.get('policy_env')}</code></span>
    <span class="pill">Enforce: <code>{payload.get('enforce')}</code></span>
    <span class="pill">Blocked: <code>{blocked}</code></span>
  </p>

  <h2>Counts</h2>
  <p>
    <span class="pill">LOW: <code>{risk_counts.get('LOW', 0)}</code></span>
    <span class="pill">MEDIUM: <code>{risk_counts.get('MEDIUM', 0)}</code></span>
    <span class="pill">HIGH: <code>{risk_counts.get('HIGH', 0)}</code></span>
  </p>
  <p>
    <span class="pill">DATA: <code>{cat_counts.get('DATA', 0)}</code></span>
    <span class="pill">STRUCTURAL: <code>{cat_counts.get('STRUCTURAL', 0)}</code></span>
    <span class="pill">RELATIONAL: <code>{cat_counts.get('RELATIONAL', 0)}</code></span>
    <span class="pill">TOPOLOGICAL: <code>{cat_counts.get('TOPOLOGICAL', 0)}</code></span>
  </p>

  <h2>Migrations</h2>
  <table>
    <tr>
      <th>Migration</th><th>Risk</th><th>Categories</th><th>Legacy</th><th>BREAKING_OK</th><th>Allowed</th>
    </tr>
    {''.join(rows)}
  </table>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"✅ Wrote {OUT_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
