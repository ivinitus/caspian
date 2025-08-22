# Force-update package-lock.json to use the latest prismjs
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue
npm install --force
