(function exposeLedgerFilters(root, factory) {
  const filters = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = filters;
  root.LedgerFilters = filters;
})(typeof globalThis !== "undefined" ? globalThis : window, function ledgerFilters() {
  function scoreMatches(record, scoreFilter) {
    if (scoreFilter === "all") return true;
    if (scoreFilter === "0") return record.score === 0;
    return record.score >= Number(scoreFilter.slice(0, -1));
  }

  function filterRecords(records, state) {
    const needle = (state.query || "").trim().toLocaleLowerCase();
    return records
      .filter((record) => {
        const searchable = [record.company, record.title, ...(record.locations || [])]
          .join(" ")
          .toLocaleLowerCase();
        return (
          (!needle || searchable.includes(needle)) &&
          (state.status === "all" || record.status === state.status) &&
          (state.source === "all" || record.source === state.source) &&
          scoreMatches(record, state.score)
        );
      })
      .sort((left, right) => {
        const freshness = (right.posted || right.first_seen || 0) -
          (left.posted || left.first_seen || 0);
        return freshness || (left.uid || "").localeCompare(right.uid || "");
      });
  }

  return { filterRecords };
});
