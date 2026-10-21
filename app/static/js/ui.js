/* Kleine UI-hulpjes zonder inline event handlers (vereist door de Content-Security-Policy). */
(function () {
  document.addEventListener("click", function (event) {
    const confirmEl = event.target.closest("[data-confirm]");
    if (confirmEl && !window.confirm(confirmEl.dataset.confirm)) {
      event.preventDefault();
      return;
    }
    if (event.target.closest('[data-action="print"]')) {
      window.print();
    }
  });
})();
