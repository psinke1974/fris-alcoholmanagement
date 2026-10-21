(function () {
  if (!("serviceWorker" in navigator)) return;
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/static/sw.js").catch(function () {
      /* stil falen in development / insecure context */
    });
  });
})();
