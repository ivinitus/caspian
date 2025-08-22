# Restart the Vite development server with clean cache
Write-Host "Stopping any running Vite servers..." -ForegroundColor Cyan
try {
  Get-Process | Where-Object { $_.ProcessName -eq "node" -and $_.CommandLine -like "*vite*" } | Stop-Process -Force
} catch {
  Write-Host "No Vite servers found to stop."
}

Write-Host "Clearing Vite cache..." -ForegroundColor Yellow
if (Test-Path "node_modules/.vite") {
  Remove-Item -Recurse -Force "node_modules/.vite" -ErrorAction SilentlyContinue
}

Write-Host "Creating temporary index.html with fix for form submission..." -ForegroundColor Green
$indexPath = Join-Path $PSScriptRoot "index.html"
$indexContent = Get-Content $indexPath -Raw
if (-not ($indexContent -match "preventFormSubmission")) {
  $updatedContent = $indexContent -replace "(<head>)", '$1
  <script>
    // Fix for form submission causing page reload
    window.addEventListener("DOMContentLoaded", function() {
      document.addEventListener("submit", function(e) {
        // Only prevent default for forms within our React app
        if (e.target.closest("#root")) {
          e.preventDefault();
          console.log("Prevented form submission navigation");
        }
      });
    });
  </script>'
  
  Set-Content -Path $indexPath -Value $updatedContent -Force
  Write-Host "Added form submission fix to index.html" -ForegroundColor Green
}

Write-Host "Clearing browser cache..." -ForegroundColor Yellow
Write-Host "Please manually clear your browser cache or open a private/incognito window."

Write-Host "Starting Vite development server..." -ForegroundColor Green
Set-Location $PSScriptRoot
npm run dev
