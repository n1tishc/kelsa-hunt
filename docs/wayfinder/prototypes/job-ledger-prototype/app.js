const VARIANTS = [
  { key: "A", name: "Spreadsheet ledger" },
  { key: "B", name: "Archive inspector" },
  { key: "C", name: "Market timeline" },
];

const state = {
  data: [],
  query: "",
  state: "open",
  source: "all",
  score: "3+",
  page: 1,
  pageSize: 100,
  selected: null,
};

const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

const formatDate = (seconds) =>
  seconds
    ? new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      }).format(new Date(seconds * 1000))
    : "Unknown";

const compact = (value) =>
  new Intl.NumberFormat("en-US", { notation: "compact" }).format(value);

function activeVariant() {
  const candidate = new URLSearchParams(location.search).get("variant") || "A";
  return VARIANTS.some((variant) => variant.key === candidate)
    ? candidate
    : "A";
}

function setVariant(key) {
  const url = new URL(location.href);
  url.searchParams.set("variant", key);
  history.replaceState({}, "", url);
  render();
}

function cycleVariant(direction) {
  const index = VARIANTS.findIndex((item) => item.key === activeVariant());
  const next = (index + direction + VARIANTS.length) % VARIANTS.length;
  setVariant(VARIANTS[next].key);
}

function filteredRows() {
  const needle = state.query.trim().toLowerCase();
  return state.data.filter((row) => {
    const text = `${row.company} ${row.title} ${row.location} ${row.source}`.toLowerCase();
    const scoreMatches =
      state.score === "all" ||
      (state.score === "0" ? row.score === 0 : row.score >= Number(state.score.slice(0, -1)));
    return (
      (!needle || text.includes(needle)) &&
      (state.state === "all" || row.state === state.state) &&
      (state.source === "all" || row.source === state.source) &&
      scoreMatches
    );
  });
}

function summary(rows = state.data) {
  return {
    total: rows.length,
    open: rows.filter((row) => row.state === "open").length,
    closed: rows.filter((row) => row.state === "closed").length,
    candidates: rows.filter(
      (row) => row.state === "open" && row.score >= 5 && (row.age_days ?? 999) <= 21,
    ).length,
    companies: new Set(rows.map((row) => row.company)).size,
  };
}

function filterControls() {
  const sources = [...new Set(state.data.map((row) => row.source))].sort();
  return `
    <label class="search-control">
      <span>Search</span>
      <input id="query" value="${escapeHtml(state.query)}"
        placeholder="Company, title, location…" autocomplete="off" />
    </label>
    <label>
      <span>Status</span>
      <select id="state-filter">
        ${["all", "open", "closed"]
          .map((value) => `<option ${state.state === value ? "selected" : ""}>${value}</option>`)
          .join("")}
      </select>
    </label>
    <label>
      <span>Source</span>
      <select id="source-filter">
        <option value="all">all</option>
        ${sources
          .map(
            (value) =>
              `<option ${state.source === value ? "selected" : ""}>${escapeHtml(value)}</option>`,
          )
          .join("")}
      </select>
    </label>
    <label>
      <span>Score</span>
      <select id="score-filter">
        ${[
          ["3+", "3+ · plausible"],
          ["5+", "5+ · strong"],
          ["10+", "10+ · explicit"],
          ["all", "all scores"],
          ["0", "0 · unclassified"],
        ]
          .map(
            ([value, label]) =>
              `<option value="${value}" ${state.score === value ? "selected" : ""}>${label}</option>`,
          )
          .join("")}
      </select>
    </label>
  `;
}

function commonHeader(kicker, title, note) {
  return `
    <header class="page-header">
      <div>
        <div class="kicker">${kicker}</div>
        <h1>${title}</h1>
        <p>${note}</p>
      </div>
      <div class="archive-badge"><span></span>US archive · read only</div>
    </header>
  `;
}

function scoreBadge(score) {
  const band = score >= 10 ? 10 : score >= 5 ? 5 : score >= 3 ? 3 : 0;
  return `<span class="score score-${band}">${score}</span>`;
}

function variantA() {
  const rows = filteredRows();
  const stats = summary(rows);
  const pages = Math.max(1, Math.ceil(rows.length / state.pageSize));
  state.page = Math.min(state.page, pages);
  const start = (state.page - 1) * state.pageSize;
  const visible = rows.slice(start, start + state.pageSize);
  return `
    <main class="variant-a">
      ${commonHeader(
        "Kelsa Hunt / Canonical Record",
        "Job ledger",
        "Every explicitly US-eligible role ever observed, in one auditable table.",
      )}
      <section class="stat-strip">
        <div><strong>${compact(stats.total)}</strong><span>matching records</span></div>
        <div><strong>${compact(stats.open)}</strong><span>open</span></div>
        <div><strong>${compact(stats.closed)}</strong><span>closed</span></div>
        <div><strong>${compact(stats.companies)}</strong><span>companies</span></div>
      </section>
      <section class="sheet-shell">
        <div class="filter-row">${filterControls()}</div>
        <div class="table-meta">
          <span>Showing ${start + 1}–${Math.min(start + state.pageSize, rows.length)}
          of ${rows.length.toLocaleString()}</span>
          <span>Page ${state.page} of ${pages}</span>
        </div>
        <div class="table-scroll">
          <table>
            <thead><tr>
              <th>Score</th><th>Status</th><th>Company</th><th>Role</th>
              <th>Location</th><th>Source</th><th>Posted</th><th>First seen</th>
            </tr></thead>
            <tbody>
              ${visible
                .map(
                  (row) => `<tr>
                    <td>${scoreBadge(row.score)}</td>
                    <td><span class="status ${row.state}">${row.state}</span></td>
                    <td class="company">${escapeHtml(row.company)}</td>
                    <td><a href="${escapeHtml(row.url)}" target="_blank">${escapeHtml(row.title)}</a></td>
                    <td>${escapeHtml(row.location)}</td>
                    <td>${escapeHtml(row.source)}</td>
                    <td>${formatDate(row.posted)}</td>
                    <td>${formatDate(row.first_seen)}</td>
                  </tr>`,
                )
                .join("")}
            </tbody>
          </table>
        </div>
        <div class="pager">
          <button id="prev-page" ${state.page === 1 ? "disabled" : ""}>← Previous</button>
          <button id="next-page" ${state.page === pages ? "disabled" : ""}>Next →</button>
        </div>
      </section>
    </main>`;
}

function variantB() {
  const rows = filteredRows();
  const stats = summary();
  if (!state.selected || !rows.some((row) => row.uid === state.selected)) {
    state.selected = rows[0]?.uid;
  }
  const selected = rows.find((row) => row.uid === state.selected);
  const recent = rows.slice(0, 80);
  return `
    <main class="variant-b">
      <aside class="archive-sidebar">
        <div class="sidebar-brand"><span>KH</span><strong>Kelsa Archive</strong></div>
        <nav>
          <button data-view-state="all" class="${state.state === "all" ? "active" : ""}">
            <span>All records</span><b>${compact(stats.total)}</b>
          </button>
          <button data-view-state="open" class="${state.state === "open" ? "active" : ""}">
            <span>Currently open</span><b>${compact(stats.open)}</b>
          </button>
          <button data-view-state="closed" class="${state.state === "closed" ? "active" : ""}">
            <span>Historical</span><b>${compact(stats.closed)}</b>
          </button>
        </nav>
        <div class="sidebar-note">
          <span>Read-only archive</span>
          <p>Application activity never appears in this public view.</p>
        </div>
      </aside>
      <section class="archive-results">
        <div class="archive-search">
          <div>
            <div class="kicker">Complete US job history</div>
            <h1>Find any role we’ve seen</h1>
          </div>
          <input id="query" value="${escapeHtml(state.query)}"
            placeholder="Search ${state.data.length.toLocaleString()} records…" autocomplete="off" />
        </div>
        <div class="result-meta">${rows.length.toLocaleString()} results · newest observations first</div>
        <div class="result-list">
          ${recent
            .map(
              (row) => `<button class="result-item ${row.uid === state.selected ? "selected" : ""}"
                data-select="${escapeHtml(row.uid)}">
                <span class="result-score">${scoreBadge(row.score)}</span>
                <span class="result-copy">
                  <strong>${escapeHtml(row.title)}</strong>
                  <span>${escapeHtml(row.company)} · ${escapeHtml(row.location)}</span>
                </span>
                <span class="result-date">${formatDate(row.posted || row.first_seen)}</span>
              </button>`,
            )
            .join("")}
        </div>
      </section>
      <aside class="record-inspector">
        ${
          selected
            ? `<div class="inspector-top">
                <span class="status ${selected.state}">${selected.state}</span>
                ${scoreBadge(selected.score)}
              </div>
              <h2>${escapeHtml(selected.title)}</h2>
              <h3>${escapeHtml(selected.company)}</h3>
              <dl>
                <div><dt>Location</dt><dd>${escapeHtml(selected.location)}</dd></div>
                <div><dt>Source</dt><dd>${escapeHtml(selected.source)}</dd></div>
                <div><dt>Posted</dt><dd>${formatDate(selected.posted)}</dd></div>
                <div><dt>First observed</dt><dd>${formatDate(selected.first_seen)}</dd></div>
                <div><dt>Classification</dt><dd>${escapeHtml(selected.reason || "No positive signal")}</dd></div>
                <div><dt>Discord</dt><dd>${selected.notified ? "Notified" : "Not notified"}</dd></div>
              </dl>
              <a class="primary-link" href="${escapeHtml(selected.url)}" target="_blank">Open original role ↗</a>`
            : `<div class="empty">No record selected.</div>`
        }
      </aside>
    </main>`;
}

function monthKey(seconds) {
  if (!seconds) return "Unknown";
  const date = new Date(seconds * 1000);
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
}

function variantC() {
  const rows = filteredRows();
  const stats = summary(rows);
  const months = new Map();
  rows.forEach((row) => {
    const key = monthKey(row.posted || row.first_seen);
    months.set(key, (months.get(key) || 0) + 1);
  });
  const bars = [...months.entries()]
    .filter(([key]) => key !== "Unknown")
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-18);
  const max = Math.max(...bars.map(([, count]) => count), 1);
  const companies = [...rows.reduce((map, row) => map.set(row.company, (map.get(row.company) || 0) + 1), new Map())]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);
  return `
    <main class="variant-c">
      ${commonHeader(
        "Kelsa Hunt / Historical Observatory",
        "The market we’ve witnessed",
        "A permanent US record viewed as history first, individual jobs second.",
      )}
      <section class="timeline-controls">${filterControls()}</section>
      <section class="timeline-grid">
        <article class="history-chart">
          <div class="section-heading"><div><span>Observed postings</span><h2>Archive timeline</h2></div>
            <strong>${stats.total.toLocaleString()} records</strong></div>
          <div class="bars">
            ${bars
              .map(
                ([month, count]) => `<div class="bar-wrap" title="${month}: ${count}">
                  <div class="bar" style="height:${Math.max(3, (count / max) * 100)}%"></div>
                  <span>${month.slice(2)}</span>
                </div>`,
              )
              .join("")}
          </div>
        </article>
        <article class="market-summary">
          <span>Archive composition</span><h2>What’s inside</h2>
          <div class="donut-row">
            <div class="donut" style="--open:${(stats.open / Math.max(stats.total, 1)) * 360}deg">
              <strong>${Math.round((stats.open / Math.max(stats.total, 1)) * 100)}%</strong><span>open</span>
            </div>
            <div class="summary-list">
              <div><i class="open-dot"></i><span>Open</span><b>${stats.open.toLocaleString()}</b></div>
              <div><i class="closed-dot"></i><span>Historical</span><b>${stats.closed.toLocaleString()}</b></div>
              <div><i class="candidate-dot"></i><span>Current Candidates</span><b>${stats.candidates}</b></div>
            </div>
          </div>
        </article>
        <article class="company-rank">
          <span>Largest histories</span><h2>Top companies</h2>
          <ol>${companies
            .map(
              ([company, count]) =>
                `<li><span>${escapeHtml(company)}</span><b>${count.toLocaleString()}</b></li>`,
            )
            .join("")}</ol>
        </article>
        <article class="recent-log">
          <div class="section-heading"><div><span>Record log</span><h2>Recently observed</h2></div></div>
          <div>
            ${rows
              .slice(0, 12)
              .map(
                (row) => `<a href="${escapeHtml(row.url)}" target="_blank">
                  <time>${formatDate(row.first_seen)}</time>
                  <span><strong>${escapeHtml(row.company)}</strong>${escapeHtml(row.title)}</span>
                  <em class="${row.state}">${row.state}</em>
                </a>`,
              )
              .join("")}
          </div>
        </article>
      </section>
    </main>`;
}

function switcher() {
  const current = VARIANTS.find((item) => item.key === activeVariant());
  return `<div class="prototype-switcher" aria-label="Prototype variants">
    <button id="variant-prev" aria-label="Previous variant">←</button>
    <span><small>THROWAWAY PROTOTYPE</small><strong>${current.key} — ${current.name}</strong></span>
    <button id="variant-next" aria-label="Next variant">→</button>
  </div>`;
}

function bindControls() {
  const query = document.querySelector("#query");
  query?.addEventListener("input", (event) => {
    state.query = event.target.value;
    state.page = 1;
    render(query.selectionStart);
  });
  document.querySelector("#state-filter")?.addEventListener("change", (event) => {
    state.state = event.target.value;
    state.page = 1;
    render();
  });
  document.querySelector("#source-filter")?.addEventListener("change", (event) => {
    state.source = event.target.value;
    state.page = 1;
    render();
  });
  document.querySelector("#score-filter")?.addEventListener("change", (event) => {
    state.score = event.target.value;
    state.page = 1;
    render();
  });
  document.querySelector("#prev-page")?.addEventListener("click", () => {
    state.page -= 1;
    render();
  });
  document.querySelector("#next-page")?.addEventListener("click", () => {
    state.page += 1;
    render();
  });
  document.querySelectorAll("[data-view-state]").forEach((button) =>
    button.addEventListener("click", () => {
      state.state = button.dataset.viewState;
      render();
    }),
  );
  document.querySelectorAll("[data-select]").forEach((button) =>
    button.addEventListener("click", () => {
      state.selected = button.dataset.select;
      render();
    }),
  );
  document.querySelector("#variant-prev")?.addEventListener("click", () => cycleVariant(-1));
  document.querySelector("#variant-next")?.addEventListener("click", () => cycleVariant(1));
}

function render(caret) {
  const app = document.querySelector("#app");
  const variant = activeVariant();
  app.innerHTML =
    (variant === "A" ? variantA() : variant === "B" ? variantB() : variantC()) + switcher();
  bindControls();
  if (typeof caret === "number") {
    const query = document.querySelector("#query");
    query?.focus();
    query?.setSelectionRange(caret, caret);
  }
}

window.addEventListener("keydown", (event) => {
  if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
  const tag = document.activeElement?.tagName;
  if (["INPUT", "TEXTAREA", "SELECT"].includes(tag) || document.activeElement?.isContentEditable) return;
  cycleVariant(event.key === "ArrowLeft" ? -1 : 1);
});
window.addEventListener("popstate", render);

fetch("/prototype-data.json")
  .then((response) => response.json())
  .then((payload) => {
    state.data = payload.rows;
    render();
  })
  .catch((error) => {
    document.querySelector("#app").innerHTML = `<div class="loading">Could not load prototype data: ${escapeHtml(error)}</div>`;
  });
