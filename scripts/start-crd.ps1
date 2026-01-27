<#
.SYNOPSIS
  Start Chrome Remote Desktop host on Windows (GitHub Actions friendly)
.DESCRIPTION
  Ensures Chrome Remote Desktop Host is installed, validates inputs, registers the host,
  and provides robust logging and retries.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$AuthCode,
  [Parameter(Mandatory = $true)][string]$Pin,
  [string]$RedirectUrl = "https://remotedesktop.google.com/_/oauthredirect",
  [string]$HostName = $env:COMPUTERNAME,
  [string]$LogPath = "$env:TEMP\\crd_setup.log",
  [switch]$SkipChromeInstall,
  [int]$RetryCount = 3,
  [int]$RetryDelaySeconds = 5
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Log {
  param(
    [Parameter(Mandatory = $true)][string]$Message,
    [ConsoleColor]$Color = [ConsoleColor]::Gray
  )
  $timestamp = Get-Date -Format o
  Write-Host $Message -ForegroundColor $Color
  "$timestamp $Message" | Out-File -FilePath $LogPath -Append -Encoding utf8
}

function Normalize-Pin {
  param([string]$Pin)
  $digits = ($Pin -replace '\\D', '')
  if ($digits.Length -lt 6) { throw "PIN must have at least 6 digits after stripping non-digits" }
  $digits = $digits.Substring(0, [Math]::Min(6, $digits.Length))
  if ($digits.Length -ne 6) { throw "PIN must be exactly 6 digits; got $($digits.Length)" }
  return $digits
}

function Parse-AuthCommand {
  param([string]$Command)
  $cmd = $Command.Trim()
  $codeMatch = [regex]::Match($cmd, '--code="?([^"\s]+)"?')
  $redirectMatch = [regex]::Match($cmd, '--redirect-url="?([^"\s]+)"?')
  $nameMatch = [regex]::Match($cmd, '--name="?([^"\s]+)"?')
  if (-not $codeMatch.Success -or -not $redirectMatch.Success) {
    throw "Auth command missing --code or --redirect-url"
  }
  return @{
    code = $codeMatch.Groups[1].Value
    redirect = $redirectMatch.Groups[1].Value
    name = if ($nameMatch.Success) { $nameMatch.Groups[1].Value } else { $null }
  }
}

function Ensure-CrdHost {
  Write-Log "🔎 Checking Chrome Remote Desktop Host installation..." Cyan
  $hostExe = Join-Path "${env:ProgramFiles(x86)}\\Google\\Chrome Remote Desktop" "CurrentVersion\\remoting_start_host.exe"
  if (Test-Path $hostExe) {
    Write-Log "✅ CRD host present at $hostExe" Green
    return $hostExe
  }

  Write-Log "📥 CRD host not found, downloading..." Cyan
  $urlCandidates = @(
    "https://dl.google.com/dl/chrome-remote-desktop/chromeremotedesktophost.msi",
    "https://dl.google.com/edgedl/chrome-remote-desktop/chromeremotedesktophost.msi"
  )
  $installer = Join-Path $env:TEMP "chromeremotedesktophost.msi"
  foreach ($url in $urlCandidates) {
    try {
      Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
      Write-Log "✅ Downloaded CRD host from $url" Green
      break
    } catch {
      Write-Log "⚠️ Failed to download from $($url): $($_)" Yellow
    }
  }
  if (-not (Test-Path $installer)) { throw "Failed to download Chrome Remote Desktop host MSI" }

  Write-Log "📦 Installing CRD host MSI..." Cyan
  Start-Process msiexec.exe -ArgumentList @("/i", $installer, "/qn", "/norestart") -Wait | Out-Null
  Remove-Item $installer -ErrorAction SilentlyContinue

  if (-not (Test-Path $hostExe)) { throw "CRD host executable not found after install at $hostExe" }
  Write-Log "✅ CRD host installed at $hostExe" Green
  return $hostExe
}

function Ensure-Chrome {
  param([switch]$Skip)
  if ($Skip) { Write-Log "⏩ Skipping Chrome install as requested." Yellow; return }

  $paths = @(
    "${env:ProgramFiles}\\Google\\Chrome\\Application\\chrome.exe",
    "${env:ProgramFiles(x86)}\\Google\\Chrome\\Application\\chrome.exe",
    "$env:LOCALAPPDATA\\Google\\Chrome\\Application\\chrome.exe"
  )
  foreach ($p in $paths) {
    if (Test-Path $p) {
      Write-Log "✅ Chrome present at $p" Green
      return
    }
  }

  Write-Log "📥 Chrome not found, downloading..." Cyan
  $chromeInstaller = Join-Path $env:TEMP "chrome_installer.exe"
  Invoke-WebRequest 'https://dl.google.com/chrome/install/latest/chrome_installer.exe' -OutFile $chromeInstaller -UseBasicParsing
  Start-Process -FilePath $chromeInstaller -ArgumentList '/silent /install' -Wait | Out-Null
  Remove-Item $chromeInstaller -ErrorAction SilentlyContinue
  Write-Log "✅ Chrome installed" Green
}

function Tail-Log {
  $candidates = @(
    "$env:ProgramData\\Google\\Chrome Remote Desktop\\log.txt",
    "$env:LOCALAPPDATA\\Google\\Chrome Remote Desktop\\log.txt"
  )
  foreach ($log in $candidates) {
    if (Test-Path $log) {
      Write-Log "📄 CRD log tail ($log):" Yellow
      try {
        Get-Content $log -Tail 50 | ForEach-Object { Write-Host $_ }
      } catch {
        Write-Log "⚠️ Unable to read $($log): $($_)" Yellow
      }
      break
    }
  }
}

# --- Main ---
Write-Log "🚀 Starting Chrome Remote Desktop setup..." Cyan
Write-Log "OS: $([System.Environment]::OSVersion.VersionString), PS: $($PSVersionTable.PSVersion)" Gray

$pinDigits = Normalize-Pin -Pin $Pin
$parsed = Parse-AuthCommand -Command $AuthCode
if (-not $RedirectUrl) { $RedirectUrl = $parsed.redirect }
if (-not $HostName) { $HostName = if ($parsed.name) { $parsed.name } else { $env:COMPUTERNAME } }

$hostExe = Ensure-CrdHost
Ensure-Chrome -Skip:$SkipChromeInstall

# Start service if exists
$svcName = "Chrome Remote Desktop Service"
$svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
if ($null -ne $svc -and $svc.Status -ne 'Running') {
  Write-Log "▶️ Starting service '$svcName'..." Cyan
  Start-Service $svcName
  $svc.WaitForStatus('Running','00:00:10') | Out-Null
  Write-Log "✅ Service '$svcName' is $((Get-Service $svcName).Status)" Green
}

$args = @("--code=$($parsed.code)", "--redirect-url=$RedirectUrl", "--name=$HostName", "--pin=$pinDigits")

for ($attempt = 1; $attempt -le $RetryCount; $attempt++) {
  Write-Log "▶️ Attempt $($attempt): registering host..." Cyan
  $output = & $hostExe @args 2>&1
  $exit = $LASTEXITCODE
  if ($exit -eq 0) {
    Write-Log "🎉 Chrome Remote Desktop registered successfully." Green
    break
  }
  Write-Log "⚠️ remoting_start_host exited with code $exit" Yellow
  if ($output) { Write-Log "Output:`n$output" Yellow }
  if ($attempt -lt $RetryCount) {
    Write-Log "⏳ Retrying in $RetryDelaySeconds seconds..." Yellow
    Start-Sleep -Seconds $RetryDelaySeconds
  } else {
    Tail-Log
    throw "remoting_start_host failed after $RetryCount attempts (exit $exit)"
  }
}

Write-Log "📌 Host name: $HostName" Gray
Write-Log "🔐 PIN: ****** (masked)" Gray
Write-Log "✅ Done." Green
