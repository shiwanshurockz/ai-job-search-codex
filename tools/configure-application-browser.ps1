$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$configDir = Join-Path $repoRoot '.codex'
$configPath = Join-Path $configDir 'config.toml'
$entry = (Join-Path $PSScriptRoot 'start-application-browser.ps1').Replace('\', '/')
$cwd = $repoRoot.Replace('\', '/')
if (Test-Path -LiteralPath $configPath) {
    Write-Output "Existing configuration preserved: $configPath"
    Write-Output "If moving the repository, update the job_application_browser args and cwd to: $entry and $cwd"
    exit 0
}
New-Item -ItemType Directory -Force $configDir | Out-Null
$entryToml = ConvertTo-Json $entry -Compress
$cwdToml = ConvertTo-Json $cwd -Compress
@"
# Generated local paths. Do not commit this file.
[mcp_servers.job_application_browser]
command = "powershell.exe"
args = ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $entryToml]
cwd = $cwdToml
startup_timeout_sec = 30
tool_timeout_sec = 90
"@ | Set-Content -LiteralPath $configPath -Encoding UTF8
Write-Output "Created $configPath. Restart Codex and check /mcp."
