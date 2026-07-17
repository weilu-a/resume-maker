/* global ResumeBridge */
(function () {
  var currentStep = 1;
  var selectedTemplateId = "blue-minimal";
  var templateMeta = {};
  var photoPath = "";
  var photoUri = "";
  var lastPdfPath = "";
  var previewTimer = null;

  function $(id) {
    return document.getElementById(id);
  }

  function collectForm() {
    var experiences = [
      {
        company: $("exp-company").value.trim(),
        period: $("exp-period").value.trim(),
        title: $("exp-title").value.trim(),
        description: $("exp-desc").value.trim(),
      },
    ];
    var education = [
      {
        school: $("edu-school").value.trim(),
        period: $("edu-period").value.trim(),
        degree: $("edu-degree").value.trim(),
        major: $("edu-major").value.trim(),
      },
    ];
    var projects = [
      {
        name: $("proj-name").value.trim(),
        period: $("proj-period").value.trim(),
        description: $("proj-desc").value.trim(),
      },
    ];
    return {
      template_id: selectedTemplateId,
      name: $("field-name").value.trim(),
      phone: $("field-phone").value.trim(),
      email: $("field-email").value.trim(),
      summary: $("field-summary").value.trim(),
      skills: $("field-skills").value.trim(),
      photo_path: photoPath,
      photo_uri: photoUri,
      experiences: experiences,
      education: education,
      projects: projects.filter(function (p) {
        return p.name || p.description;
      }),
    };
  }

  function updateTemplateLabel() {
    var el = $("preview-template-name");
    if (!el) return;
    var meta = templateMeta[selectedTemplateId];
    el.textContent = meta ? meta.name : selectedTemplateId;
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

  async function updateLivePreview() {
    updateTemplateLabel();
    var frame = $("live-preview-frame");
    if (!frame) return;
    try {
      var res = await ResumeBridge.apiCall(
        "preview_form",
        JSON.stringify(collectForm())
      );
      if (!res.ok) {
        frame.srcdoc =
          '<p style="padding:16px;font-family:sans-serif;color:#666;">' +
          (res.error || "预览失败") +
          "</p>";
        return;
      }
      frame.srcdoc = withBalancedPreviewCss(res.html || "");
    } catch (e) {
      frame.srcdoc =
        '<p style="padding:16px;font-family:sans-serif;color:#666;">' +
        (e.message || String(e)) +
        "</p>";
    }
  }

  function scheduleLivePreview() {
    if (previewTimer) clearTimeout(previewTimer);
    previewTimer = setTimeout(function () {
      updateLivePreview();
    }, 280);
  }

  async function loadTemplates() {
    var list = await ResumeBridge.apiCall("list_templates");
    var grid = $("template-grid");
    grid.innerHTML = "";
    templateMeta = {};
    (list || []).forEach(function (t, idx) {
      templateMeta[t.id] = t;
      var card = document.createElement("div");
      card.className =
        "template-card border-2 border-transparent bg-[#252525] rounded-xl overflow-hidden cursor-pointer transition-all flex flex-col" +
        (idx === 0 ? " selected" : "");
      card.dataset.id = t.id;
      card.innerHTML =
        '<div class="bg-[#333] h-64 flex items-center justify-center overflow-hidden">' +
        '<img alt="' +
        t.name +
        '" class="w-4/5 shadow-2xl ' +
        (idx === 0 ? "" : "opacity-60") +
        '" src="' +
        (t.preview_url || "") +
        '"/>' +
        "</div>" +
        '<div class="p-4 flex justify-between items-center">' +
        "<div><h4 class=\"font-medium\">" +
        t.name +
        '</h4><span class="text-[10px] px-2 py-0.5 rounded" style="color:' +
        t.tag_color +
        ";background:" +
        t.tag_color +
        '22">' +
        t.tag +
        "</span></div>" +
        (idx === 0
          ? '<iconify-icon class="text-[#4F8CFF] text-xl" icon="ph:check-circle-fill"></iconify-icon>'
          : "") +
        "</div>";
      card.onclick = function () {
        selectTemplate(card, t.id);
      };
      grid.appendChild(card);
    });
    if (list && list[0]) selectedTemplateId = list[0].id;
    updateTemplateLabel();
  }

  function selectTemplate(el, id) {
    selectedTemplateId = id;
    document.querySelectorAll(".template-card").forEach(function (card) {
      card.classList.remove("selected");
      var img = card.querySelector("img");
      if (img) img.classList.add("opacity-60");
      var check = card.querySelector('iconify-icon[icon="ph:check-circle-fill"]');
      if (check) check.remove();
    });
    el.classList.add("selected");
    var img2 = el.querySelector("img");
    if (img2) img2.classList.remove("opacity-60");
    var infoArea = el.querySelector(".p-4");
    var icon = document.createElement("iconify-icon");
    icon.setAttribute("icon", "ph:check-circle-fill");
    icon.className = "text-[#4F8CFF] text-xl";
    infoArea.appendChild(icon);
    updateTemplateLabel();
    if (currentStep === 2) scheduleLivePreview();
  }

  function markStepDone(step) {
    var head = $("step-" + step + "-head");
    head.classList.remove("step-active");
    head.classList.add("text-[#10B981]");
    head.innerHTML =
      '<div class="w-6 h-6 rounded-full bg-[#10B981] flex items-center justify-center text-white text-xs"><iconify-icon icon="ph:check-bold"></iconify-icon></div><span class="text-sm">已完成</span>';
    var line = $("line-" + step);
    if (line) line.classList.add("step-line-active");
  }

  function activateStep(step) {
    var head = $("step-" + step + "-head");
    head.classList.add("step-active");
    head.classList.remove("text-[#AAAAAA]");
    if (step === 1) {
      head.innerHTML =
        '<div class="w-6 h-6 rounded-full border border-current flex items-center justify-center text-xs font-bold">1</div><span class="text-sm">选择模板</span>';
    } else if (step === 2) {
      head.innerHTML =
        '<div class="w-6 h-6 rounded-full border border-current flex items-center justify-center text-xs font-bold">2</div><span class="text-sm">填写信息</span>';
    } else {
      head.innerHTML =
        '<div class="w-6 h-6 rounded-full border border-current flex items-center justify-center text-xs font-bold">3</div><span class="text-sm">生成导出</span>';
    }
  }

  window.nextStep = async function () {
    if (currentStep === 1 && !selectedTemplateId) {
      ResumeBridge.showToast("请先选择模板", "warn");
      return;
    }
    if (currentStep === 2) {
      var data = collectForm();
      if (!data.name) {
        ResumeBridge.showToast("请填写姓名", "warn");
        return;
      }
    }
    if (currentStep >= 3) return;

    $("step-" + currentStep).classList.add("hidden");
    if (currentStep === 2) $("step-2").classList.add("hidden");
    markStepDone(currentStep);
    currentStep += 1;
    $("step-" + currentStep).classList.remove("hidden");
    if (currentStep === 2) {
      $("step-2").classList.remove("hidden");
      $("step-2").classList.add("flex");
      scheduleLivePreview();
    }
    activateStep(currentStep);
    $("prev-btn").classList.remove("hidden");

    if (currentStep === 3) {
      $("next-btn").classList.add("hidden");
      await runGenerate();
    }
  };

  window.prevStep = function () {
    if (currentStep <= 1) return;
    var leaving = currentStep;
    $("step-" + leaving).classList.add("hidden");
    if (leaving === 2) {
      $("step-2").classList.remove("flex");
    }
    var leaveHead = $("step-" + leaving + "-head");
    leaveHead.classList.remove("step-active", "text-[#10B981]");
    leaveHead.classList.add("text-[#AAAAAA]");
    activateStep(leaving);
    leaveHead.classList.remove("step-active");
    leaveHead.classList.add("text-[#AAAAAA]");

    currentStep -= 1;
    $("step-" + currentStep).classList.remove("hidden");
    if (currentStep === 2) {
      $("step-2").classList.add("flex");
      scheduleLivePreview();
    }
    activateStep(currentStep);
    var line = $("line-" + currentStep);
    if (line) line.classList.remove("step-line-active");
    if (currentStep === 1) $("prev-btn").classList.add("hidden");
    $("next-btn").classList.remove("hidden");
    $("generating-state").classList.remove("hidden");
    $("success-state").classList.add("hidden");
  };

  async function runGenerate() {
    $("generating-state").classList.remove("hidden");
    $("success-state").classList.add("hidden");
    $("gen-status").textContent = "AI 正在优化排版和文字描述，请稍候";
    try {
      var payload = collectForm();
      var result = await ResumeBridge.apiCall(
        "generate_resume",
        JSON.stringify(payload)
      );
      if (!result.ok) {
        ResumeBridge.showToast(result.error || "生成失败", "warn");
        $("gen-status").textContent = result.error || "生成失败";
        return;
      }
      lastPdfPath = result.pdf_path;
      $("export-path").textContent = result.pdf_path;
      var srcNote =
        result.ai_source === "ollama"
          ? "Ollama 已润色"
          : result.ai_source === "deepseek"
            ? "DeepSeek 云端润色"
            : "本地规则润色（Fallback）";
      $("ai-source-tag").textContent = srcNote;
      var previewImg = $("result-pdf-preview");
      if (previewImg && result.preview_url) {
        previewImg.src = result.preview_url;
      }
      $("generating-state").classList.add("hidden");
      $("success-state").classList.remove("hidden");
      ResumeBridge.showToast("简历生成成功", "ok");
    } catch (e) {
      ResumeBridge.showToast(e.message || String(e), "warn");
      $("gen-status").textContent = e.message || String(e);
    }
  }

  window.exportPdfDone = function () {
    $("success-modal").classList.remove("hidden");
  };

  window.closeModal = function () {
    $("success-modal").classList.add("hidden");
  };

  window.openOutputFolder = async function () {
    await ResumeBridge.apiCall("open_output_folder");
  };

  window.pickPhoto = async function () {
    try {
      var res = await ResumeBridge.apiCall("pick_photo");
      if (res.ok) {
        photoPath = res.path;
        photoUri = res.uri;
        $("photo-hint").textContent = "已选择照片";
        scheduleLivePreview();
      }
    } catch (e) {
      ResumeBridge.showToast(e.message || String(e), "warn");
    }
  };

  document.addEventListener("DOMContentLoaded", async function () {
    [
      "field-name",
      "field-phone",
      "field-email",
      "field-summary",
      "field-skills",
      "exp-company",
      "exp-period",
      "exp-title",
      "exp-desc",
      "edu-school",
      "edu-degree",
      "edu-major",
      "edu-period",
      "proj-name",
      "proj-period",
      "proj-desc",
    ].forEach(function (id) {
      var el = $(id);
      if (el) el.addEventListener("input", scheduleLivePreview);
    });
    $("btn-pick-photo").addEventListener("click", window.pickPhoto);
    $("btn-export-pdf").addEventListener("click", window.exportPdfDone);
    $("btn-open-folder").addEventListener("click", window.openOutputFolder);
    try {
      await loadTemplates();
      var health = await ResumeBridge.apiCall("check_ollama");
      if (!health.online || !health.has_model) {
        ResumeBridge.showToast(health.message || "Ollama 未就绪，将使用降级润色", "warn");
      }
    } catch (e) {
      ResumeBridge.showToast(e.message || String(e), "warn");
    }
  });
})();
