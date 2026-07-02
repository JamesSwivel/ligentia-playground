(function () {
  "use strict";

  var Viewer = (window.Viewer = window.Viewer || {});

  function isJsonFile(file) {
    return /\.json$/i.test(file.name || "");
  }

  // options: { dropzoneEl, fileInputEl, errorEl, onFile(parsed, docType, fileName) }
  function initUpload(options) {
    var dropzoneEl = options.dropzoneEl;
    var fileInputEl = options.fileInputEl;
    var errorEl = options.errorEl;

    function showError(msg) {
      errorEl.textContent = msg;
      errorEl.hidden = false;
    }

    function clearError() {
      errorEl.hidden = true;
      errorEl.textContent = "";
    }

    function handleFile(file) {
      clearError();
      if (!file) return;
      if (!isJsonFile(file)) {
        showError('Please upload a .json file. "' + file.name + '" was rejected.');
        return;
      }
      file
        .text()
        .then(function (text) {
          var parsed;
          try {
            parsed = JSON.parse(text);
          } catch (e) {
            showError("Could not parse JSON: " + e.message);
            return;
          }
          var docType = Viewer.detectDocType(parsed);
          options.onFile(parsed, docType, file.name);
        })
        .catch(function (e) {
          showError("Could not read file: " + e.message);
        });
    }

    fileInputEl.addEventListener("change", function () {
      var file = fileInputEl.files && fileInputEl.files[0];
      handleFile(file);
      fileInputEl.value = "";
    });

    dropzoneEl.addEventListener("click", function () {
      fileInputEl.click();
    });

    ["dragenter", "dragover"].forEach(function (evt) {
      dropzoneEl.addEventListener(evt, function (ev) {
        ev.preventDefault();
        dropzoneEl.classList.add("dropzone--active");
      });
    });
    ["dragleave", "drop"].forEach(function (evt) {
      dropzoneEl.addEventListener(evt, function (ev) {
        ev.preventDefault();
        dropzoneEl.classList.remove("dropzone--active");
      });
    });
    dropzoneEl.addEventListener("drop", function (ev) {
      var file = ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files[0];
      handleFile(file);
    });
  }

  Viewer.initUpload = initUpload;
})();
