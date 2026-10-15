param([string]$PythonExe, [string]$ExecutableName = 'S5Studio-3.1')
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
# The 3.1 runtime includes the supplied catalogs/template, verified compiler
# and only the explicitly authorized Bulova example. No personal settings,
# recovery, other projects, original corpus or ADB is bundled.
& $python -X utf8 main.py template-info --report (Join-Path $projectRoot 'docs/template-build-profile.json') | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Template funzionante mancante o modificato.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/tailwind.css'))) { throw 'CSS Tailwind mancante: esegui npm ci e npm run build nella cartella frontend.' }
& $python -X utf8 (Join-Path $PSScriptRoot 'update_translations.py') --compile
if ($LASTEXITCODE -ne 0) { throw 'Cataloghi di traduzione non validi: packaging interrotto.' }
& $python -X utf8 (Join-Path $PSScriptRoot 'prepare_runtime.py')
if ($LASTEXITCODE -ne 0) { throw 'Runtime incompleto: packaging interrotto.' }
$runtime = Join-Path $projectRoot 'build/runtime-3.1'
if ($ExecutableName -notmatch '^S5Studio-[0-9]+(\.[0-9]+){1,2}(-aggiornato)?$') { throw 'Nome eseguibile non valido.' }
& $python -m PyInstaller --noconfirm --onefile --windowed --name $executableName --add-data "$runtime;." --distpath $projectRoot --workpath (Join-Path $projectRoot 'build/pyinstaller-3.1') --specpath (Join-Path $projectRoot 'build') main.py
if ($LASTEXITCODE -ne 0) { throw 'Creazione eseguibile fallita.' }
# User preference: inspect the bundle only; do not launch/copy the EXE into
# an isolated environment. Source/editor tests precede packaging separately.
& $python -X utf8 (Join-Path $PSScriptRoot 'verify_bundle.py') (Join-Path $projectRoot ($executableName + '.exe')) --report (Join-Path $projectRoot 'docs/executable-build-3.1.json')
if ($LASTEXITCODE -ne 0) { throw 'Verifica delle risorse incorporate fallita.' }
