(function () {
  "use strict";

  var Viewer = (window.Viewer = window.Viewer || {});

  var DOC_TYPE_LABELS = {
    invoice: "Invoice",
    packingList: "Packing List",
    docClassification: "Doc Classification",
    unknown: "Raw JSON",
  };

  var els = {};
  var currentRawInstance = null;

  function cacheEls() {
    els.body = document.body;
    els.docTypeLabel = document.getElementById("doc-type-label");
    els.startOverBtn = document.getElementById("start-over-btn");
    els.dropzone = document.getElementById("dropzone");
    els.fileInput = document.getElementById("file-input");
    els.uploadError = document.getElementById("upload-error");
    els.headerSection = document.getElementById("header-section");
    els.detailSection = document.getElementById("detail-section");
    els.rawSection = document.getElementById("raw-section");
  }

  function disposeCurrent() {
    if (currentRawInstance && currentRawInstance.dispose) {
      currentRawInstance.dispose();
    }
    currentRawInstance = null;
    els.headerSection.innerHTML = "";
    els.detailSection.innerHTML = "";
    els.rawSection.innerHTML = "";
    els.headerSection.hidden = false;
    els.detailSection.hidden = false;
    els.rawSection.hidden = true;
  }

  function showUploadScreen() {
    disposeCurrent();
    els.body.classList.remove("screen-viewer");
    els.body.classList.add("screen-upload");
    els.docTypeLabel.textContent = "";
    els.uploadError.hidden = true;
  }

  function showViewer(parsed, docType, fileName) {
    disposeCurrent();
    els.body.classList.remove("screen-upload");
    els.body.classList.add("screen-viewer");
    els.docTypeLabel.textContent = (DOC_TYPE_LABELS[docType] || docType) + " — " + fileName;

    var jsonData = (parsed && parsed.result && parsed.result.jsonData) || {};

    if (docType === "invoice") {
      Viewer.renderInvoice({ headerEl: els.headerSection, detailEl: els.detailSection }, { jsonData: jsonData });
    } else if (docType === "packingList") {
      Viewer.renderPackingList({ headerEl: els.headerSection, detailEl: els.detailSection }, { jsonData: jsonData });
    } else if (docType === "docClassification") {
      els.headerSection.hidden = true;
      Viewer.renderClassification({ detailEl: els.detailSection }, { jsonData: jsonData });
    } else {
      els.headerSection.hidden = true;
      els.detailSection.hidden = true;
      els.rawSection.hidden = false;
      Viewer.renderRaw({ rawEl: els.rawSection }, { fullEnvelope: parsed })
        .then(function (instance) {
          currentRawInstance = instance;
        })
        .catch(function (e) {
          els.rawSection.innerHTML = "";
          var err = document.createElement("div");
          err.className = "error-banner";
          err.textContent = "Failed to load JSON editor: " + e.message;
          els.rawSection.appendChild(err);
        });
    }
  }

  function init() {
    cacheEls();
    Viewer.theme.initThemeToggle(document.getElementById("theme-toggle"));

    Viewer.initUpload({
      dropzoneEl: els.dropzone,
      fileInputEl: els.fileInput,
      errorEl: els.uploadError,
      onFile: showViewer,
    });

    els.startOverBtn.addEventListener("click", showUploadScreen);

    showUploadScreen();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  Viewer.app = { showUploadScreen: showUploadScreen, showViewer: showViewer };
})();
