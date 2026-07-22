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
      if (window.pywebview && window.pywebview.api) {
        resolve(true);
        return;
      }
      
      var resolved = false;
      
      function onReady() {
        if (resolved) return;
        resolved = true;
        resolve(window.pywebview && window.pywebview.api ? true : false);
      }
      
      if (document.readyState === 'complete' || document.readyState === 'interactive') {
        if (window.pywebview && window.pywebview.api) {
          resolve(true);
          return;
        }
      }
      
      document.addEventListener('_pywebviewready', onReady);
      
      var start = Date.now();
      (function tick() {
        if (resolved) return;
        if (window.pywebview && window.pywebview.api) {
          onReady();
          return;
        }
        if (Date.now() - start >= timeoutMs) {
          resolved = true;
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
      if (!ready) {
        console.error("pywebview not found - running in browser mode");
        throw new Error("桌面桥接未就绪（未检测到 pywebview），请通过 python app/main.py 启动软件");
      }
      if (!window.pywebview.api) {
        console.error("pywebview.api not found");
        throw new Error("桌面桥接未就绪（api 不存在），请通过 python app/main.py 启动软件");
      }
      if (!window.pywebview.api[method]) {
        console.error("API method not found:", method, "Available:", Object.keys(window.pywebview.api));
        throw new Error("桌面桥接未就绪（API " + method + " 不存在），请通过 python app/main.py 启动软件");
      }
      
      var apiPromise = window.pywebview.api[method].apply(window.pywebview.api, args);
      var timeoutPromise = new Promise(function (resolve, reject) {
        setTimeout(function () {
          reject(new Error("API 调用超时（" + method + "）"));
        }, 120000);
      });
      
      return Promise.race([apiPromise, timeoutPromise]);
    });
  }

  global.ResumeBridge = { showToast: showToast, waitForApi: waitForApi, apiCall: apiCall };
})(window);