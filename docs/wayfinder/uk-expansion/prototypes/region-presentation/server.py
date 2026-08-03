#!/usr/bin/env python3
"""THROWAWAY PROTOTYPE — demonstrate region presentation in Discord and on the ledger.

Serves real Store data for both US and UK regions so you can click through
variants and pick the right shape. See the ticket for the decision options.
"""

import json
import pathlib
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PROTOTYPE_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

import job_alert  # noqa: E402


def build_derived_view(region=None):
    store = job_alert.Store(REPO_ROOT / "jobs.json")
    rows = []
    now_ts = int(time.time())
    for rec in store.region_records(region or job_alert.REGION_US):
        keep, score, reason = job_alert.classify(
            rec.get("title", ""),
            rec.get("degrees"),
            rec.get("category"),
        )
        ref = rec.get("posted") or rec.get("first_seen") or 0
        rows.append(
            {
                "uid": rec.get("uid", ""),
                "title": rec.get("title", ""),
                "company": rec.get("company", ""),
                "locations": rec.get("locations", []),
                "source": rec.get("source", ""),
                "score": score,
                "reason": reason,
                "region": region or "US",
                "age_days": (now_ts - ref) // 86400 if ref else None,
            }
        )
    return rows


def build_all_regions_view():
    """Return rows from all eligible regions with a region column."""
    store = job_alert.Store(REPO_ROOT / "jobs.json")
    rows = []
    now_ts = int(time.time())
    for rec in store.jobs.values():
        if rec.get("migrated"):
            continue
        locations = rec.get("locations") or []
        for region in job_alert.ELIGIBLE_REGIONS:
            view = job_alert.strict_region_record(rec, region)
            if view is None:
                continue
            keep, score, reason = job_alert.classify(
                view.get("title", ""),
                view.get("degrees"),
                view.get("category"),
            )
            if score < 5:
                continue
            ref = view.get("posted") or view.get("first_seen") or 0
            rows.append(
                {
                    "uid": view.get("uid", ""),
                    "title": view.get("title", ""),
                    "company": view.get("company", ""),
                    "locations": view.get("locations", []),
                    "source": view.get("source", ""),
                    "score": score,
                    "reason": reason,
                    "region": region,
                    "age_days": (now_ts - ref) // 86400 if ref else None,
                }
            )
    return rows


def region_emoji(region):
    return {"US": "🇺🇸", "UK": "🇬🇧"}.get(region, "🌐")


def region_tag(region):
    return f"{region_emoji(region)} {region}"


class PrototypeHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(build_html().encode())
        elif self.path == "/api/us":
            self._serve_json(build_derived_view(job_alert.REGION_US))
        elif self.path == "/api/uk":
            self._serve_json(build_derived_view(job_alert.REGION_UK))
        elif self.path == "/api/all":
            self._serve_json(build_all_regions_view())
        elif self.path == "/api/stats":
            self._serve_json(build_stats())
        else:
            super().do_GET()

    def _serve_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass  # Silence request logs


def build_stats():
    store = job_alert.Store(REPO_ROOT / "jobs.json")
    us_count = len(store.region_records(job_alert.REGION_US))
    uk_count = len(store.region_records(job_alert.REGION_UK))
    return {
        "us_records": us_count,
        "uk_records": uk_count,
        "total": us_count + uk_count,
    }


def build_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Region Presentation Prototype — kelsa-hunt</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 960px; margin: 0 auto; padding: 1rem; }
  h1 { font-size: 1.4rem; }
  h2 { font-size: 1.1rem; margin-top: 2rem; }
  h3 { font-size: 1rem; margin-top: 1.5rem; }
  table { border-collapse: collapse; width: 100%; font-size: 0.85rem; }
  th, td { border: 1px solid #ddd; padding: 0.3rem 0.5rem; text-align: left; }
  th { background: #f5f5f5; cursor: pointer; }
  th:hover { background: #e0e0e0; }
  tr:hover { background: #fafafa; }
  .region-us { background: #e8f5e9; }
  .region-uk { background: #e3f2fd; }
  .region-tag { font-weight: bold; }
  .score-10 { color: #2e7d32; font-weight: bold; }
  .score-5 { color: #1565c0; }
  .score-3 { color: #757575; }
  .btn { padding: 0.3rem 0.6rem; margin: 0.2rem; cursor: pointer; border: 1px solid #ccc; background: #fafafa; border-radius: 3px; font-size: 0.8rem; }
  .btn.active { background: #1976d2; color: white; border-color: #1976d2; }
  .variant { margin-bottom: 2rem; padding: 1rem; border: 1px solid #e0e0e0; border-radius: 4px; }
  .variant h3 { margin-top: 0; }
  .decision { font-style: italic; color: #666; margin-bottom: 0.5rem; }
  .embed-preview { background: #fafafa; border: 1px solid #e0e0e0; padding: 0.5rem; border-radius: 4px; margin: 0.3rem 0; font-family: monospace; font-size: 0.8rem; white-space: pre-wrap; }
  .stats { display: flex; gap: 2rem; margin-bottom: 1rem; }
  .stat { text-align: center; }
  .stat .num { font-size: 1.5rem; font-weight: bold; }
  .stat .label { font-size: 0.75rem; color: #666; }
</style>
</head>
<body>
<h1>Region Presentation Prototype</h1>
<p>Click through variants to decide how region appears in Discord and on the ledger.</p>

<div class="stats" id="stats"></div>

<h2>Variant A — Mixed default, region column</h2>
<div class="variant">
  <p class="decision">Default view shows both regions mixed, sorted by score. A "Region" column lets users filter.</p>
  <button class="btn active" onclick="loadView('mixed')">Load data</button>
  <div id="variant-a"></div>
</div>

<h2>Variant B — Default to US, UK click-away</h2>
<div class="variant">
  <p class="decision">Page opens showing US only. UK is a tab/link at the top. UK rows are fewer so they don't bury US content.</p>
  <button class="btn" onclick="loadView('us-default')">Load US data</button>
  <button class="btn" onclick="loadView('uk-default')">Load UK data</button>
  <div id="variant-b"></div>
</div>

<h2>Variant C — Grouped by region</h2>
<div class="variant">
  <p class="decision">Rows are grouped under US and UK headers. Easier to scan at a glance, but takes more vertical space.</p>
  <button class="btn" onclick="loadView('grouped')">Load grouped data</button>
  <div id="variant-c"></div>
</div>

<h2>Discord Embed Variants</h2>
<div class="variant">
  <h3>Option 1 — Region emoji in title prefix</h3>
  <div class="embed-preview" id="embed-1"></div>

  <h3>Option 2 — Region field in embed</h3>
  <div class="embed-preview" id="embed-2"></div>

  <h3>Option 3 — Region in digest row (compact)</h3>
  <div class="embed-preview" id="embed-3"></div>
</div>

<h2>Mixed Batch Ordering</h2>
<div class="variant">
  <h3>Interleaved (current sort key)</h3>
  <div id="batch-interleaved"></div>

  <h3>Sectioned by region (US first, then UK)</h3>
  <div id="batch-sectioned"></div>
</div>

<script>
const API = '/api';

async function loadJSON(url) {
  const resp = await fetch(url);
  return resp.json();
}

function esc(s) { return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function renderTable(container, rows, columns) {
  if (!rows.length) { container.innerHTML = '<p>No data</p>'; return; }
  let html = '<table><thead><tr>';
  columns.forEach(c => { html += `<th>${esc(c.label)}</th>`; });
  html += '</tr></thead><tbody>';
  rows.forEach(r => {
    html += '<tr>';
    columns.forEach(c => {
      const val = c.key ? r[c.key] : c.fn(r);
      html += `<td>${esc(String(val))}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  container.innerHTML = html;
}

async function loadView(view) {
  const data = await loadJSON(`${API}/all`);
  let rows = data;

  if (view === 'us-default') rows = data.filter(r => r.region === 'US');
  if (view === 'uk-default') rows = data.filter(r => r.region === 'UK');

  const cols = [
    { label: 'Region', key: 'region' },
    { label: 'Score', key: 'score' },
    { label: 'Company', key: 'company' },
    { label: 'Title', key: 'title' },
    { label: 'Locations', key: 'locations' },
    { label: 'Source', key: 'source' },
    { label: 'Age', key: 'age_days' },
  ];

  if (view === 'mixed' || view === 'us-default' || view === 'uk-default') {
    renderTable(document.getElementById('variant-a'), rows, cols);
  }

  if (view === 'us-default') {
    renderTable(document.getElementById('variant-b'), rows, cols);
  } else if (view === 'uk-default') {
    renderTable(document.getElementById('variant-b'), rows, cols);
  }

  if (view === 'grouped') {
    const grouped = {};
    rows.forEach(r => {
      if (!grouped[r.region]) grouped[r.region] = [];
      grouped[r.region].push(r);
    });
    let html = '';
    for (const [region, regionRows] of Object.entries(grouped)) {
      html += `<h4>${region} (${regionRows.length})</h4>`;
      html += '<table><thead><tr>';
      cols.forEach(c => { html += `<th>${esc(c.label)}</th>`; });
      html += '</tr></thead><tbody>';
      regionRows.forEach(r => {
        html += '<tr>';
        cols.forEach(c => { html += `<td>${esc(String(c.key ? r[c.key] : c.fn(r)))}</td>`; });
        html += '</tr>';
      });
      html += '</tbody></table>';
    }
    document.getElementById('variant-c').innerHTML = html;
  }
}

async function loadEmbeds() {
  const data = await loadJSON(`${API}/all`);
  const top = data.slice(0, 3);

  // Option 1: region emoji in title prefix
  const emb1 = top.map(r => {
    const title = r.title.length > 80 ? r.title.slice(0, 80) + '…' : r.title;
    return `[${regionEmoji(r.region)} ${title}](${r.uid}) — ${r.company}`;
  }).join('\n');
  document.getElementById('embed-1').textContent = emb1;

  // Option 2: region as a field
  const emb2 = top.map(r => {
    return `Title: ${r.title}\nCompany: ${r.company}\nRegion: ${r.region}\nLocations: ${(r.locations||[]).join(', ')}\nScore: ${r.score}`;
  }).join('\n---\n');
  document.getElementById('embed-2').textContent = emb2;

  // Option 3: region in digest row
  const emb3 = top.map(r => {
    const title = r.title.length > 50 ? r.title.slice(0, 50) + '…' : r.title;
    return `${regionTag(r.region)} ${title} — ${r.company} (Score ${r.score})`;
  }).join('\n');
  document.getElementById('embed-3').textContent = emb3;
}

function regionEmoji(region) {
  return {'US': '🇺🇸', 'UK': '🇬🇧'}[region] || '🌐';
}

function regionTag(region) {
  return regionEmoji(region) + ' ' + region;
}

async function loadBatches() {
  const data = await loadJSON(`${API}/all`);
  const sorted = data.sort((a, b) => b.score - a.score || a.age_days - b.age_days);

  // Interleaved
  const inter = sorted.slice(0, 10).map(r =>
    `${regionTag(r.region)} [${r.score}] ${r.company} — ${r.title}`
  ).join('\n');
  document.getElementById('batch-interleaved').textContent = inter;

  // Sectioned
  const us = sorted.filter(r => r.region === 'US').slice(0, 5);
  const uk = sorted.filter(r => r.region === 'UK').slice(0, 5);
  let sec = '🇺🇸 US:\n';
  sec += us.map(r => `  [${r.score}] ${r.company} — ${r.title}`).join('\n');
  sec += '\n🇬🇧 UK:\n';
  sec += uk.map(r => `  [${r.score}] ${r.company} — ${r.title}`).join('\n');
  document.getElementById('batch-sectioned').textContent = sec;
}

// Load everything on page load
loadView('mixed');
loadEmbeds();
loadBatches();

// Load stats
loadJSON(`${API}/stats`).then(stats => {
  document.getElementById('stats').innerHTML = `
    <div class="stat"><div class="num">${stats.us_records}</div><div class="label">US Records</div></div>
    <div class="stat"><div class="num">${stats.uk_records}</div><div class="label">UK Records</div></div>
    <div class="stat"><div class="num">${stats.total}</div><div class="label">Total</div></div>
  `;
});
</script>
</body>
</html>"""


def main():
    port = 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), PrototypeHandler)
    print(f"Region presentation prototype on http://127.0.0.1:{port}")
    print("Variants: / (mixed), /api/us, /api/uk, /api/all, /api/stats")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()