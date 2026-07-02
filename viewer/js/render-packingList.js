(function () {
  "use strict";

  var Viewer = (window.Viewer = window.Viewer || {});

  function sanitizePart(s) {
    return String(s || "").replace(/[^a-zA-Z0-9_-]+/g, "-").replace(/^-+|-+$/g, "");
  }

  function num3(v) {
    if (v === null || v === undefined || v === "") return "";
    var n = Number(v);
    return isFinite(n) ? n.toFixed(3) : String(v);
  }

  function addressSubsection(title, addr) {
    if (!addr || typeof addr !== "object") return null;
    return {
      title: title,
      items: [
        { label: "Company", value: addr.companyName },
        { label: "Address", value: addr.addressSingleLine },
        { label: "State", value: addr.state },
        { label: "Zip", value: addr.zip },
        { label: "Country", value: addr.country },
        { label: "Email", value: addr.email },
        { label: "Phone", value: addr.phone },
        { label: "Fax", value: addr.fax },
        { label: "Contact", value: addr.contactPerson },
        { label: "Tax ID", value: addr.taxID },
      ],
      collapsedItems: [{ label: "Raw address lines", value: addr.rawAddressLines }],
      collapsedLabel: "Raw address lines",
    };
  }

  function buildMultiDetails(label, arr) {
    if (!Array.isArray(arr) || arr.length === 0) return null;
    var det = document.createElement("details");
    det.className = "kv-collapsed";
    var sum = document.createElement("summary");
    sum.textContent = arr.length + " alternate " + label + (arr.length === 1 ? "" : "s") + " detected";
    det.appendChild(sum);
    arr.forEach(function (entry, i) {
      var pre = document.createElement("pre");
      pre.style.fontSize = "12px";
      pre.style.whiteSpace = "pre-wrap";
      pre.style.margin = "6px 0";
      pre.textContent = "#" + (i + 1) + ": " + JSON.stringify(entry, null, 2);
      det.appendChild(pre);
    });
    return det;
  }

  // containers: { headerEl, detailEl }, ctx: { jsonData }
  function renderPackingList(containers, ctx) {
    var jd = ctx.jsonData || {};

    if (jd.error) {
      var banner = document.createElement("div");
      banner.className = "error-banner";
      banner.textContent = "Extraction error: " + jd.error;
      containers.headerEl.appendChild(banner);
    }

    var extraNode = buildMultiDetails("packing list", jd.multiplePackingLists);

    var kvHost = document.createElement("div");
    containers.headerEl.appendChild(kvHost);
    Viewer.kv.renderHeader(kvHost, {
      items: [
        { label: "Date of Issue", value: jd.dateOfIssue },
        { label: "Packing List Layout", value: jd.packingListLayout },
        { label: "Packing List Number", value: jd.packingListNum },
        { label: "Invoice Number", value: jd.invoiceNum },
        { label: "PO Number", value: jd.PONum },
        { label: "Packing List Date", value: jd.packingListDate },
        { label: "Gross Weight", value: jd.totalGrossWeight != null ? jd.totalGrossWeight + " " + (jd.grossWeightUnit || "") : "" },
        { label: "Net Weight", value: jd.totalNetWeight != null ? jd.totalNetWeight + " " + (jd.grossWeightUnit || "") : "" },
        { label: "Total Line Items", value: jd.totalLineItems },
        { label: "Total Qty", value: jd.totalQty },
        { label: "Total Carton Qty", value: jd.totalCartonQty },
        { label: "Total CBM", value: jd.totalCbm },
        { label: "Incoterms", value: jd.incoterms },
        { label: "Country of Origin", value: jd.countryOfOrigin },
        { label: "Multiple Packing Lists?", value: jd.isMultiplePackingLists ? "Yes" : "No" },
      ],
      extraNode: extraNode,
      subsections: [
        addressSubsection("Issue From", jd.issueFrom),
        addressSubsection("Issue To", jd.issueTo),
      ].filter(Boolean),
    });

    var detailTitle = document.createElement("h3");
    detailTitle.className = "section-title";
    detailTitle.textContent = "Packing List Items";
    containers.detailEl.appendChild(detailTitle);

    var tableHost = document.createElement("div");
    containers.detailEl.appendChild(tableHost);

    var columns = [
      { key: "lineNum", label: "#", type: "number" },
      { key: "lineNumParent", label: "Parent #", type: "number" },
      { key: "PONum", label: "PO Number", type: "string" },
      { key: "invoiceNum", label: "Invoice Number", type: "string" },
      { key: "code", label: "Code", type: "string" },
      { key: "desc", label: "Description", type: "string" },
      { key: "remark", label: "Remark", type: "string" },
      { key: "qty", label: "Qty", type: "number" },
      { key: "qtyPerCarton", label: "Qty/Carton", type: "number" },
      { key: "cartonQty", label: "Carton Qty", type: "number" },
      { key: "grossWeight", label: "Gross Wt", type: "number", formatter: num3 },
      { key: "netWeight", label: "Net Wt", type: "number", formatter: num3 },
      { key: "cbm", label: "CBM", type: "number", formatter: num3 },
      { key: "containerType", label: "Container Type", type: "string" },
      { key: "containerNum", label: "Container #", type: "string" },
      { key: "containerSealNum", label: "Seal #", type: "string" },
      { key: "packageStartNum", label: "Pkg Start", type: "number" },
      { key: "packageEndNum", label: "Pkg End", type: "number" },
      { key: "totalPackages", label: "Total Pkgs", type: "number" },
      {
        key: "extra",
        label: "Extra",
        type: "badge",
        sortable: false,
        onBadgeClick: function (row) {
          Viewer.modal.openKeyValue("Extra Fields (Line " + row.lineNum + ")", row.extra || {});
        },
      },
    ];

    return Viewer.createTable(tableHost, {
      columns: columns,
      rows: Array.isArray(jd.packingListItems) ? jd.packingListItems : [],
      csvFilenameBase: "packingListItems" + (jd.packingListNum ? "_" + sanitizePart(jd.packingListNum) : jd.invoiceNum ? "_" + sanitizePart(jd.invoiceNum) : ""),
      emptyMessage: "No packing list items.",
    });
  }

  Viewer.renderPackingList = renderPackingList;
})();
