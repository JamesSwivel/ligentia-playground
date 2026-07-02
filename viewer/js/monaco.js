(function () {
  "use strict";

  // Lazy Monaco bootstrap. loader.js + require.config({paths:{vs:...}}) are wired
  // up via <script> tags in index.html (before this file loads); we only ever call
  // require(['vs/editor/editor.main']) once we actually need Monaco (i.e. only when
  // the "unknown" doc type is rendered), memoized so a second unknown-type upload in
  // the same session doesn't re-fetch/re-init.

  var monacoPromise = null;

  function loadMonaco() {
    if (monacoPromise) return monacoPromise;
    monacoPromise = new Promise(function (resolve, reject) {
      if (typeof window.require !== "function") {
        reject(new Error("Monaco AMD loader (require) is not available."));
        return;
      }
      window.require(["vs/editor/editor.main"], function () {
        resolve(window.monaco);
      }, reject);
    });
    return monacoPromise;
  }

  // Returns a Promise<{ editor, model, dispose() }>
  function createReadOnlyJsonEditor(containerEl, jsObject) {
    return loadMonaco().then(function (monaco) {
      var model = monaco.editor.createModel(JSON.stringify(jsObject, null, 2), "json");
      var editor = monaco.editor.create(containerEl, {
        model: model,
        readOnly: true,
        domReadOnly: true,
        automaticLayout: true,
        minimap: { enabled: true },
        folding: true,
        foldingStrategy: "auto",
        scrollBeyondLastLine: false,
        wordWrap: "off",
      });
      return {
        editor: editor,
        model: model,
        dispose: function () {
          editor.dispose();
          model.dispose();
        },
      };
    });
  }

  window.Viewer = window.Viewer || {};
  window.Viewer.loadMonaco = loadMonaco;
  window.Viewer.createReadOnlyJsonEditor = createReadOnlyJsonEditor;
})();
