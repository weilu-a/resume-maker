/* global window */
(function (global) {
  function showToast(message, type) {
    type = type || "";
    var el = document.getElementById("app-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "app-toast";
      el.className = "toast";
      document.body.appendChild(el);
    }
    el.className = "toast show " + type;
    el.textContent = message;
    window.setTimeout(function () {
      el.classList.remove("show");
    }, 4000);
  }

  function waitForApi(timeoutMs) {
    timeoutMs = timeoutMs || 8000;
    return new Promise(function (resolve) {
      var start = Date.now();
      (function tick() {
        if (window.pywebview && window.pywebview.api) {
          resolve(true);
          return;
        }
        if (Date.now() - start >= timeoutMs) {
          resolve(false);
          return;
        }
        setTimeout(tick, 50);
      })();
    });
  }

  function apiCall(method) {
    var args = Array.prototype.slice.call(arguments, 1);
    return waitForApi().then(function (ready) {
      if (!ready || !window.pywebview.api[method]) {
        throw new Error("桌面桥接未就绪，请通过 python app/main.py 启动软件");
      }
      return window.pywebview.api[method].apply(window.pywebview.api, args);
    });
  }

  global.ResumeBridge = { showToast: showToast, waitForApi: waitForApi, apiCall: apiCall };
})(window);