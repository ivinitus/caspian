# Restart the Vite development server
Write-Host "Stopping any running Vite servers..." -ForegroundColor Yellow
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "vite" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Clearing Vite cache..." -ForegroundColor Yellow
if (Test-Path "node_modules/.vite") {
  Remove-Item -Recurse -Force "node_modules/.vite" -ErrorAction SilentlyContinue
}

# Clear browser storage data via the dev tools
Write-Host "NOTE: You may need to clear your browser cache and local storage manually" -ForegroundColor Cyan

Write-Host "Starting Vite development server..." -ForegroundColor Green
Set-Location $PSScriptRoot
npm run dev
