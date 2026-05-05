// Tiny URL-query helper used by every detail page.
// Usage:  const id = window.RRD.query('id');
(function () {
  const RRD = (window.RRD = window.RRD || {});
  RRD.query = function (key, fallback) {
    const params = new URLSearchParams(window.location.search);
    return params.has(key) ? params.get(key) : (fallback ?? null);
  };
  RRD.findById = function (collection, id) {
    if (!Array.isArray(collection) || id == null) return null;
    return collection.find((row) => String(row.id) === String(id)) || null;
  };
})();
