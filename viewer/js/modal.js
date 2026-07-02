(function () {
  "use strict";

  var rootEl = null;
  var currentOverlay = null;
  var currentOnClose = null;

  function getRoot() {
    if (!rootEl) rootEl = document.getElementById("modal-root");
    return rootEl;
  }

  function close() {
    if (currentOverlay && currentOverlay.parentNode) {
      currentOverlay.parentNode.removeChild(currentOverlay);
    }
    currentOverlay = null;
    var cb = currentOnClose;
    currentOnClose = null;
    if (cb) cb();
  }

  function escHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // options: { title, renderBody(bodyEl), renderFooter(footerEl)?, onClose?, width? }
  function open(options) {
    close();

    var overlay = document.createElement("div");
    overlay.className = "modal-overlay";

    var modal = document.createElement("div");
    modal.className = "modal";
    if (options.width) modal.style.width = options.width;

    var header = document.createElement("div");
    header.className = "modal__header";
    var titleEl = document.createElement("h3");
    titleEl.className = "modal__title";
    titleEl.textContent = options.title || "";
    var closeBtn = document.createElement("button");
    closeBtn.className = "modal__close";
    closeBtn.setAttribute("aria-label", "Close");
    closeBtn.innerHTML = "&times;";
    closeBtn.addEventListener("click", close);
    header.appendChild(titleEl);
    header.appendChild(closeBtn);

    var body = document.createElement("div");
    body.className = "modal__body";

    modal.appendChild(header);
    modal.appendChild(body);

    if (options.renderBody) options.renderBody(body);

    var footer = null;
    if (options.renderFooter) {
      footer = document.createElement("div");
      footer.className = "modal__footer";
      modal.appendChild(footer);
      options.renderFooter(footer);
    }

    overlay.appendChild(modal);
    overlay.addEventListener("mousedown", function (ev) {
      if (ev.target === overlay) close();
    });

    getRoot().appendChild(overlay);
    currentOverlay = overlay;
    currentOnClose = options.onClose || null;

    function onKeydown(ev) {
      if (ev.key === "Escape") {
        close();
      }
    }
    document.addEventListener("keydown", onKeydown, { once: true });

    return { overlayEl: overlay, modalEl: modal, bodyEl: body, footerEl: footer, close: close };
  }

  // Convenience: render an arbitrary object's own keys as a key/value table.
  // Used for the invoiceItems[].extra / packingListItems[].extra badge popup,
  // where keys are fully dynamic and not known ahead of time.
  function openKeyValue(title, obj) {
    return open({
      title: title,
      renderBody: function (bodyEl) {
        var keys = obj && typeof obj === "object" ? Object.keys(obj) : [];
        if (keys.length === 0) {
          var empty = document.createElement("div");
          empty.className = "kv-modal-empty";
          empty.textContent = "No additional data.";
          bodyEl.appendChild(empty);
          return;
        }
        var table = document.createElement("table");
        table.className = "kv-modal-table";
        keys.forEach(function (key) {
          var tr = document.createElement("tr");
          var tdKey = document.createElement("td");
          tdKey.textContent = key;
          var tdVal = document.createElement("td");
          var value = obj[key];
          if (value === null || value === undefined || value === "") {
            tdVal.innerHTML = '<span class="kv-modal-empty">&mdash;</span>';
          } else if (typeof value === "object") {
            tdVal.textContent = JSON.stringify(value);
          } else {
            tdVal.textContent = String(value);
          }
          tr.appendChild(tdKey);
          tr.appendChild(tdVal);
          table.appendChild(tr);
        });
        bodyEl.appendChild(table);
      },
    });
  }

  window.Viewer = window.Viewer || {};
  window.Viewer.modal = {
    open: open,
    close: close,
    openKeyValue: openKeyValue,
    escHtml: escHtml,
  };
})();
