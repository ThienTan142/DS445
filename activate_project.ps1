$ErrorActionPreference = "Stop"

# Bật UTF-8 để Python/PowerShell in tiếng Việt không lỗi encoding.
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Kích hoạt môi trường ảo của project.
.\.venv\Scripts\Activate.ps1

Write-Host "Đã kích hoạt môi trường DS445 Shopee Sentiment (.venv)"
Write-Host "Python:" (python --version)
