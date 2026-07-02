(function () {
  "use strict";

  // Generic "header" key/value renderer. Knows nothing about invoice/packingList/
  // classification field semantics - callers pass already-labeled {label, value}
  // pairs; this module only lays them out (main panel + nested sub-section panels
  // like issueFrom/issueTo, plus an optional collapsed <details> block per panel).

  function fieldsToGrid(items) {
    var grid = document.createElement("div");
    grid.className = "kv-grid";
    (items || []).forEach(function (item) {
      var wrap = document.createElement("div");
      wrap.className = "kv-item";
      var label = document.createElement("div");
      label.className = "kv-item__label";
      label.textContent = item.label;
      var val = document.createElement("div");
      val.className = "kv-item__value";
      if (item.value === undefined || item.value === null || item.value === "") {
        val.innerHTML = '<span class="kv-modal-empty">&mdash;</span>';
      } else {
        val.textContent = String(item.value);
      }
      wrap.appendChild(label);
      wrap.appendChild(val);
      grid.appendChild(wrap);
    });
    return grid;
  }

  // options: { title?, items: [{label, value}], collapsedItems?: [{label, value}], collapsedLabel? }
  function renderPanel(parentEl, options) {
    var panel = document.createElement("div");
    panel.className = "kv-panel";
    if (options.title) {
      var t = document.createElement("div");
      t.className = "kv-panel__title";
      t.textContent = options.title;
      panel.appendChild(t);
    }
    panel.appendChild(fieldsToGrid(options.items));
    if (options.collapsedItems && options.collapsedItems.length) {
      var det = document.createElement("details");
      det.className = "kv-collapsed";
      var sum = document.createElement("summary");
      sum.textContent = options.collapsedLabel || "More details";
      det.appendChild(sum);
      det.appendChild(fieldsToGrid(options.collapsedItems));
      panel.appendChild(det);
    }
    parentEl.appendChild(panel);
    return panel;
  }

  // options: { title?, items?, collapsedItems?, collapsedLabel?, extraNode?: Element, subsections?: [panelOptions] }
  function renderHeader(containerEl, options) {
    containerEl.innerHTML = "";
    if (options.items && options.items.length) {
      renderPanel(containerEl, {
        title: options.title,
        items: options.items,
        collapsedItems: options.collapsedItems,
        collapsedLabel: options.collapsedLabel,
      });
    }
    if (options.extraNode) {
      containerEl.appendChild(options.extraNode);
    }
    if (options.subsections && options.subsections.length) {
      var grid = document.createElement("div");
      grid.className = "kv-subsections";
      options.subsections.forEach(function (sub) {
        renderPanel(grid, sub);
      });
      containerEl.appendChild(grid);
    }
  }

  window.Viewer = window.Viewer || {};
  window.Viewer.kv = { renderPanel: renderPanel, renderHeader: renderHeader };
})();
