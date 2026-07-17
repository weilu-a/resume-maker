/* global ResumeBridge */
(function () {
  var currentInterview = {
  id: null,
  techDirection: '',
  companyType: '',
  difficulty: 'intermediate',
  resumeFile: null,
  resumePath: '',
  resumeText: '',
  startTime: null,
  messages: [],
  summary: ''
};

  var startingInterview = false;
  var sendingMessage = false;
  var exitingInterview = false;

  var interviewHistory = [];
  var currentView = 'setup';

  var techDirectionLabels = {
    frontend: '前端开发',
    backend: '后端开发',
    client: '客户端开发'
  };

  var companyTypeLabels = {
    bigtech: '互联网大厂',
    multinational: '跨国名企',
    soe: '国企/事业单位',
    startup: '成长型创业公司'
  };

  var difficultyLabels = {
    junior: '初级',
    intermediate: '中级',
    senior: '高级'
  };

  function $(id) {
    return document.getElementById(id);
  }

  function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  function formatDate(date) {
    var d = new Date(date);
    return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
  }

  function renderHistory() {
  var list = $('history-list');
  if (!list) return;

  list.innerHTML = '';
  interviewHistory.forEach(function (item) {
    var card = document.createElement('div');
    card.className = 'history-card p-3 rounded-xl cursor-pointer';
    if (currentInterview.id === item.id) {
      card.classList.add('active');
    }
    card.innerHTML =
      '<div class="text-sm font-medium mb-1">' + escapeHtml(item.title || '面试记录') + '</div>' +
      '<div class="text-[10px] text-[#666666]">' +
      escapeHtml(item.date || '') +
      ' • ' +
      (item.messageCount || 0) +
      '轮对话</div>';
    card.onclick = function () {
      loadHistoryItem(item);
    };
    list.appendChild(card);
  });
}

  async function refreshHistoryFromDisk() {
    try {
      var items = await ResumeBridge.apiCall('list_interviews');
      if (Array.isArray(items)) {
        interviewHistory = items;
        renderHistory();
      }
    } catch (e) {
      // 浏览器预览无桥接时忽略
    }
  }

  function syncLocalHistoryItem() {
    var item = interviewHistory.find(function (h) {
      return h.id === currentInterview.id;
    });
    var title =
      (techDirectionLabels[currentInterview.techDirection] || '技术') +
      '-' +
      (companyTypeLabels[currentInterview.companyType] || '面试');
    if (!item) {
      interviewHistory.unshift({
        id: currentInterview.id,
        title: title,
        techDirection: currentInterview.techDirection,
        companyType: currentInterview.companyType,
        difficulty: currentInterview.difficulty,
        resumePath: currentInterview.resumePath || '',
        resumeText: currentInterview.resumeText || '',
        date: formatDate(Date.now()),
        messageCount: currentInterview.messages.length,
        messages: currentInterview.messages.slice()
      });
    } else {
      item.messageCount = currentInterview.messages.length;
      item.messages = currentInterview.messages.slice();
      item.resumeText = currentInterview.resumeText || item.resumeText || '';
      item.resumePath = currentInterview.resumePath || item.resumePath || '';
    }
    renderHistory();
  }

  function loadHistoryItem(item) {
  currentInterview = {
    id: item.id,
    techDirection: item.techDirection || '',
    companyType: item.companyType || '',
    difficulty: item.difficulty || 'intermediate',
    resumeFile: null,
    resumePath: item.resumePath || '',
    resumeText: item.resumeText || '',
    startTime: null,
    messages: (item.messages || []).slice(),
    summary: item.summary || ''
  };
  showHistoryView();
}

  function showSetupView() {
    currentView = 'setup';
    $('setup-view').classList.remove('hidden');
    $('interview-view').classList.add('hidden');
    $('interview-view').classList.remove('flex');
    $('summary-view').classList.add('hidden');
  }

  function showInterviewView() {
    currentView = 'interview';
    $('setup-view').classList.add('hidden');
    $('interview-view').classList.remove('hidden');
    $('interview-view').classList.add('flex');
    $('summary-view').classList.add('hidden');

    $('interview-title').textContent =
      (techDirectionLabels[currentInterview.techDirection] || '技术') + '模拟';
    $('interview-difficulty').textContent =
      difficultyLabels[currentInterview.difficulty] || currentInterview.difficulty;
    $('interview-company').textContent =
      companyTypeLabels[currentInterview.companyType] || currentInterview.companyType;

    $('chat-input-container').classList.remove('hidden');
    $('history-summary-container').classList.add('hidden');

    renderMessages();
    scrollToBottom();
  }

  function showHistoryView() {
    currentView = 'interview';
    $('setup-view').classList.add('hidden');
    $('interview-view').classList.remove('hidden');
    $('interview-view').classList.add('flex');
    $('summary-view').classList.add('hidden');

    $('interview-title').textContent =
      (techDirectionLabels[currentInterview.techDirection] || '技术') + '历史';
    $('interview-difficulty').textContent =
      difficultyLabels[currentInterview.difficulty] || currentInterview.difficulty;
    $('interview-company').textContent =
      companyTypeLabels[currentInterview.companyType] || currentInterview.companyType;

    $('chat-input-container').classList.add('hidden');
    $('history-summary-container').classList.remove('hidden');

    renderMessages();
    scrollToBottom();
  }

  function showSummaryView() {
    currentView = 'summary';
    $('setup-view').classList.add('hidden');
    $('interview-view').classList.add('hidden');
    $('interview-view').classList.remove('flex');
    $('summary-view').classList.remove('hidden');

    $('summary-subtitle').textContent =
      (techDirectionLabels[currentInterview.techDirection] || '技术') +
      ' · ' +
      (companyTypeLabels[currentInterview.companyType] || '企业') +
      ' · ' +
      (difficultyLabels[currentInterview.difficulty] || currentInterview.difficulty);

    var contentEl = $('summary-content');
    if (currentInterview.summary) {
      contentEl.innerHTML = parseMarkdown(currentInterview.summary);
    } else {
      contentEl.innerHTML =
        '<div class="text-center text-[#666666] py-8">' +
        '<iconify-icon class="text-4xl text-[#4F8CFF] mb-4 inline-block" icon="ph:file-text"></iconify-icon>' +
        '<p>暂无面试总结</p>' +
        '</div>';
    }
  }

  function parseMarkdown(text) {
    if (!text) return '';
    var html = text
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    html = html.replace(/^## (.+)$/gm, '<h3 class="text-lg font-bold text-white mt-6 mb-3">$1</h3>');
    html = html.replace(/^### (.+)$/gm, '<h4 class="text-base font-semibold text-white mt-4 mb-2">$1</h4>');
    html = html.replace(/^\- (.+)$/gm, '<li class="text-sm text-[#AAAAAA] mb-2">$1</li>');
    html = html.replace(/<\/li>\n<li/g, '</li>\n<li');
    html = html.replace(/(<li[^>]*>[\s\S]*<\/li>)/g, '<ul class="list-disc pl-5 space-y-1">$1</ul>');
    html = html.replace(/<\/ul>\n<ul>/g, '');
    html = html.replace(/\n\n/g, '<br><br>');
    return html;
  }

  function renderMessages() {
    var container = $('chat-container');
    var typing = $('typing-indicator');
    if (!container || !typing) return;

    while (container.firstChild && container.firstChild !== typing) {
      container.removeChild(container.firstChild);
    }

    currentInterview.messages.forEach(function (msg) {
      if (msg.role === 'user') {
        addUserMessage(msg.content);
      } else {
        addAiMessage(msg.content);
      }
    });
  }

  function addUserMessage(content) {
    var container = $('chat-container');
    if (!container) return;

    var userMsg = document.createElement('div');
    userMsg.className = 'flex items-start space-x-4 flex-row-reverse space-x-reverse max-w-4xl ml-auto';
    userMsg.innerHTML =
      '<div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center border-2 border-[#3A3A3A] flex-none">' +
      '<iconify-icon icon="ph:user-bold" class="text-xl"></iconify-icon>' +
      '</div>' +
      '<div class="chat-bubble-user p-5 shadow-lg max-w-[80%]">' +
      '<div class="text-sm leading-relaxed"><p>' +
      escapeHtml(content) +
      '</p></div>' +
      '</div>';

    var typing = $('typing-indicator');
    container.insertBefore(userMsg, typing);
  }

  function addAiMessage(content, callback) {
    var container = $('chat-container');
    if (!container) return;

    var aiMsg = document.createElement('div');
    aiMsg.className = 'flex items-start space-x-4 max-w-4xl';
    aiMsg.innerHTML =
      '<div class="w-10 h-10 rounded-full bg-[#3A3A3A] flex items-center justify-center text-[#4F8CFF] flex-none">' +
      '<iconify-icon icon="ph:robot-fill" class="text-2xl"></iconify-icon>' +
      '</div>' +
      '<div class="chat-bubble-ai p-5 shadow-lg max-w-[80%]">' +
      '<div class="markdown-content text-sm leading-relaxed">' +
      '<p></p>' +
      '</div>' +
      '</div>';

    var typing = $('typing-indicator');
    container.insertBefore(aiMsg, typing);

    var textElement = aiMsg.querySelector('p');
    typeWriterEffect(textElement, content, callback);
  }

  function typeWriterEffect(element, text, callback) {
    var index = 0;
    var speed = 18;
    text = text || '';

    function type() {
      if (index < text.length) {
        element.textContent += text.charAt(index);
        index++;
        scrollToBottom();
        setTimeout(type, speed);
      } else if (callback) {
        callback();
      }
    }

    type();
  }

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  function scrollToBottom() {
    var container = $('chat-container');
    if (container) {
      requestAnimationFrame(function () {
        container.scrollTop = container.scrollHeight;
      });
    }
  }

  function buildSavePayload() {
  return {
    id: currentInterview.id,
    title:
      (techDirectionLabels[currentInterview.techDirection] || '技术') +
      '-' +
      (companyTypeLabels[currentInterview.companyType] || '面试'),
    tech_direction: currentInterview.techDirection,
    company_type: currentInterview.companyType,
    difficulty: currentInterview.difficulty,
    start_time: currentInterview.startTime,
    messages: currentInterview.messages,
    resume_text: currentInterview.resumeText || '',
    resume_path: currentInterview.resumePath || '',
    summary: currentInterview.summary || ''
  };
}

  function resetSetupForm() {
    currentInterview = {
      id: null,
      techDirection: '',
      companyType: '',
      difficulty: 'intermediate',
      resumeFile: null,
      resumePath: '',
      resumeText: '',
      startTime: null,
      messages: []
    };

    var radios = document.querySelectorAll('input[name="tech-direction"]');
    radios.forEach(function (radio) {
      radio.checked = false;
    });

    var btns = document.querySelectorAll('.difficulty-btn');
    btns.forEach(function (btn) {
      btn.classList.remove('active');
      btn.classList.remove('bg-[#3A3A3A]', 'text-white');
      btn.classList.add('text-[#AAAAAA]');
      if (btn.dataset.difficulty === 'intermediate') {
        btn.classList.add('active');
        btn.classList.add('bg-[#3A3A3A]', 'text-white');
        btn.classList.remove('text-[#AAAAAA]');
      }
    });

    $('company-type').value = 'bigtech';
    clearResume();
  }

  async function persistAndExit() {
    if (exitingInterview) return;
    exitingInterview = true;
    try {
      if (currentInterview.id && currentInterview.messages.length) {
        try {
          var res = await ResumeBridge.apiCall(
            'save_interview',
            JSON.stringify(buildSavePayload())
          );
          if (res && res.ok) {
            ResumeBridge.showToast('面试记录已保存', 'ok');
          } else {
            ResumeBridge.showToast((res && res.error) || '保存失败', 'warn');
          }
        } catch (e) {
          ResumeBridge.showToast(e.message || String(e), 'warn');
        }
      }
      await refreshHistoryFromDisk();
      renderHistory();
    } finally {
      exitingInterview = false;
    }
  }

  async function generateAndShowSummary() {
    var contentEl = $('summary-content');
    contentEl.innerHTML =
      '<div class="text-center text-[#666666] py-8">' +
      '<iconify-icon class="text-4xl text-[#4F8CFF] mb-4 inline-block animate-spin" icon="ph:loader"></iconify-icon>' +
      '<p>AI 正在生成面试总结...</p>' +
      '</div>';

    showSummaryView();

    try {
      var payload = {
        company_type: currentInterview.companyType,
        tech_direction: currentInterview.techDirection,
        difficulty: currentInterview.difficulty,
        resume_text: currentInterview.resumeText || '',
        messages: currentInterview.messages.map(function (m) {
          return { role: m.role, content: m.content };
        })
      };

      var result = await ResumeBridge.apiCall('interview_summary', JSON.stringify(payload));

      if (!result || !result.ok) {
        currentInterview.summary = '';
        contentEl.innerHTML =
          '<div class="text-center text-[#666666] py-8">' +
          '<iconify-icon class="text-4xl text-[#FF4D4F] mb-4 inline-block" icon="ph:alert-circle"></iconify-icon>' +
          '<p>AI 生成总结失败</p>' +
          '<p class="text-xs mt-2 text-[#888]">' + ((result && result.error) || '') + '</p>' +
          '</div>';
        ResumeBridge.showToast((result && result.error) || '生成总结失败', 'warn');
      } else {
        currentInterview.summary = result.summary || '';
        contentEl.innerHTML = parseMarkdown(currentInterview.summary);
        ResumeBridge.showToast('面试总结已生成', 'ok');
      }

      await persistAndExit();
    } catch (e) {
      currentInterview.summary = '';
      contentEl.innerHTML =
        '<div class="text-center text-[#666666] py-8">' +
        '<iconify-icon class="text-4xl text-[#FF4D4F] mb-4 inline-block" icon="ph:alert-circle"></iconify-icon>' +
        '<p>生成总结时发生错误</p>' +
        '<p class="text-xs mt-2 text-[#888]">' + (e.message || String(e)) + '</p>' +
        '</div>';
      ResumeBridge.showToast(e.message || String(e), 'warn');
      await persistAndExit();
    }
  }

  async function sendMessage() {
    if (sendingMessage || exitingInterview) return;

    var input = $('chat-input');
    var text = input.value.trim();
    if (!text) return;

    sendingMessage = true;
    var typing = $('typing-indicator');

    try {
      currentInterview.messages.push({ role: 'user', content: text, timestamp: Date.now() });
      addUserMessage(text);
      input.value = '';
      scrollToBottom();
      syncLocalHistoryItem();

      typing.style.display = 'flex';
      scrollToBottom();

      var payload = {
        company_type: currentInterview.companyType,
        tech_direction: currentInterview.techDirection,
        difficulty: currentInterview.difficulty,
        resume_text: currentInterview.resumeText || '',
        messages: currentInterview.messages.map(function (m) {
          return { role: m.role, content: m.content };
        })
      };

      var result = await ResumeBridge.apiCall('interview_reply', JSON.stringify(payload));
      typing.style.display = 'none';

      if (!result || !result.ok) {
        ResumeBridge.showToast((result && result.error) || '面试官回复失败', 'warn');
        return;
      }

      var speech = result.speech || '';
      var shouldEnd = !!result.end_interview;

      currentInterview.messages.push({ role: 'ai', content: speech, timestamp: Date.now() });
      syncLocalHistoryItem();

      addAiMessage(speech, function () {
        if (shouldEnd) {
          ResumeBridge.showToast('面试官已结束本场面试', 'ok');
          persistAndExit();
        }
      });
    } catch (e) {
      typing.style.display = 'none';
      ResumeBridge.showToast(e.message || String(e), 'warn');
    } finally {
      sendingMessage = false;
    }
  }

  async function startInterview() {
    if (startingInterview) return;

    if (!currentInterview.techDirection) {
      ResumeBridge.showToast('请选择技术方向', 'warn');
      return;
    }

    startingInterview = true;
    try {
      currentInterview.resumeText = currentInterview.resumeText || '';

      if (currentInterview.resumePath) {
        ResumeBridge.showToast('正在从简历 PDF 读取文字...', '');
        var extracted = await ResumeBridge.apiCall(
          'extract_pdf_text',
          currentInterview.resumePath
        );
        if (!extracted || !extracted.ok) {
          ResumeBridge.showToast(
            (extracted && extracted.error) || '简历文字提取失败',
            'warn'
          );
          return;
        }
        currentInterview.resumeText = extracted.text || '';
        if (!currentInterview.resumeText.trim()) {
          ResumeBridge.showToast('未能从 PDF 提取到文字（可能是扫描件）', 'warn');
        } else {
          ResumeBridge.showToast(
            '已读取简历文字 ' +
              (extracted.chars || currentInterview.resumeText.length) +
              ' 字',
            'ok'
          );
        }
      } else if (currentInterview.resumeFile && !currentInterview.resumePath) {
        ResumeBridge.showToast(
          '当前为浏览器预览，无法解析 PDF；请用 python app/main.py 启动后选择文件',
          'warn'
        );
      }

      currentInterview.id = generateId();
      currentInterview.companyType = $('company-type').value;
      currentInterview.startTime = Date.now();
      currentInterview.messages = [];

      var openingRes = await ResumeBridge.apiCall(
        'get_interview_opening',
        currentInterview.companyType
      );
      if (!openingRes || !openingRes.ok || !openingRes.speech) {
        ResumeBridge.showToast(
          (openingRes && openingRes.error) || '获取开场白失败',
          'warn'
        );
        return;
      }

      currentInterview.messages.push({
        role: 'ai',
        content: openingRes.speech,
        timestamp: Date.now()
      });
      syncLocalHistoryItem();
      showInterviewView();
    } catch (e) {
      ResumeBridge.showToast(e.message || String(e), 'warn');
    } finally {
      startingInterview = false;
    }
  }

  function endInterview() {
    generateAndShowSummary();
  }

  async function restartInterview() {
    if (!currentInterview.id) return;

    var tech = currentInterview.techDirection;
    var diff = currentInterview.difficulty;
    var company = currentInterview.companyType || $('company-type').value;
    var resumeFile = currentInterview.resumeFile;
    var resumePath = currentInterview.resumePath;
    var resumeText = currentInterview.resumeText;

    try {
      var openingRes = await ResumeBridge.apiCall('get_interview_opening', company);
      var opening =
        openingRes && openingRes.ok && openingRes.speech
          ? openingRes.speech
          : '你好，请先做一个自我介绍。';

      currentInterview = {
        id: currentInterview.id,
        techDirection: tech,
        companyType: company,
        difficulty: diff,
        resumeFile: resumeFile,
        resumePath: resumePath,
        resumeText: resumeText,
        startTime: Date.now(),
        messages: [{ role: 'ai', content: opening, timestamp: Date.now() }]
      };

      syncLocalHistoryItem();
      showInterviewView();
    } catch (e) {
      ResumeBridge.showToast(e.message || String(e), 'warn');
    }
  }

  function selectTechDirection(el, tech) {
    currentInterview.techDirection = tech;
  }

  function selectDifficulty(el, difficulty) {
    document.querySelectorAll('.difficulty-btn').forEach(function (btn) {
      btn.classList.remove('active');
      btn.classList.remove('bg-[#3A3A3A]', 'text-white');
      btn.classList.add('text-[#AAAAAA]');
    });
    el.classList.add('active');
    el.classList.add('bg-[#3A3A3A]', 'text-white');
    el.classList.remove('text-[#AAAAAA]');
    currentInterview.difficulty = difficulty;
  }

  function applyResumeSelected(name, path) {
    currentInterview.resumeFile = name ? { name: name } : null;
    currentInterview.resumePath = path || '';
    currentInterview.resumeText = '';
    $('resume-filename').textContent = name || '已选择文件';
    $('resume-selected').classList.remove('hidden');
    $('resume-drop-zone').classList.add('hidden');
  }

  async function pickResume() {
    try {
      var res = await ResumeBridge.apiCall('pick_pdf');
      if (res && res.cancelled) return;
      if (!res || !res.ok) {
        ResumeBridge.showToast((res && res.error) || '选择文件失败', 'warn');
        return;
      }
      applyResumeSelected(res.name || '已选择文件', res.path || '');
    } catch (e) {
      $('resume-input').click();
    }
  }

  function handleResumeUpload(input) {
    if (input.files && input.files[0]) {
      var file = input.files[0];
      if (!/\.pdf$/i.test(file.name)) {
        ResumeBridge.showToast('目前仅支持 PDF 格式简历', 'warn');
        input.value = '';
        return;
      }
      applyResumeSelected(file.name, '');
      ResumeBridge.showToast(
        '已选择文件，但浏览器预览无法解析 PDF；开始面试请用桌面版',
        'warn'
      );
    }
  }

  function clearResume() {
    currentInterview.resumeFile = null;
    currentInterview.resumePath = '';
    currentInterview.resumeText = '';
    $('resume-input').value = '';
    $('resume-selected').classList.add('hidden');
    $('resume-drop-zone').classList.remove('hidden');
  }

  window.showSetupView = showSetupView;
  window.showInterviewView = showInterviewView;
  window.showHistoryView = showHistoryView;
  window.showSummaryView = showSummaryView;
  window.startInterview = startInterview;
  window.endInterview = endInterview;
  window.restartInterview = restartInterview;
  window.sendMessage = sendMessage;
  window.selectTechDirection = selectTechDirection;
  window.selectDifficulty = selectDifficulty;
  window.pickResume = pickResume;
  window.handleResumeUpload = handleResumeUpload;
  window.clearResume = clearResume;

  async function refreshAiBadge() {
    var badge = $('ollama-badge');
    if (!badge) return;
    try {
      var health = await ResumeBridge.apiCall('check_ollama');
      if (health && health.online && health.has_model) {
        badge.textContent = 'Ollama 优先';
        badge.className =
          'text-[10px] px-2 py-0.5 rounded bg-[#10B981]/20 text-[#10B981]';
        return;
      }
      var ds = await ResumeBridge.apiCall('check_deepseek');
      if (ds && ds.configured) {
        badge.textContent = 'DeepSeek 备用';
        badge.className =
          'text-[10px] px-2 py-0.5 rounded bg-[#10B981]/20 text-[#10B981]';
        return;
      }
      badge.textContent = 'AI 未就绪';
      badge.className =
        'text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-400';
      ResumeBridge.showToast(
        (health && health.message) || '请启动 Ollama，或在 .env 配置 DEEPSEEK_API_KEY',
        'warn'
      );
    } catch (e) {
      badge.textContent = '检测失败';
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    $('chat-input').addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    refreshHistoryFromDisk();
    renderHistory();
    refreshAiBadge();
  });
})();
