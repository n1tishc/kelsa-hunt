const PAGE_SIZE = 100;

const state = {
  records: [],
  query: "",
  status: "open",
  source: "all",
  score: "3+",
  page: 1,
};

const byId = (id) => document.getElementById(id);
const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

function formatDate(seconds) {
  if (!seconds) return "—";
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(seconds * 1000));
}

function scoreBadge(score) {
  const band = score >= 10 ? 10 : score >= 5 ? 5 : score >= 3 ? 3 : 0;
  return `<span class="score score-${band}">${score}</span>`;
}

function roleCell(record) {
  const title = escapeHtml(record.title || "Untitled role");
  if (!record.url) return title;
  return `<a href="${escapeHtml(record.url)}" target="_blank" rel="noopener noreferrer">${title}</a>`;
}

function recordRow(record) {
  return `<tr>
    <td>${scoreBadge(record.score)}</td>
    <td><span class="status ${record.status}">${record.status}</span></td>
    <td class="company">${escapeHtml(record.company || "—")}</td>
    <td>${roleCell(record)}</td>
    <td>${escapeHtml((record.locations || []).join(" · ") || "—")}</td>
    <td>${escapeHtml(record.source || "—")}</td>
    <td>${formatDate(record.posted)}</td>
    <td>${formatDate(record.first_seen)}</td>
    <td>${formatDate(record.closed_at)}</td>
  </tr>`;
}

function render() {
  const matches = LedgerFilters.filterRecords(state.records, state);
  const pageCount = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
  state.page = Math.min(state.page, pageCount);
  const start = (state.page - 1) * PAGE_SIZE;
  const visible = matches.slice(start, start + PAGE_SIZE);
  const archiveOpen = state.records.filter((record) => record.status === "open").length;

  byId("matching-count").textContent = matches.length.toLocaleString();
  byId("open-count").textContent = archiveOpen.toLocaleString();
  byId("closed-count").textContent = (state.records.length - archiveOpen).toLocaleString();
  byId("company-count").textContent = new Set(matches.map((record) => record.company)).size.toLocaleString();
  byId("range").textContent = matches.length
    ? `Showing ${start + 1}–${start + visible.length} of ${matches.length.toLocaleString()}`
    : "No Records match these filters";
  byId("page-label").textContent = `Page ${state.page} of ${pageCount}`;
  byId("previous").disabled = state.page === 1;
  byId("next").disabled = state.page === pageCount;
  byId("records").innerHTML = visible.length
    ? visible.map(recordRow).join("")
    : '<tr><td colspan="9" class="empty">Try a broader search or filter.</td></tr>';
}

function resetPageAndRender() {
  state.page = 1;
  render();
}

function bindControls() {
  byId("search").addEventListener("input", (event) => {
    state.query = event.target.value;
    resetPageAndRender();
  });
  for (const [id, key] of [
    ["status-filter", "status"],
    ["source-filter", "source"],
    ["score-filter", "score"],
  ]) {
    byId(id).addEventListener("change", (event) => {
      state[key] = event.target.value;
      resetPageAndRender();
    });
  }
  byId("previous").addEventListener("click", () => {
    state.page -= 1;
    render();
  });
  byId("next").addEventListener("click", () => {
    state.page += 1;
    render();
  });
}

function populateSources() {
  const sources = [...new Set(state.records.map((record) => record.source).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right));
  byId("source-filter").insertAdjacentHTML(
    "beforeend",
    sources.map((source) => `<option value="${escapeHtml(source)}">${escapeHtml(source)}</option>`).join(""),
  );
}

async function loadLedger() {
  try {
    const response = await fetch("jobs.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    state.records = payload.records || [];
    state.status = payload.defaults?.status || "open";
    state.score = payload.defaults?.score || "3+";
    byId("status-filter").value = state.status;
    byId("score-filter").value = state.score;
    byId("canonical-updated").textContent = payload.canonical_updated
      ? `Canonical Store · ${new Date(payload.canonical_updated).toLocaleString()}`
      : "Canonical Store snapshot";
    populateSources();
    render();
  } catch (error) {
    byId("records").innerHTML = `<tr><td colspan="9" class="empty">Could not load the ledger: ${escapeHtml(error.message)}</td></tr>`;
    byId("range").textContent = "Derived View unavailable";
  }
}

bindControls();
loadLedger();
