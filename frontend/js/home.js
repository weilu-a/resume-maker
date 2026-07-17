/* global ResumeBridge */
(function () {
  function $(id) {
    return document.getElementById(id);
  }

  function greeting() {
    var h = new Date().getHours();
    if (h < 12) return "上午好";
    if (h < 18) return "下午好";
    return "晚上好";
  }

  async function loadRecent() {
    var list = await ResumeBridge.apiCall("list_recent_outputs");
    var box = $("recent-list");
    if (!box) return;
    if (!list || !list.length) {
      box.innerHTML =
        '<div class="text-[#666666] text-sm py-6">暂无导出记录，去生成一份简历吧。</div>';
      return;
    }
    box.innerHTML = "";
    list.forEach(function (item) {
      var d = new Date((item.mtime || 0) * 1000);
      var time =
        d.getFullYear() +
        "-" +
        String(d.getMonth() + 1).padStart(2, "0") +
        "-" +
        String(d.getDate()).padStart(2, "0") +
        " " +
        String(d.getHours()).padStart(2, "0") +
        ":" +
        String(d.getMinutes()).padStart(2, "0");
      var row = document.createElement("div");
      row.className =
        "glass-card p-4 rounded-xl flex items-center hover:bg-[#2D2D2D] transition-colors cursor-pointer group";
      row.innerHTML =
        '<div class="w-10 h-12 bg-[#3A3A3A] rounded flex items-center justify-center text-[#AAAAAA] mr-4">' +
        '<iconify-icon class="text-2xl" icon="ph:file-pdf"></iconify-icon></div>' +
        '<div class="flex-1"><h4 class="font-medium mb-0.5">' +
        item.name +
        '</h4><div class="flex items-center space-x-3 text-xs text-[#666666]">' +
        "<span>" +
        time +
        '</span><span>•</span><span class="text-[#4F8CFF]">已导出 PDF</span></div></div>';
      row.onclick = function () {
        ResumeBridge.apiCall("open_output_folder");
      };
      box.appendChild(row);
    });
  }

  document.addEventListener("DOMContentLoaded", async function () {
    var g = $("greeting-title");
    if (g) g.textContent = greeting() + "，探险者";
    try {
      await ResumeBridge.waitForApi();
      var health = await ResumeBridge.apiCall("check_ollama");
      var badge = $("ollama-badge");
      if (badge) {
        if (health.online && health.has_model) {
          badge.textContent = "Ollama 就绪";
          badge.className =
            "text-[10px] px-2 py-0.5 rounded bg-[#10B981]/20 text-[#10B981]";
        } else if (health.online) {
          badge.textContent = "缺模型";
          badge.className =
            "text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-400";
          ResumeBridge.showToast(
            health.message || "请运行 setup_ai.bat 拉取模型",
            "warn"
          );
        } else {
          badge.textContent = "降级模式";
          badge.className =
            "text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-400";
          ResumeBridge.showToast(
            health.message || "Ollama 未就绪，请运行 setup_ai.bat",
            "warn"
          );
        }
      }
      await loadRecent();
    } catch (e) {
      ResumeBridge.showToast(e.message || String(e), "warn");
    }
  });
})();