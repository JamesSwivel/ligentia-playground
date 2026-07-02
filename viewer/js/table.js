(function () {
  "use strict";

  var Viewer = (window.Viewer = window.Viewer || {});

  // ---- default per-type formatters / comparators -------------------------

  function defaultFormatter(type) {
    switch (type) {
      case "number":
        return function (v) {
          if (v === null || v === undefined || v === "") return "";
          var n = Number(v);
          return isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: 6 }) : String(v);
        };
      case "boolean":
        return function (v) {
          return v ? "Yes" : "No";
        };
      case "date":
      case "string":
      default:
        return function (v) {
          return v === null || v === undefined ? "" : String(v);
        };
    }
  }

  function defaultComparator(type) {
    switch (type) {
      case "number":
        return function (a, b) {
          return Number(a) - Number(b);
        };
      case "boolean":
        return function (a, b) {
          return (a ? 1 : 0) - (b ? 1 : 0);
        };
      case "date":
        return function (a, b) {
          var ta = Date.parse(a);
          var tb = Date.parse(b);
          if (isNaN(ta) || isNaN(tb)) return a < b ? -1 : a > b ? 1 : 0;
          return ta - tb;
        };
      case "string":
      default:
        return function (a, b) {
          return String(a).localeCompare(String(b), undefined, { sensitivity: "base" });
        };
    }
  }

  function isMissing(value, type) {
    if (value === null || value === undefined || value === "") return true;
    if (type === "number") return !isFinite(Number(value));
    return false;
  }

  // ---- table instance ------------------------------------------------------

  function createTable(containerEl, options) {
    var columns = options.columns;
    var originalEntries = (options.rows || []).map(function (row, idx) {
      return { row: row, idx: idx };
    });
    var csvFilenameBase = options.csvFilenameBase || "export";
    var emptyMessage = options.emptyMessage || "No rows.";

    var state = {
      filters: new Map(),
      sortMode: "none", // 'none' | 'simple' | 'advanced'
      simpleSort: null, // { key, dir }
      advancedSort: [], // [{ key, dir }]
    };

    // ---- filtering ----

    function filterValue(col, row) {
      var value = row[col.key];
      if (col.type === "badge") return JSON.stringify(value == null ? {} : value);
      return String(value == null ? "" : value);
    }

    function matchesFilters(entry) {
      var matched = true;
      state.filters.forEach(function (text, key) {
        if (!matched || !text) return;
        var col = columnsByKey[key];
        if (!col) return;
        var haystack = filterValue(col, entry.row).toLowerCase();
        if (haystack.indexOf(text.toLowerCase()) === -1) matched = false;
      });
      return matched;
    }

    // ---- sorting ----

    function rowComparatorFor(col, dir) {
      var typeCmp = defaultComparator(col.type);
      var cmp = col.comparator || typeCmp;
      return function (entryA, entryB) {
        var a = entryA.row[col.key];
        var b = entryB.row[col.key];
        var aMissing = isMissing(a, col.type);
        var bMissing = isMissing(b, col.type);
        if (aMissing || bMissing) {
          if (aMissing && bMissing) return 0;
          return aMissing ? 1 : -1; // missing always sorts last, regardless of direction
        }
        var result = cmp(a, b);
        return dir === "desc" ? -result : result;
      };
    }

    function compositeComparator(sortList) {
      var comparators = sortList.map(function (s) {
        return rowComparatorFor(columnsByKey[s.key], s.dir);
      });
      return function (entryA, entryB) {
        for (var i = 0; i < comparators.length; i++) {
          var r = comparators[i](entryA, entryB);
          if (r !== 0) return r;
        }
        return entryA.idx - entryB.idx; // stable tie-break on original order
      };
    }

    // ---- pipeline ----

    var columnsByKey = {};
    columns.forEach(function (c) {
      columnsByKey[c.key] = c;
    });

    var displayedEntries = [];

    function recompute() {
      var filtered = originalEntries.filter(matchesFilters);
      if (state.sortMode === "simple" && state.simpleSort) {
        filtered = filtered
          .slice()
          .sort(compositeComparator([state.simpleSort]));
      } else if (state.sortMode === "advanced" && state.advancedSort.length) {
        filtered = filtered.slice().sort(compositeComparator(state.advancedSort));
      }
      displayedEntries = filtered;
      renderBody();
      renderHeaderBadges();
      renderChips();
      renderFooter();
    }

    function getDisplayedRows() {
      return displayedEntries.map(function (e) {
        return e.row;
      });
    }

    // ---- DOM scaffolding ----

    containerEl.innerHTML = "";

    var wrap = document.createElement("div");
    wrap.className = "table-wrap";

    var toolbar = document.createElement("div");
    toolbar.className = "table-toolbar";

    var advancedSortBtn = makeBtn("Advanced sort", openAdvancedSortPanel);
    var addFilterBtn = makeBtn("Add filter", openAddFilterPanel);
    var spacer = document.createElement("div");
    spacer.className = "table-toolbar__spacer";
    var resetSortBtn = makeBtn("Reset sorting", function () {
      state.sortMode = "none";
      state.simpleSort = null;
      state.advancedSort = [];
      recompute();
    });
    var resetFilterBtn = makeBtn("Reset filtering", function () {
      state.filters.clear();
      recompute();
    });
    var resetAllBtn = makeBtn("Reset all", function () {
      state.sortMode = "none";
      state.simpleSort = null;
      state.advancedSort = [];
      state.filters.clear();
      recompute();
    });
    var exportBtn = makeBtn("⬇ Export CSV", function () {
      Viewer.exportRowsToCsv(columns, getDisplayedRows(), csvFilenameBase);
    });
    exportBtn.classList.add("btn--primary");

    toolbar.appendChild(advancedSortBtn);
    toolbar.appendChild(addFilterBtn);
    toolbar.appendChild(spacer);
    toolbar.appendChild(resetSortBtn);
    toolbar.appendChild(resetFilterBtn);
    toolbar.appendChild(resetAllBtn);
    toolbar.appendChild(exportBtn);

    var chipsEl = document.createElement("div");
    chipsEl.className = "filter-chips";

    var scrollEl = document.createElement("div");
    scrollEl.className = "table-scroll";

    var table = document.createElement("table");
    table.className = "data-table";
    var thead = document.createElement("thead");
    var headRow = document.createElement("tr");
    var thByKey = {};
    columns.forEach(function (col) {
      var th = document.createElement("th");
      th.textContent = col.label;
      if (col.sortable !== false) {
        th.classList.add("sortable");
        th.addEventListener("click", function () {
          onHeaderClick(col);
        });
      }
      thByKey[col.key] = th;
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    var tbody = document.createElement("tbody");
    table.appendChild(thead);
    table.appendChild(tbody);
    scrollEl.appendChild(table);

    var footerEl = document.createElement("div");
    footerEl.className = "table-footer";

    wrap.appendChild(toolbar);
    wrap.appendChild(chipsEl);
    wrap.appendChild(scrollEl);
    wrap.appendChild(footerEl);
    containerEl.appendChild(wrap);

    function makeBtn(label, onClick) {
      var btn = document.createElement("button");
      btn.className = "btn";
      btn.textContent = label;
      btn.addEventListener("click", onClick);
      return btn;
    }

    // ---- rendering ----

    function renderHeaderBadges() {
      columns.forEach(function (col) {
        var th = thByKey[col.key];
        var existing = th.querySelector(".sort-badge");
        if (existing) existing.remove();
        if (state.sortMode === "simple" && state.simpleSort && state.simpleSort.key === col.key) {
          var badge = document.createElement("span");
          badge.className = "sort-badge";
          badge.textContent = state.simpleSort.dir === "asc" ? "▲" : "▼";
          th.appendChild(badge);
        }
      });
    }

    function renderChips() {
      chipsEl.innerHTML = "";
      state.filters.forEach(function (text, key) {
        var col = columnsByKey[key];
        if (!col) return;
        var chip = document.createElement("span");
        chip.className = "chip";
        var label = document.createElement("span");
        label.textContent = col.label + ": “" + text + "”";
        var removeBtn = document.createElement("button");
        removeBtn.innerHTML = "&times;";
        removeBtn.title = "Remove filter";
        removeBtn.addEventListener("click", function () {
          state.filters.delete(key);
          recompute();
        });
        chip.appendChild(label);
        chip.appendChild(removeBtn);
        chipsEl.appendChild(chip);
      });
    }

    function renderFooter() {
      footerEl.textContent =
        "Showing " + displayedEntries.length + " of " + originalEntries.length + " row" +
        (originalEntries.length === 1 ? "" : "s") +
        (state.filters.size ? " (filtered)" : "");
    }

    function renderBody() {
      tbody.innerHTML = "";
      if (displayedEntries.length === 0) {
        var tr = document.createElement("tr");
        var td = document.createElement("td");
        td.colSpan = columns.length;
        td.className = "table-empty";
        td.textContent = emptyMessage;
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
      }
      displayedEntries.forEach(function (entry) {
        var row = entry.row;
        var tr = document.createElement("tr");
        columns.forEach(function (col) {
          var td = document.createElement("td");
          if (col.type === "number") td.classList.add("cell-num");
          if (col.type === "badge") {
            var value = row[col.key];
            var count = value && typeof value === "object" ? Object.keys(value).length : 0;
            var btn = document.createElement("button");
            btn.className = "badge-btn";
            btn.textContent = "Extra (" + count + ")";
            btn.addEventListener("click", function () {
              if (col.onBadgeClick) col.onBadgeClick(row);
            });
            td.appendChild(btn);
          } else {
            var raw = row[col.key];
            var text = col.formatter ? col.formatter(raw, row) : defaultFormatter(col.type)(raw);
            td.textContent = text;
            if (text) td.title = text;
          }
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
    }

    // ---- interactions ----

    function onHeaderClick(col) {
      if (state.sortMode === "simple" && state.simpleSort && state.simpleSort.key === col.key) {
        if (state.simpleSort.dir === "asc") {
          state.simpleSort.dir = "desc";
        } else {
          state.sortMode = "none";
          state.simpleSort = null;
        }
      } else {
        state.sortMode = "simple";
        state.simpleSort = { key: col.key, dir: "asc" };
        state.advancedSort = [];
      }
      recompute();
    }

    function openAdvancedSortPanel() {
      var sortableCols = columns.filter(function (c) {
        return c.sortable !== false;
      });
      if (sortableCols.length === 0) return;
      var working = state.advancedSort.map(function (s) {
        return { key: s.key, dir: s.dir };
      });
      var selectEl, listEl;

      function availableCols() {
        return sortableCols.filter(function (c) {
          return !working.some(function (w) {
            return w.key === c.key;
          });
        });
      }

      function refreshSelect() {
        selectEl.innerHTML = "";
        var placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Choose column…";
        selectEl.appendChild(placeholder);
        availableCols().forEach(function (c) {
          var opt = document.createElement("option");
          opt.value = c.key;
          opt.textContent = c.label;
          selectEl.appendChild(opt);
        });
      }

      function refreshList() {
        listEl.innerHTML = "";
        working.forEach(function (entry, i) {
          var col = columnsByKey[entry.key];
          var li = document.createElement("li");
          var idx = document.createElement("span");
          idx.className = "sort-list__index";
          idx.textContent = i + 1 + ".";
          var keyEl = document.createElement("span");
          keyEl.className = "sort-list__key";
          keyEl.textContent = col ? col.label : entry.key;
          var dirBtn = document.createElement("button");
          dirBtn.className = "btn btn--icon";
          dirBtn.textContent = entry.dir === "asc" ? "▲ Asc" : "▼ Desc";
          dirBtn.addEventListener("click", function () {
            entry.dir = entry.dir === "asc" ? "desc" : "asc";
            refreshList();
          });
          var removeBtn = document.createElement("button");
          removeBtn.innerHTML = "&times;";
          removeBtn.title = "Remove";
          removeBtn.addEventListener("click", function () {
            working.splice(i, 1);
            refreshList();
            refreshSelect();
          });
          li.appendChild(idx);
          li.appendChild(keyEl);
          li.appendChild(dirBtn);
          li.appendChild(removeBtn);
          listEl.appendChild(li);
        });
        if (working.length === 0) {
          var empty = document.createElement("li");
          empty.textContent = "No columns added yet.";
          empty.style.color = "var(--fg-muted)";
          listEl.appendChild(empty);
        }
      }

      Viewer.modal.open({
        title: "Advanced sort",
        width: "480px",
        renderBody: function (bodyEl) {
          var addRow = document.createElement("div");
          addRow.className = "panel-row";
          selectEl = document.createElement("select");
          var addBtn = document.createElement("button");
          addBtn.className = "btn";
          addBtn.textContent = "Add";
          addBtn.addEventListener("click", function () {
            if (!selectEl.value) return;
            working.push({ key: selectEl.value, dir: "asc" });
            refreshList();
            refreshSelect();
          });
          addRow.appendChild(selectEl);
          addRow.appendChild(addBtn);

          listEl = document.createElement("ul");
          listEl.className = "sort-list";

          bodyEl.appendChild(addRow);
          bodyEl.appendChild(listEl);

          refreshSelect();
          refreshList();
        },
        renderFooter: function (footerEl2) {
          var cancelBtn = document.createElement("button");
          cancelBtn.className = "btn";
          cancelBtn.textContent = "Cancel";
          cancelBtn.addEventListener("click", Viewer.modal.close);
          var applyBtn = document.createElement("button");
          applyBtn.className = "btn btn--primary";
          applyBtn.textContent = "Apply";
          applyBtn.addEventListener("click", function () {
            state.advancedSort = working.filter(function (e) {
              return e.dir === "asc" || e.dir === "desc";
            });
            state.sortMode = state.advancedSort.length ? "advanced" : "none";
            state.simpleSort = null;
            Viewer.modal.close();
            recompute();
          });
          footerEl2.appendChild(cancelBtn);
          footerEl2.appendChild(applyBtn);
        },
      });
    }

    function openAddFilterPanel() {
      var filterableCols = columns.filter(function (c) {
        return c.filterable !== false;
      });
      if (filterableCols.length === 0) return;
      var selectEl, inputEl;

      function applyAndClose() {
        if (!inputEl.value) return;
        state.filters.set(selectEl.value, inputEl.value);
        Viewer.modal.close();
        recompute();
      }

      Viewer.modal.open({
        title: "Add filter",
        renderBody: function (bodyEl) {
          var row = document.createElement("div");
          row.className = "panel-row";
          selectEl = document.createElement("select");
          filterableCols.forEach(function (c) {
            var opt = document.createElement("option");
            opt.value = c.key;
            opt.textContent = c.label;
            selectEl.appendChild(opt);
          });
          inputEl = document.createElement("input");
          inputEl.type = "text";
          inputEl.placeholder = "Contains…";
          inputEl.addEventListener("keydown", function (ev) {
            if (ev.key === "Enter") applyAndClose();
          });
          row.appendChild(selectEl);
          row.appendChild(inputEl);
          bodyEl.appendChild(row);
          setTimeout(function () {
            inputEl.focus();
          }, 0);
        },
        renderFooter: function (footerEl2) {
          var cancelBtn = document.createElement("button");
          cancelBtn.className = "btn";
          cancelBtn.textContent = "Cancel";
          cancelBtn.addEventListener("click", Viewer.modal.close);
          var addBtn = document.createElement("button");
          addBtn.className = "btn btn--primary";
          addBtn.textContent = "Add filter";
          addBtn.addEventListener("click", applyAndClose);
          footerEl2.appendChild(cancelBtn);
          footerEl2.appendChild(addBtn);
        },
      });
    }

    recompute();

    return {
      getDisplayedRows: getDisplayedRows,
      destroy: function () {
        containerEl.innerHTML = "";
      },
    };
  }

  Viewer.createTable = createTable;
})();
