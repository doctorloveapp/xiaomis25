$ErrorActionPreference = 'Stop'
$toolRoot = $PSScriptRoot
$release = 'https://github.com/m0tral/EasyFace/releases/download/v4.23/EasyFace_Gen2_CompilerV423.zip'
$archive = Join-Path $toolRoot 'EasyFace_Gen2_CompilerV423.zip'
$target = Join-Path $toolRoot 'easyface-4.23'
$zipHash = '5B62773369C10C3402F369E8AA579F13393AF359D0214C0D979464E5CC776CEF'
$exeHash = 'BFB8C3B6666B79DE165884D832C69D46E5BBFA581C65C1E188CDDFC4B9D6723A'
if (-not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri $release -OutFile $archive
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $zipHash) {
    throw 'Hash del download inatteso: il file non è la release provata.'
}
Expand-Archive -LiteralPath $archive -DestinationPath $target -Force
if ((Get-FileHash -LiteralPath (Join-Path $target 'Compiler.exe') -Algorithm SHA256).Hash -ne $exeHash) {
    throw 'Hash del compilatore inatteso.'
}
Write-Output 'EasyFace Compiler 4.23 per S5 pronto. Nessuna installazione di sistema eseguita.'
