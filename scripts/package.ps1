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
# The private 0.10 runtime includes the supplied personal catalogs/template and
# the locally verified compiler. No project/recovery/corpus/ADB is bundled.
& $python -X utf8 main.py template-info --report (Join-Path $projectRoot 'docs/template-build-profile.json') | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Template funzionante mancante o modificato.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/tailwind.css'))) { throw 'CSS Tailwind mancante: esegui npm ci e npm run build nella cartella frontend.' }
& $python -X utf8 (Join-Path $PSScriptRoot 'prepare_runtime.py')
if ($LASTEXITCODE -ne 0) { throw 'Runtime incompleto: packaging interrotto.' }
$runtime = Join-Path $projectRoot 'build/runtime-0.10'
& $python -m PyInstaller --noconfirm --onefile --windowed --name S5Studio-0.10 --add-data "$runtime;." --distpath $projectRoot --workpath (Join-Path $projectRoot 'build/pyinstaller-0.10') --specpath (Join-Path $projectRoot 'build') main.py
if ($LASTEXITCODE -ne 0) { throw 'Creazione eseguibile fallita.' }
