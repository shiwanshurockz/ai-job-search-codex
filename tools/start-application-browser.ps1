$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
$node = Get-Command node.exe -ErrorAction SilentlyContinue
if ($node) { $nodePath = $node.Source } else {
    $nodePath = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
}
$entry = Join-Path $PSScriptRoot 'browser/node_modules/@playwright/mcp/cli.js'
if (-not (Test-Path $nodePath)) { throw 'Node.js 18+ is required for the application browser.' }
if (-not (Test-Path $entry)) { throw 'Install browser dependencies with: bun install --cwd tools/browser --ignore-scripts' }
& $nodePath $entry --browser chrome --user-data-dir (Join-Path $repoRoot '.local-tools/application-browser') --output-dir (Join-Path $repoRoot '.local-tools/browser-output') --no-webmcp @args
exit $LASTEXITCODE
