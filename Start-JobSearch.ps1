param([switch]$Check)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$runtime = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies'
$toolDirs = @(
    (Join-Path $PSScriptRoot '.local-tools/bun-windows-x64'),
    (Join-Path $runtime 'python'),
    (Join-Path $runtime 'native/git/cmd'),
    (Join-Path $runtime 'native/poppler/Library/bin'),
    (Join-Path $env:LOCALAPPDATA 'Programs/MiKTeX/miktex/bin/x64')
)
foreach ($toolDir in $toolDirs) {
    if (Test-Path -LiteralPath $toolDir) { $env:PATH = "$toolDir;$env:PATH" }
}
$codexCommand = Get-Command codex.exe -ErrorAction SilentlyContinue
if ($codexCommand) {
    $codexPath = $codexCommand.Source
} else {
    $appBin = Join-Path $env:LOCALAPPDATA 'OpenAI/Codex/bin'
    $candidate = Get-ChildItem -Path "$appBin/*/codex.exe" -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $candidate) { throw 'Codex was not found. Install Codex CLI or the Codex desktop app first.' }
    $codexPath = $candidate.FullName
}
if ($Check) {
    & $codexPath --version
    foreach ($toolName in @('python', 'bun', 'git', 'lualatex', 'xelatex', 'pdftoppm')) {
        $tool = Get-Command $toolName -ErrorAction SilentlyContinue
        if ($tool) { Write-Output "$toolName : $($tool.Source)" }
        else { Write-Output "$toolName : MISSING" }
    }
    exit 0
}
# The desktop-bundled executable is not a standalone daemon package.
# Run its interactive UI in-process, as recommended by its startup error.
$codexArgs = @($args)
$appBinRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'OpenAI/Codex/bin')) + [IO.Path]::DirectorySeparatorChar
$isAppBundled = [IO.Path]::GetFullPath($codexPath).StartsWith($appBinRoot, [StringComparison]::OrdinalIgnoreCase)
$usesRemote = @($codexArgs | Where-Object { $_ -eq '--remote' -or $_ -like '--remote=*' }).Count -gt 0
if ($isAppBundled -and -not $usesRemote -and $codexArgs -notcontains 'agents' -and $codexArgs -notcontains '--no-daemon') {
    $codexArgs = @('--no-daemon') + $codexArgs
}
& $codexPath @codexArgs
exit $LASTEXITCODE
