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

  function bindPreviewInputs(root) {
    if (!root) return;
    root.querySelectorAll("input, textarea").forEach(function (el) {
      el.addEventListener("input", scheduleLivePreview);
    });
  }

  function makeExpCard(data) {
    data = data || {};
    var card = document.createElement("div");
    card.className =
      "exp-item p-4 bg-[#252525] rounded-xl border border-[#3A3A3A] space-y-3";
    card.innerHTML =
      '<div class="flex justify-between items-center">' +
      '<span class="text-xs text-[#666666]">工作经历</span>' +
      '<button type="button" class="btn-remove-item text-[11px] text-[#AAAAAA] hover:text-red-400">删除</button>' +
      "</div>" +
      '<input class="exp-company w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-sm outline-none" placeholder="公司名称"/>' +
      '<div class="grid grid-cols-2 gap-3">' +
      '<input class="exp-title w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-sm outline-none" placeholder="职位"/>' +
      '<input class="exp-period w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-sm outline-none" placeholder="时间"/>' +
      "</div>" +
      '<textarea class="exp-desc w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-xs h-24 outline-none" placeholder="工作描述"></textarea>';
    card.querySelector(".exp-company").value = data.company || "";
    card.querySelector(".exp-title").value = data.title || "";
    card.querySelector(".exp-period").value = data.period || "";
    card.querySelector(".exp-desc").value = data.description || "";
    card.querySelector(".btn-remove-item").addEventListener("click", function () {
      var list = $("exp-list");
      if (list.querySelectorAll(".exp-item").length <= 1) {
        ResumeBridge.showToast("至少保留一条工作经历", "warn");
        return;
      }
      card.remove();
      scheduleLivePreview();
    });
    bindPreviewInputs(card);
    return card;
  }

  function makeEduCard(data) {
    data = data || {};
    var card = document.createElement("div");
    card.className =
      "edu-item p-4 bg-[#252525] rounded-xl border border-[#3A3A3A] space-y-3";
    card.innerHTML =
      '<div class="flex justify-between items-center">' +
      '<span class="text-xs text-[#666666]">教育背景</span>' +
      '<button type="button" class="btn-remove-item text-[11px] text-[#AAAAAA] hover:text-red-400">删除</button>' +
      "</div>" +
      '<input class="edu-school w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-sm outline-none" placeholder="学校"/>' +
      '<div class="grid grid-cols-3 gap-3">' +
      '<input class="edu-degree w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-sm outline-none" placeholder="学历"/>' +
      '<input class="edu-major w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-sm outline-none" placeholder="专业"/>' +
      '<input class="edu-period w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-sm outline-none" placeholder="时间"/>' +
      "</div>";
    card.querySelector(".edu-school").value = data.school || "";
    card.querySelector(".edu-degree").value = data.degree || "";
    card.querySelector(".edu-major").value = data.major || "";
    card.querySelector(".edu-period").value = data.period || "";
    card.querySelector(".btn-remove-item").addEventListener("click", function () {
      var list = $("edu-list");
      if (list.querySelectorAll(".edu-item").length <= 1) {
        ResumeBridge.showToast("至少保留一条教育背景", "warn");
        return;
      }
      card.remove();
      scheduleLivePreview();
    });
    bindPreviewInputs(card);
    return card;
  }

  function makeProjCard(data) {
    data = data || {};
    var card = document.createElement("div");
    card.className =
      "proj-item p-4 bg-[#252525] rounded-xl border border-[#3A3A3A] space-y-3";
    card.innerHTML =
      '<div class="flex justify-between items-center">' +
      '<span class="text-xs text-[#666666]">项目经历</span>' +
      '<button type="button" class="btn-remove-item text-[11px] text-[#AAAAAA] hover:text-red-400">删除</button>' +
      "</div>" +
      '<div class="grid grid-cols-2 gap-3">' +
      '<input class="proj-name w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-sm outline-none" placeholder="项目名称"/>' +
      '<input class="proj-period w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-sm outline-none" placeholder="时间"/>' +
      "</div>" +
      '<textarea class="proj-desc w-full bg-[#1A1A1A] border border-[#3A3A3A] rounded-lg px-3 py-2 text-xs h-20 outline-none" placeholder="项目描述"></textarea>';
    card.querySelector(".proj-name").value = data.name || "";
    card.querySelector(".proj-period").value = data.period || "";
    card.querySelector(".proj-desc").value = data.description || "";
    card.querySelector(".btn-remove-item").addEventListener("click", function () {
      var list = $("proj-list");
      if (list.querySelectorAll(".proj-item").length <= 1) {
        ResumeBridge.showToast("至少保留一条项目经历", "warn");
        return;
      }
      card.remove();
      scheduleLivePreview();
    });
    bindPreviewInputs(card);
    return card;
  }

  function initEntryLists() {
    var expList = $("exp-list");
    var eduList = $("edu-list");
    var projList = $("proj-list");
    expList.appendChild(
      makeExpCard({
        company: "某某科技有限公司",
        title: "高级前端开发工程师",
        period: "2021.06 - 至今",
        description:
          "负责公司网站的开发和维护。使用了 Vue 框架，修复了很多 Bug。参与了几个新功能的上线。",
      })
    );
    eduList.appendChild(
      makeEduCard({
        school: "某名牌大学",
        degree: "本科",
        major: "计算机科学与技术",
        period: "2017.09 - 2021.06",
      })
    );
    projList.appendChild(
      makeProjCard({
        name: "Resume Studio 简历工坊",
        period: "2024.01 - 2024.06",
        description:
          "基于 AI 的简历辅助生成系统，帮助求职者快速打造专业简历。",
      })
    );
    $("btn-add-exp").addEventListener("click", function () {
      expList.appendChild(makeExpCard({}));
      scheduleLivePreview();
    });
    $("btn-add-edu").addEventListener("click", function () {
      eduList.appendChild(makeEduCard({}));
      scheduleLivePreview();
    });
    $("btn-add-proj").addEventListener("click", function () {
      projList.appendChild(makeProjCard({}));
      scheduleLivePreview();
    });
  }

  function collectForm() {
    var experiences = [];
    document.querySelectorAll("#exp-list .exp-item").forEach(function (card) {
      var item = {
        company: card.querySelector(".exp-company").value.trim(),
        period: card.querySelector(".exp-period").value.trim(),
        title: card.querySelector(".exp-title").value.trim(),
        description: card.querySelector(".exp-desc").value.trim(),
      };
      if (item.company || item.title || item.description) experiences.push(item);
    });
    var education = [];
    document.querySelectorAll("#edu-list .edu-item").forEach(function (card) {
      var item = {
        school: card.querySelector(".edu-school").value.trim(),
        period: card.querySelector(".edu-period").value.trim(),
        degree: card.querySelector(".edu-degree").value.trim(),
        major: card.querySelector(".edu-major").value.trim(),
      };
      if (item.school || item.major || item.degree) education.push(item);
    });
    var projects = [];
    document.querySelectorAll("#proj-list .proj-item").forEach(function (card) {
      var item = {
        name: card.querySelector(".proj-name").value.trim(),
        period: card.querySelector(".proj-period").value.trim(),
        description: card.querySelector(".proj-desc").value.trim(),
      };
      if (item.name || item.description) projects.push(item);
    });
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
      projects: projects,
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
    initEntryLists();
    ["field-name", "field-phone", "field-email", "field-summary", "field-skills"].forEach(
      function (id) {
        var el = $(id);
        if (el) el.addEventListener("input", scheduleLivePreview);
      }
    );
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
