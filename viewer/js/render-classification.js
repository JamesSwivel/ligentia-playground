(function () {
  "use strict";

  var Viewer = (window.Viewer = window.Viewer || {});

  function joinPageNums(v) {
    return Array.isArray(v) ? v.join(", ") : "";
  }

  // containers: { detailEl }, ctx: { jsonData }
  function renderClassification(containers, ctx) {
    var jd = ctx.jsonData || {};
    var groups = Array.isArray(jd.classificationGroups) ? jd.classificationGroups : [];
    var perPage = Array.isArray(jd.classifications) ? jd.classifications : [];

    var pageCount = perPage.length || groups.reduce(function (sum, g) {
      return sum + (Array.isArray(g.pageNums) ? g.pageNums.length : 0);
    }, 0);

    var caption = document.createElement("div");
    caption.className = "section-caption";
    caption.textContent = groups.length + " classification group" + (groups.length === 1 ? "" : "s") +
      " across " + pageCount + " page" + (pageCount === 1 ? "" : "s") + ".";
    containers.detailEl.appendChild(caption);

    var primaryTitle = document.createElement("h3");
    primaryTitle.className = "section-title";
    primaryTitle.textContent = "Classification Groups";
    containers.detailEl.appendChild(primaryTitle);

    var primaryHost = document.createElement("div");
    containers.detailEl.appendChild(primaryHost);

    var primaryColumns = [
      { key: "docTypeGroupId", label: "Group ID", type: "string" },
      { key: "docType", label: "Doc Type", type: "string" },
      { key: "layout", label: "Layout", type: "string" },
      { key: "pageNums", label: "Pages", type: "string", formatter: joinPageNums },
      { key: "score", label: "Score", type: "number" },
      { key: "reason", label: "Reason", type: "string" },
    ];

    var primaryTable = Viewer.createTable(primaryHost, {
      columns: primaryColumns,
      rows: groups,
      csvFilenameBase: "classificationGroups",
      emptyMessage: "No classification groups.",
    });

    var secondaryTable = null;
    if (perPage.length) {
      var details = document.createElement("details");
      var summary = document.createElement("summary");
      summary.textContent = "Per-page classifications (" + perPage.length + ")";
      details.appendChild(summary);

      var secondaryHost = document.createElement("div");
      secondaryHost.style.marginTop = "10px";
      details.appendChild(secondaryHost);
      containers.detailEl.appendChild(details);

      var secondaryColumns = [
        { key: "pageNum", label: "Page #", type: "number" },
        { key: "docType", label: "Doc Type", type: "string" },
        { key: "layout", label: "Layout", type: "string" },
        { key: "docNum", label: "Doc #", type: "string" },
        { key: "docTypeGroupId", label: "Group ID", type: "string" },
        { key: "score", label: "Score", type: "number" },
        { key: "reason", label: "Reason", type: "string" },
      ];

      secondaryTable = Viewer.createTable(secondaryHost, {
        columns: secondaryColumns,
        rows: perPage,
        csvFilenameBase: "classifications",
        emptyMessage: "No per-page classifications.",
      });
    }

    return { primaryTable: primaryTable, secondaryTable: secondaryTable };
  }

  Viewer.renderClassification = renderClassification;
})();
