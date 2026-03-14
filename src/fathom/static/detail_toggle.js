/* Detail toggle: column visibility, tab keyboard nav, granularity switch */
(function () {
  "use strict";

  /* --- Column toggle state management --- */
  var hiddenCols = {};

  function applyHidden(container) {
    var root = container || document;
    Object.keys(hiddenCols).forEach(function (cls) {
      var els = root.querySelectorAll("." + cls);
      var display = hiddenCols[cls] ? "none" : "";
      for (var i = 0; i < els.length; i++) {
        els[i].style.display = display;
      }
    });
  }

  document.addEventListener("change", function (e) {
    var cb = e.target;
    if (!cb.classList.contains("col-toggle")) return;
    var col = cb.getAttribute("data-column");
    if (!col) return;
    hiddenCols[col] = !cb.checked;
    applyHidden(document);
  });

  /* Re-apply hidden state after HTMX swaps new content into #detail-panel */
  document.addEventListener("htmx:afterSwap", function (e) {
    if (e.detail && e.detail.target && e.detail.target.id === "detail-panel") {
      applyHidden(e.detail.target);
    }
  });

  /* --- Tab keyboard navigation (ARIA tablist pattern) --- */
  document.addEventListener("keydown", function (e) {
    var tablist = e.target.closest(".detail-tabs");
    if (!tablist) return;
    var tabs = tablist.querySelectorAll('[role="tab"]');
    if (!tabs.length) return;

    var idx = -1;
    for (var i = 0; i < tabs.length; i++) {
      if (tabs[i] === e.target) { idx = i; break; }
    }
    if (idx === -1) return;

    var next = -1;
    if (e.key === "ArrowRight") {
      next = (idx + 1) % tabs.length;
    } else if (e.key === "ArrowLeft") {
      next = (idx - 1 + tabs.length) % tabs.length;
    } else if (e.key === "Home") {
      next = 0;
    } else if (e.key === "End") {
      next = tabs.length - 1;
    }

    if (next !== -1) {
      e.preventDefault();
      tabs[next].focus();
    }
  });

  /* Update aria-selected on tab click */
  document.addEventListener("click", function (e) {
    var tab = e.target.closest('[role="tab"]');
    if (!tab) return;
    var tablist = tab.closest(".detail-tabs");
    if (!tablist) return;

    var tabs = tablist.querySelectorAll('[role="tab"]');
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].setAttribute("aria-selected", "false");
      tabs[i].setAttribute("tabindex", "-1");
    }
    tab.setAttribute("aria-selected", "true");
    tab.setAttribute("tabindex", "0");

    var panel = document.getElementById("detail-panel");
    if (panel) {
      panel.setAttribute("aria-labelledby", tab.id);
    }
  });

  /* --- Granularity toggle --- */
  var currentGranularity = "monthly";

  document.addEventListener("change", function (e) {
    if (e.target.name !== "detail-granularity") return;
    currentGranularity = e.target.value;

    /* Find the currently active tab and re-trigger its request */
    var activeTab = document.querySelector('.detail-tabs [role="tab"][aria-selected="true"]');
    if (!activeTab) return;

    /* Update hx-post URL to include granularity param */
    var baseUrl = activeTab.getAttribute("hx-post");
    if (!baseUrl) return;

    /* Strip existing granularity param */
    baseUrl = baseUrl.replace(/[?&]granularity=[^&]*/g, "");

    var url = baseUrl + "?granularity=" + currentGranularity;

    /* Use htmx.ajax to re-fetch with new granularity */
    if (typeof htmx !== "undefined") {
      htmx.ajax("POST", url, {
        target: "#detail-panel",
        swap: "innerHTML",
        source: activeTab,
      });
    }
  });
})();
