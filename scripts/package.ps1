param([string]$PythonExe)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$python = $PythonExe
if (-not $python) {
  $python = Join-Path $env:LOCALAPPDATA 'Programs/Python/Python313/python.exe'
  if (-not (Test-Path -LiteralPath $python -ErrorAction SilentlyContinue)) {
    $python = (Get-Command python.exe -ErrorAction Stop).Source
  }
}
# Desktop distribution only. Watchface ZIP surgery is implemented by
# s5studio/semantic_package.py and is shared by the GUI and apply-template CLI.
# Keep data/ alongside the EXE: the user's preset library is external.
& $python -X utf8 main.py template-info --report (Join-Path $projectRoot 'docs/template-build-profile.json') | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Template funzionante mancante o modificato.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/tailwind.css'))) { throw 'CSS Tailwind mancante: esegui npm ci e npm run build nella cartella frontend.' }
& $python -m PyInstaller --noconfirm --onefile --windowed --name S5Studio-0.8 --add-data "$projectRoot/frontend/index.html;frontend" --add-data "$projectRoot/frontend/app.js;frontend" --add-data "$projectRoot/frontend/editor-controls.js;frontend" --add-data "$projectRoot/frontend/studio.css;frontend" --add-data "$projectRoot/frontend/tailwind.css;frontend" --distpath $projectRoot --workpath (Join-Path $projectRoot 'build/pyinstaller-0.8') --specpath (Join-Path $projectRoot 'build') main.py
if ($LASTEXITCODE -ne 0) { throw 'Creazione eseguibile fallita.' }
