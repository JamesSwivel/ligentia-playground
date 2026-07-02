(function () {
  "use strict";

  function stripHtml(html) {
    var div = document.createElement("div");
    div.innerHTML = String(html == null ? "" : html);
    return div.textContent || div.innerText || "";
  }

  function csvEscape(value) {
    var s = value == null ? "" : String(value);
    if (/[",\r\n]/.test(s)) {
      s = '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
  }

  function defaultCellText(col, value, row) {
    if (col.type === "badge") {
      return JSON.stringify(value == null ? {} : value);
    }
    if (col.csvFormatter) return col.csvFormatter(value, row);
    if (col.formatter) return stripHtml(col.formatter(value, row));
    if (value == null) return "";
    if (col.type === "number") {
      var n = Number(value);
      return isFinite(n) ? String(n) : String(value);
    }
    if (col.type === "boolean") return value ? "Yes" : "No";
    return String(value);
  }

  function timestamp() {
    var d = new Date();
    function pad(n) {
      return n < 10 ? "0" + n : "" + n;
    }
    return (
      d.getFullYear() +
      pad(d.getMonth() + 1) +
      pad(d.getDate()) +
      "-" +
      pad(d.getHours()) +
      pad(d.getMinutes()) +
      pad(d.getSeconds())
    );
  }

  // columns: ColumnDef[], rows: object[] (already filtered+sorted / the currently
  // displayed set), filenameBase: string (should already include any doc id, e.g.
  // "invoiceItems_BV2503-0030" - this function only appends a timestamp + extension).
  function exportRowsToCsv(columns, rows, filenameBase) {
    var lines = [];
    lines.push(columns.map(function (c) { return csvEscape(c.label); }).join(","));
    rows.forEach(function (row) {
      var cells = columns.map(function (col) {
        var value = row[col.key];
        return csvEscape(defaultCellText(col, value, row));
      });
      lines.push(cells.join(","));
    });
    var csvBody = lines.join("\r\n") + "\r\n";
    var bom = "﻿";
    var blob = new Blob([bom, csvBody], { type: "text/csv;charset=utf-8;" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = (filenameBase || "export") + "_" + timestamp() + ".csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 0);
  }

  window.Viewer = window.Viewer || {};
  window.Viewer.exportRowsToCsv = exportRowsToCsv;
})();
