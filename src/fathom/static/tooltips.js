/**
 * Tax bracket row click-to-fill and keyboard activation.
 *
 * Delegated event listeners on #comparison-form handle:
 * - click: fill tax rate input from bracket row data-rate attribute
 * - keydown: Enter/Space activates bracket row via click
 *
 * Event delegation ensures HTMX-swapped fields work automatically.
 */
(function () {
  "use strict";

  var form = document.getElementById("comparison-form");
  if (!form) {
    return;
  }

  form.addEventListener("click", function (e) {
    var row = e.target.closest(".bracket-row");
    if (!row) {
      return;
    }
    var rate = row.getAttribute("data-rate");
    var taxInput = document.getElementById("tax-rate");
    if (taxInput && rate) {
      taxInput.value = rate;
      // Also check the "Include tax implications" checkbox
      var taxCheckbox = form.querySelector('[name="tax_enabled"]');
      if (taxCheckbox && !taxCheckbox.checked) {
        taxCheckbox.checked = true;
      }
      // Update aria-selected on rows
      var allRows = row.parentElement.querySelectorAll(".bracket-row");
      for (var i = 0; i < allRows.length; i++) {
        allRows[i].setAttribute("aria-selected", "false");
      }
      row.setAttribute("aria-selected", "true");
    }
  });

  form.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") {
      return;
    }
    var row = e.target.closest(".bracket-row");
    if (!row) {
      return;
    }
    e.preventDefault();
    row.click();
  });
})();
