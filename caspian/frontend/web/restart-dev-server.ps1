# Restart the Vite development server
Write-Host "Stopping any running npm processes..." -ForegroundColor Yellow
Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*npm*" } | Stop-Process -Force

# Clear npm cache
Write-Host "Clearing npm cache..." -ForegroundColor Yellow
npm cache clean --force

# Start the development server
Write-Host "Starting development server..." -ForegroundColor Green
npm run dev
