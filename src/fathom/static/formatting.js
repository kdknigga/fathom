/**
 * Client-side monetary input formatting.
 *
 * Delegated event listeners on #comparison-form handle:
 * - focusin: strip commas for clean editing
 * - focusout: add commas for readability
 * - paste: clean $, commas, whitespace from pasted text
 *
 * Event delegation ensures HTMX-swapped fields work automatically.
 */
(function () {
  "use strict";

  var form = document.getElementById("comparison-form");
  if (!form) {
    return;
  }

  function isMonetary(target) {
    return target && target.hasAttribute("data-monetary");
  }

  form.addEventListener("focusin", function (e) {
    if (!isMonetary(e.target)) {
      return;
    }
    e.target.value = e.target.value.replace(/,/g, "");
  });

  form.addEventListener("focusout", function (e) {
    if (!isMonetary(e.target)) {
      return;
    }
    var raw = e.target.value.replace(/,/g, "");
    if (raw === "" || isNaN(raw)) {
      return;
    }
    var parts = raw.split(".");
    var num = parseFloat(raw);
    if (parts.length === 2) {
      var decimals = parts[1].length;
      e.target.value = num.toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      });
    } else {
      e.target.value = num.toLocaleString("en-US");
    }
  });

  form.addEventListener("paste", function (e) {
    if (!isMonetary(e.target)) {
      return;
    }
    e.preventDefault();
    var text = (e.clipboardData || window.clipboardData).getData("text");
    e.target.value = text.replace(/[$,\s]/g, "");
  });
})();
