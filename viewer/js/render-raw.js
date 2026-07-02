(function () {
  "use strict";

  var Viewer = (window.Viewer = window.Viewer || {});

  // containers: { rawEl }, ctx: { fullEnvelope }
  // Returns a Promise<{ dispose() }> so app.js can dispose the Monaco instance on
  // "start over" (avoids leaking editors across repeated unknown-type uploads).
  function renderRaw(containers, ctx) {
    containers.rawEl.innerHTML = "";
    var loading = document.createElement("div");
    loading.className = "monaco-loading";
    loading.textContent = "Loading editor…";
    containers.rawEl.appendChild(loading);

    var editorContainer = document.createElement("div");
    editorContainer.className = "monaco-container";
    editorContainer.hidden = true;
    containers.rawEl.appendChild(editorContainer);

    return Viewer.createReadOnlyJsonEditor(editorContainer, ctx.fullEnvelope).then(function (instance) {
      loading.remove();
      editorContainer.hidden = false;
      return instance;
    });
  }

  Viewer.renderRaw = renderRaw;
})();
