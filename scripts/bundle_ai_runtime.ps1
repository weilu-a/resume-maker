# Bundle CPU-only Ollama + qwen2.5:3b into dist\ResumeStudio\runtime
# so classmates can use AI without installing Ollama.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path (Join-Path $Root "app\main.py"))) {
  $Root = Get-Location
}

$Dist = Join-Path $Root "dist\ResumeStudio"
$Runtime = Join-Path $Dist "runtime"
$OllamaDst = Join-Path $Runtime "ollama"
$ModelsDst = Join-Path $Runtime "models"

$OllamaSrc = Join-Path $env:LOCALAPPDATA "Programs\Ollama"
$ModelsSrc = Join-Path $env:USERPROFILE ".ollama\models"

Write-Host "Root   : $Root"
Write-Host "Dist   : $Dist"
Write-Host "Ollama : $OllamaSrc"
Write-Host "Models : $ModelsSrc"

if (-not (Test-Path (Join-Path $Dist "ResumeStudio.exe"))) {
  Write-Error "Please build first: run build.bat (missing dist\ResumeStudio\ResumeStudio.exe)"
}

if (-not (Test-Path (Join-Path $OllamaSrc "ollama.exe"))) {
  Write-Error "Ollama not found at $OllamaSrc. Install Ollama first."
}

if (-not (Test-Path (Join-Path $ModelsSrc "manifests"))) {
  Write-Error "Models not found at $ModelsSrc. Run: ollama pull qwen2.5:3b"
}

# Clean previous runtime
if (Test-Path $Runtime) {
  Write-Host "Removing old runtime..."
  Remove-Item $Runtime -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $OllamaDst | Out-Null

Write-Host "[1/3] Copy ollama.exe ..."
Copy-Item (Join-Path $OllamaSrc "ollama.exe") (Join-Path $OllamaDst "ollama.exe") -Force

# CPU (+ optional vulkan) only — skip huge CUDA/ROCm folders (~2.5GB)
$LibSrc = Join-Path $OllamaSrc "lib\ollama"
$LibDst = Join-Path $OllamaDst "lib\ollama"
if (Test-Path $LibSrc) {
  Write-Host "[2/3] Copy CPU inference libs (skip CUDA/ROCm)..."
  New-Item -ItemType Directory -Force -Path $LibDst | Out-Null
  Get-ChildItem $LibSrc -File | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $LibDst $_.Name) -Force
  }
  $VulkanSrc = Join-Path $LibSrc "vulkan"
  if (Test-Path $VulkanSrc) {
    Copy-Item $VulkanSrc (Join-Path $LibDst "vulkan") -Recurse -Force
  }
} else {
  Write-Host "[2/3] No lib\ollama folder — relying on ollama.exe alone"
}

Write-Host "[3/3] Copy model files (qwen2.5:3b, ~1.9GB) — please wait..."
New-Item -ItemType Directory -Force -Path $ModelsDst | Out-Null
# robocopy is faster/more reliable for large trees
$rc = Start-Process -FilePath "robocopy.exe" -ArgumentList @(
  "`"$ModelsSrc`"", "`"$ModelsDst`"", "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/nc", "/ns", "/np"
) -Wait -PassThru
# robocopy exit codes 0-7 are success
if ($rc.ExitCode -ge 8) {
  Write-Error "robocopy failed with code $($rc.ExitCode)"
}

$bytes = (Get-ChildItem $Runtime -Recurse -File | Measure-Object Length -Sum).Sum
Write-Host ("Done. runtime size = {0:N1} GB" -f ($bytes / 1GB))
Write-Host "Path: $Runtime"
Write-Host "Classmates: unzip/run ResumeStudio.exe — AI starts automatically."
