/* global ResumeBridge, echarts */
(function () {
  var lastResult = null;
  var pdfPath = "";
  var selectedTemplateId = "blue-minimal";
  var templates = [];

  function $(id) {
    return document.getElementById(id);
  }

  function setLoadingText(text) {
    var el = $("loading-text");
    if (el) el.innerText = text;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function withBalancedPreviewCss(html) {
    var balance =
      "<style id='preview-balance'>" +
      "html,body{height:100%!important;min-height:100%!important;}" +
      "table.layout{height:100%!important;min-height:100%!important;}" +
      "td.side,td.main{height:100%!important;}" +
      ".banner{margin:20px 0 14px!important;}" +
      ".banner:first-child{margin-top:0!important;}" +
      ".item{margin-bottom:18px!important;padding-bottom:14px!important;}" +
      ".pill{margin:18px 0 10px!important;}" +
      ".side-meta{line-height:1.9!important;}" +
      ".desc{line-height:1.8!important;}" +
      ".sec-h,.sec{margin-top:22px!important;margin-bottom:12px!important;}" +
      ".resume-mark{margin-bottom:20px!important;}" +
      ".side-title{margin-bottom:16px!important;}" +
      "h1{margin-bottom:16px!important;}" +
      "</style>";
    if (!html) return html;
    if (html.indexOf("</head>") !== -1) {
      return html.replace("</head>", balance + "</head>");
    }
    return balance + html;
  }

  function setOptimizedHtml(html) {
    var frame = $("optimized-preview-frame");
    if (!frame) return;
    frame.srcdoc = withBalancedPreviewCss(html || "");
  }

  function renderSuggestions(list) {
    var box = $("suggest-list");
    box.innerHTML = "";
    var iconMap = {
      check: "ph:check-circle-bold",
      info: "ph:info-bold",
      star: "ph:star-bold",
    };
    var colorMap = {
      check: "#10B981",
      info: "#4F8CFF",
      star: "#8B5CF6",
    };
    (list || []).forEach(function (s) {
      var icon = s.icon || "info";
      var div = document.createElement("div");
      div.className = "p-4 hover:bg-[#2D2D2D] transition-colors";
      div.innerHTML =
        '<div class="flex items-center space-x-2 mb-2" style="color:' +
        (colorMap[icon] || "#4F8CFF") +
        '">' +
        '<iconify-icon icon="' +
        (iconMap[icon] || iconMap.info) +
        '"></iconify-icon>' +
        '<span class="text-xs font-bold">' +
        escapeHtml(s.type || "建议") +
        "</span></div>" +
        '<p class="text-[11px] text-[#AAAAAA] leading-snug">' +
        escapeHtml(s.text || "") +
        "</p>";
      box.appendChild(div);
    });
  }

  function initChart(score) {
    score = score || 88;
    var chartDom = $("score-chart");
    if (!chartDom || typeof echarts === "undefined") return;
    var myChart = echarts.init(chartDom);
    myChart.setOption({
      series: [
        {
          type: "pie",
          radius: ["70%", "90%"],
          avoidLabelOverlap: false,
          label: { show: false },
          emphasis: { disabled: true },
          data: [
            { value: score, itemStyle: { color: "#4F8CFF" } },
            { value: Math.max(0, 100 - score), itemStyle: { color: "#3A3A3A" } },
          ],
        },
      ],
      graphic: {
        type: "text",
        left: "center",
        top: "center",
        style: {
          text: String(score),
          fill: "#fff",
          fontSize: 14,
          fontWeight: "bold",
        },
      },
    });
  }

  function renderTemplateChips() {
    var box = $("template-chips");
    if (!box) return;
    box.innerHTML = "";
    (templates || []).forEach(function (t) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tpl-chip" + (t.id === selectedTemplateId ? " active" : "");
      btn.textContent = t.name || t.id;
      btn.onclick = function () {
        switchTemplate(t.id);
      };
      box.appendChild(btn);
    });
  }

  async function switchTemplate(id) {
    if (!id || id === selectedTemplateId) return;
    selectedTemplateId = id;
    renderTemplateChips();
    var loading = $("preview-loading");
    if (loading) loading.classList.remove("hidden");
    try {
      var res = await ResumeBridge.apiCall("preview_optimized", selectedTemplateId);
      if (!res.ok) {
        ResumeBridge.showToast(res.error || "预览失败", "warn");
        return;
      }
      setOptimizedHtml(res.html || "");
      ResumeBridge.showToast("已切换预览（导出时才生成 PDF）", "ok");
    } catch (e) {
      ResumeBridge.showToast(e.message || String(e), "warn");
    } finally {
      if (loading) loading.classList.add("hidden");
    }
  }

  function showResult(result) {
    lastResult = result;
    $("optimizing-view").classList.add("hidden");
    $("result-view").classList.remove("hidden");
    $("action-btns").classList.remove("hidden");
    $("action-btns").classList.add("flex");

    $("score-up").textContent = "提升了 " + (result.score_up || 0) + "%";
    $("metric-skill").textContent = (result.skill_match || 0) + "%";
    $("metric-exp").textContent = (result.experience_density || 0) + "%";
    $("metric-kw").textContent = (result.keywords || 0) + "%";
    $("ai-source-opt").textContent =
      result.ai_source === "ollama"
        ? "Ollama 优化"
        : result.ai_source === "deepseek"
          ? "DeepSeek 云端优化"
          : "本地规则优化";

    if (result.template_id) {
      selectedTemplateId = result.template_id;
    }
    renderTemplateChips();
    setOptimizedHtml(result.preview_html || "");

    var oriImg = $("original-pdf-preview");
    var fallback = $("original-fallback");
    if (result.original_preview_url) {
      oriImg.src = result.original_preview_url;
      oriImg.classList.remove("hidden");
      fallback.classList.add("hidden");
    } else {
      oriImg.removeAttribute("src");
      fallback.classList.remove("hidden");
      fallback.textContent = result.raw_preview || "无法预览原 PDF 页面";
    }

    renderSuggestions(result.suggestions);
    initChart(result.score || 88);
  }

  async function runOptimize(path) {
    pdfPath = path;
    $("upload-view").classList.add("hidden");
    $("optimizing-view").classList.remove("hidden");
    $("result-view").classList.add("hidden");

    var steps = [
      "正在解析 PDF 文本...",
      "正在分析原始文案...",
      "正在调用 AI 优化...",
      "正在套用简历模板生成预览...",
    ];
    var i = 0;
    setLoadingText(steps[0]);
    var timer = setInterval(function () {
      i += 1;
      if (i < steps.length) setLoadingText(steps[i]);
    }, 700);

    try {
      var result = await ResumeBridge.apiCall(
        "optimize_resume",
        path,
        selectedTemplateId
      );
      clearInterval(timer);
      if (!result.ok) {
        ResumeBridge.showToast(result.error || "优化失败", "warn");
        $("optimizing-view").classList.add("hidden");
        $("upload-view").classList.remove("hidden");
        return;
      }
      showResult(result);
      ResumeBridge.showToast("优化完成", "ok");
    } catch (e) {
      clearInterval(timer);
      ResumeBridge.showToast(e.message || String(e), "warn");
      $("optimizing-view").classList.add("hidden");
      $("upload-view").classList.remove("hidden");
    }
  }

  window.startOptimizing = async function () {
    try {
      ResumeBridge.showToast('正在打开文件选择器...', '');
      var res = await ResumeBridge.apiCall("pick_pdf");
      if (res.ok) {
        $("upload-filename").textContent = res.name || "已选择文件";
        await runOptimize(res.path);
      } else if (res.error) {
        ResumeBridge.showToast('选择文件失败: ' + res.error, 'warn');
      } else if (!res.cancelled) {
        ResumeBridge.showToast('未选择文件', '');
      }
    } catch (e) {
      ResumeBridge.showToast('选择文件时出错: ' + (e.message || String(e)), 'warn');
    }
  };

  window.reupload = function () {
    lastResult = null;
    pdfPath = "";
    $("result-view").classList.add("hidden");
    $("action-btns").classList.add("hidden");
    $("action-btns").classList.remove("flex");
    $("upload-view").classList.remove("hidden");
  };

  window.exportOptimized = async function () {
    try {
      var res = await ResumeBridge.apiCall("export_optimized", selectedTemplateId);
      if (!res.ok) {
        ResumeBridge.showToast(res.error || "导出失败", "warn");
        return;
      }
      if (res.html) {
        setOptimizedHtml(res.html);
      }
      ResumeBridge.showToast("已导出: " + res.pdf_path, "ok");
      await ResumeBridge.apiCall("open_output_folder");
    } catch (e) {
      ResumeBridge.showToast(e.message || String(e), "warn");
    }
  };

  document.addEventListener("DOMContentLoaded", async function () {
    var zone = $("drop-zone");
    zone.addEventListener("click", window.startOptimizing);
    $("btn-reupload").addEventListener("click", window.reupload);
    $("btn-export-opt").addEventListener("click", window.exportOptimized);
    try {
      templates = (await ResumeBridge.apiCall("list_templates")) || [];
      if (templates[0]) selectedTemplateId = templates[0].id;
      renderTemplateChips();
      var health = await ResumeBridge.apiCall("check_ollama");
      if (!health.online || !health.has_model) {
        ResumeBridge.showToast(health.message || "Ollama 未就绪", "warn");
      }
    } catch (e) {
      ResumeBridge.showToast(e.message || String(e), "warn");
    }
  });
})();
