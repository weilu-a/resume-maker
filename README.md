# 简历工坊 · Resume Studio（resume-maker）

基于 **Python + pywebview** 的桌面应用：本地窗口运行（不是浏览器网站），支持 **简历生成**、**简历优化**、**模拟面试**。

## 功能

1. **生成简历**：选择模板 → 填写信息/上传照片 → AI 润色 → 导出 PDF
2. **简历优化**：上传 PDF → 提取文本 → AI 优化对照 → 导出优化版 PDF
3. **模拟面试**：上传简历、设置岗位难度，多轮对话模拟面试

## AI 说明

- **优先**使用本机 Ollama（或打包内置 runtime）
- 本地不可用时，可走 DeepSeek 云端（在 `.env` 配置 `DEEPSEEK_API_KEY`）
- 都不可用时，简历功能会降级为规则润色

## 快速开始

```bash
# 创建虚拟环境并安装依赖
py -3 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# 启动（也可用 run.bat）
.\.venv\Scripts\python.exe app\main.py
```

可选：安装 [Ollama](https://ollama.com/) 后执行 `ollama pull qwen2.5:3b`。

复制 `.env.example` 为 `.env` 可配置 DeepSeek。

## 目录

| 路径 | 作用 |
|------|------|
| `app/` | Python 后端与桌面入口 |
| `frontend/` | HTML / CSS / JS |
| `templates/` | 简历 HTML 模板 |
| `models/resume/` | 模板元数据与预览 |
| `output/` | 导出的 PDF |
| `scripts/` | 打包内置 AI 等脚本 |

## 打包发布

```bash
build.bat
```

产物在 `dist/ResumeStudio/`（体积较大时会包含内置模型）。

## 技术栈

- 桌面壳：pywebview
- 后端：Python（Jinja2、pdfplumber、xhtml2pdf、requests）
- AI：Ollama / DeepSeek
