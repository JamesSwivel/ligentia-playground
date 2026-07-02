(function () {
  "use strict";

  // Pure function, no DOM access. Order matters: invoiceDate -> packingListDate ->
  // classificationGroups array -> unknown, per product spec.
  function detectDocType(parsed) {
    var jd = (parsed && parsed.result && parsed.result.jsonData) || {};
    if (jd.invoiceDate !== undefined) return "invoice";
    if (jd.packingListDate !== undefined) return "packingList";
    if (Array.isArray(jd.classificationGroups)) return "docClassification";
    return "unknown";
  }

  window.Viewer = window.Viewer || {};
  window.Viewer.detectDocType = detectDocType;
})();
