(function () {
  "use strict";

  var Viewer = (window.Viewer = window.Viewer || {});

  function sanitizePart(s) {
    return String(s || "").replace(/[^a-zA-Z0-9_-]+/g, "-").replace(/^-+|-+$/g, "");
  }

  function money(v) {
    if (v === null || v === undefined || v === "") return "";
    var n = Number(v);
    return isFinite(n) ? n.toFixed(2) : String(v);
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
  function renderInvoice(containers, ctx) {
    var jd = ctx.jsonData || {};

    if (jd.error) {
      var banner = document.createElement("div");
      banner.className = "error-banner";
      banner.textContent = "Extraction error: " + jd.error;
      containers.headerEl.appendChild(banner);
    }

    var extraNode = buildMultiDetails("invoice", jd.multipleInvoices);

    var kvHost = document.createElement("div");
    containers.headerEl.appendChild(kvHost);
    Viewer.kv.renderHeader(kvHost, {
      items: [
        { label: "Date of Issue", value: jd.dateOfIssue },
        { label: "Invoice Date", value: jd.invoiceDate },
        { label: "Invoice Number", value: jd.invoiceNum },
        { label: "Currency", value: jd.invoiceCurrency },
        { label: "Total Line Items", value: jd.totalLineItems },
        { label: "Total Qty", value: jd.totalQty },
        { label: "Total Amount", value: money(jd.totalAmount) },
        { label: "Incoterms", value: jd.incoterms },
        { label: "Country of Origin", value: jd.countryOfOrigin },
        { label: "Multiple Invoices?", value: jd.isMultipleInvoices ? "Yes" : "No" },
      ],
      extraNode: extraNode,
      subsections: [
        addressSubsection("Issue From", jd.issueFrom),
        addressSubsection("Issue To", jd.issueTo),
      ].filter(Boolean),
    });

    var detailTitle = document.createElement("h3");
    detailTitle.className = "section-title";
    detailTitle.textContent = "Invoice Items";
    containers.detailEl.appendChild(detailTitle);

    var tableHost = document.createElement("div");
    containers.detailEl.appendChild(tableHost);

    var columns = [
      { key: "lineNum", label: "#", type: "number" },
      { key: "qty", label: "Qty", type: "number" },
      { key: "code", label: "Code", type: "string" },
      { key: "desc", label: "Description", type: "string" },
      { key: "remark", label: "Remark", type: "string" },
      { key: "unitPrice", label: "Unit Price", type: "number", formatter: money },
      { key: "amount", label: "Amount", type: "number", formatter: money },
      { key: "PONum", label: "PO Number", type: "string" },
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
      rows: Array.isArray(jd.invoiceItems) ? jd.invoiceItems : [],
      csvFilenameBase: "invoiceItems" + (jd.invoiceNum ? "_" + sanitizePart(jd.invoiceNum) : ""),
      emptyMessage: "No invoice items.",
    });
  }

  Viewer.renderInvoice = renderInvoice;
})();
