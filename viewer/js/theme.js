(function () {
  "use strict";

  var STORAGE_KEY = "viewer.theme";
  var VALID = ["light", "dark", "system"];

  function getStoredTheme() {
    try {
      var v = window.localStorage.getItem(STORAGE_KEY);
      return VALID.indexOf(v) !== -1 ? v : "system";
    } catch (e) {
      return "system";
    }
  }

  function setStoredTheme(theme) {
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      /* localStorage unavailable (e.g. private mode) - theme just won't persist */
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
  }

  function resolvedLabel(theme) {
    if (theme !== "system") return theme === "dark" ? "Dark" : "Light";
    var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    return "System (" + (prefersDark ? "Dark" : "Light") + ")";
  }

  // Apply immediately (theme.js is loaded+run in <head> before body paints)
  // to avoid a flash of the wrong theme.
  applyTheme(getStoredTheme());

  function setTheme(theme) {
    if (VALID.indexOf(theme) === -1) theme = "system";
    setStoredTheme(theme);
    applyTheme(theme);
    updateToggleUI();
  }

  var toggleButtons = null;

  function updateToggleUI() {
    if (!toggleButtons) return;
    var current = getStoredTheme();
    toggleButtons.forEach(function (btn) {
      var isActive = btn.getAttribute("data-theme-value") === current;
      btn.setAttribute("aria-pressed", isActive ? "true" : "false");
      if (btn.getAttribute("data-theme-value") === "system") {
        btn.title = resolvedLabel("system");
      }
    });
  }

  function initThemeToggle(containerEl) {
    toggleButtons = Array.prototype.slice.call(containerEl.querySelectorAll("[data-theme-value]"));
    toggleButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        setTheme(btn.getAttribute("data-theme-value"));
      });
    });
    updateToggleUI();

    if (window.matchMedia) {
      var mq = window.matchMedia("(prefers-color-scheme: dark)");
      var onChange = function () {
        if (getStoredTheme() === "system") updateToggleUI();
      };
      if (mq.addEventListener) mq.addEventListener("change", onChange);
      else if (mq.addListener) mq.addListener(onChange);
    }
  }

  window.Viewer = window.Viewer || {};
  window.Viewer.theme = {
    getStoredTheme: getStoredTheme,
    setTheme: setTheme,
    initThemeToggle: initThemeToggle,
  };
})();
