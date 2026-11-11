# Bloodborne PC path tracing mod: installs over (or removes from) a Bloodborne PC folder.
# -Elevated is set by the script itself when it restarts with administrator rights.
param([switch]$Uninstall, [string]$Target, [switch]$Elevated)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$man = Get-Content -LiteralPath (Join-Path $here 'manifest.json') -Raw | ConvertFrom-Json
$files = @($man.files.PSObject.Properties)
$markerName = 'rt-installed.json'
$backupName = 'rt-backup'

# The elevated window closes on exit, so it waits for a key first.
function Exit-Script([int]$code) {
    if ($Elevated) { Write-Host ''; Read-Host 'Press Enter to close' | Out-Null }
    exit $code
}

function Stop-Install([string]$msg) {
    Write-Host ''
    Write-Host "ERROR: $msg" -ForegroundColor Red
    Write-Host 'Nothing was installed or removed.' -ForegroundColor Red
    Exit-Script 1
}

trap {
    Write-Host ''
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Exit-Script 1
}

function Test-Writable([string]$dir) {
    try {
        $probe = Join-Path $dir ".rt-write-test-$PID"
        [IO.File]::WriteAllText($probe, 'x')
        Remove-Item -LiteralPath $probe -Force
        return $true
    } catch { return $false }
}

function Test-Port([string]$dir) {
    return $dir -and (Test-Path -LiteralPath (Join-Path $dir 'bbport-files.json')) -and
        (Test-Path -LiteralPath (Join-Path $dir 'bin'))
}

function Get-Sha([string]$path) {
    return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

# Find the Bloodborne PC folder: -Target, the folder around this one, or ask.
if (-not $Target) {
    foreach ($c in @((Split-Path $here -Parent), $here, (Get-Location).Path)) {
        if (Test-Port $c) { $Target = $c; break }
    }
}
if (-not $Target) {
    Add-Type -AssemblyName System.Windows.Forms
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = 'Pick your Bloodborne PC folder (the one with Bloodborne.exe)'
    if ($dlg.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { Stop-Install 'No folder picked.' }
    $Target = $dlg.SelectedPath
}
$Target = (Resolve-Path -LiteralPath $Target).Path
if (-not (Test-Port $Target)) { Stop-Install "$Target is not a Bloodborne PC folder (no bbport-files.json / bin)." }
Write-Host "Bloodborne PC folder: $Target"

$running = Get-Process -Name 'bb-probe', 'Bloodborne', 'Play Bloodborne' -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -and $_.Path.StartsWith($Target, [StringComparison]::OrdinalIgnoreCase) }
if ($running) { Stop-Install 'Close the game and the launcher first.' }

# A protected folder (Program Files and the like) needs administrator rights: ask for them once.
if (-not ((Test-Writable $Target) -and (Test-Writable (Join-Path $Target 'bin')))) {
    if ($Elevated) { Stop-Install "Windows does not allow writing to $Target, even as administrator." }
    Write-Host 'This folder needs administrator rights. Windows will ask for them now.' -ForegroundColor Yellow
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$($MyInvocation.MyCommand.Path)`"",
        '-Target', "`"$Target`"", '-Elevated')
    if ($Uninstall) { $argList += '-Uninstall' }
    try {
        $p = Start-Process powershell.exe -Verb RunAs -ArgumentList $argList -Wait -PassThru
    } catch { Stop-Install 'Administrator rights were refused.' }
    if ($p.ExitCode -ne 0) { Write-Host ''; Write-Host 'ERROR: the administrator window reported a failure (see that window).' -ForegroundColor Red }
    else { Write-Host 'Done in the administrator window.' -ForegroundColor Green }
    exit $p.ExitCode
}

$marker = Join-Path $Target $markerName
$backup = Join-Path $Target $backupName
$ini = Join-Path $Target 'bbport.ini'
$portList = Get-Content -LiteralPath (Join-Path $Target 'bbport-files.json') -Raw | ConvertFrom-Json
$folderVersion = $portList.version
$prev = $null
if (Test-Path -LiteralPath $marker) { $prev = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json }
# Bloodborne PC was updated after path tracing was installed: the backup holds the old version's files.
$stale = $prev -and $prev.base_version -and ($prev.base_version -ne $folderVersion)

# The sha256 Bloodborne PC lists for a file of this folder, $null when it lists none.
function Get-PortSha([string]$rel) {
    $p = $portList.files.PSObject.Properties[$rel]
    if ($p) { return $p.Value }
    return $null
}

# Path tracing is switched on by environment variables. SuperMedo's launcher passes the ones in its
# Advanced > Diagnostics > Extra variables field (extra_env in %APPDATA%\bbport-launcher\settings.json)
# to the game, so the launcher itself is not replaced. These are the tuned pt2 values.
$settings = Join-Path $env:APPDATA 'bbport-launcher\settings.json'
$rtEnv = @('BB_RT=1', 'BB_RT_DIRECT=1', 'BB_RT_GI=1', 'BB_RT_COMPACT=0', 'BB_RT_REFIT_BUDGET=0', 'BB_RT_FILL_LIGHT=off',
    'BB_HDR_GAMMA=0', 'BB_RT_FILL_ENCLOSED=0.1', 'BB_RT_SKIN_ALPHA=1', 'BB_RT_FX_FOG=0', 'BB_RT_FX_FOG_G=0',
    'BB_RT_GI_LAST_BOUNCE_CACHE=1', 'BB_RT_GI_SER=1', 'BB_RT_GI_PIPELINE=1', 'BB_RT_RESTIR_GI=1', 'BB_RT_DLSS_RR=0',
    'BB_RT_KEEP_GI=1')
$rtKeys = @($rtEnv | ForEach-Object { $_.Split('=')[0] })
$envRx = [regex]'"extra_env"\s*:\s*"((?:[^"\\]|\\.)*)"'

# The extra_env value as written in the file (JSON-escaped), '' when missing, $null without the file.
function Get-ExtraEnv {
    if (-not (Test-Path -LiteralPath $settings)) { return $null }
    $m = $envRx.Match([IO.File]::ReadAllText($settings))
    if ($m.Success) { return $m.Groups[1].Value }
    return ''
}

# Writes extra_env, keeping the rest of the file as it is; checks the result is still valid JSON.
function Set-ExtraEnv([string]$value) {
    $line = '"extra_env": "' + $value + '"'
    $old = $null
    if (Test-Path -LiteralPath $settings) {
        $old = [IO.File]::ReadAllText($settings)
        if ($envRx.IsMatch($old)) { $raw = $envRx.Replace($old, [Text.RegularExpressions.MatchEvaluator] { param($m) $line }, 1) }
        elseif ($old.Trim() -match '^\{\s*\}$') { $raw = "{`n  $line`n}`n" }
        else { $raw = ([regex]'\{').Replace($old, "{`n  $line,", 1) }
    } else {
        New-Item -ItemType Directory -Force -Path (Split-Path $settings -Parent) | Out-Null
        $raw = "{`n  $line`n}`n"
    }
    [IO.File]::WriteAllText($settings, $raw, (New-Object Text.UTF8Encoding $false))
    try { $null = [IO.File]::ReadAllText($settings) | ConvertFrom-Json }
    catch {
        if ($null -ne $old) { [IO.File]::WriteAllText($settings, $old, (New-Object Text.UTF8Encoding $false)) }
        throw "could not write the launcher settings ($settings)"
    }
}

function Split-Env([string]$value) { return @(($value -split '\s+') | Where-Object { $_ }) }
function Test-RtToken([string]$token) { return $rtKeys -contains $token.Split('=')[0] }

# The upscaler line of bbport.ini: its value, '' when the line is missing, $null without the file.
function Get-Upscaler {
    if (-not (Test-Path -LiteralPath $ini)) { return $null }
    foreach ($line in Get-Content -LiteralPath $ini) {
        if ($line -match '^\s*upscaler\s*=\s*(.*?)\s*$') { return $Matches[1] }
    }
    return ''
}

# Sets the upscaler line; '' removes it.
function Set-Upscaler([string]$value) {
    $lines = @()
    if (Test-Path -LiteralPath $ini) { $lines = @(Get-Content -LiteralPath $ini | Where-Object { $_ -notmatch '^\s*upscaler\s*=' }) }
    else { $lines = @('# bbport settings (in-game menu: Insert / L3+R3)') }
    if ($value -and $lines.Count -and $lines[0].StartsWith('#')) {
        $lines = @($lines[0], "upscaler=$value") + @($lines | Select-Object -Skip 1)
    } elseif ($value) {
        $lines = @("upscaler=$value") + $lines
    }
    Set-Content -LiteralPath $ini -Value $lines -Encoding ASCII
}

if ($Uninstall) {
    if (-not (Test-Path -LiteralPath $marker)) { Stop-Install 'Path tracing is not installed in this folder.' }
    $n = 0
    foreach ($f in $files) {
        $rel = $f.Name
        $dst = Join-Path $Target $rel
        if ($stale) {
            # The backup is of the old version: never put it back. Remove only what the port does not list.
            if (-not (Test-Path -LiteralPath $dst)) { continue }
            $want = Get-PortSha $rel
            if (-not $want) { Remove-Item -LiteralPath $dst -Force; $n++ }
            elseif ((Get-Sha $dst) -ne $want) {
                Write-Host "  $rel is not Bloodborne PC $folderVersion's own file: repair or reinstall Bloodborne PC." -ForegroundColor Yellow
            }
            continue
        }
        if ($f.Value.stock) {
            $src = Join-Path $backup $rel
            if (Test-Path -LiteralPath $src) {
                Copy-Item -LiteralPath $src -Destination $dst -Force
                $n++
            } else {
                Write-Host "  no backup for $rel, left as is" -ForegroundColor Yellow
            }
        } elseif (Test-Path -LiteralPath $dst) {
            Remove-Item -LiteralPath $dst -Force
            $n++
        }
    }
    $state = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    $old = $state.upscaler
    if ($null -ne $old) { Set-Upscaler $old }
    # No bbport.ini before the install: drop the one the install made if it holds no other setting.
    if ($state.ini_existed -eq $false -and (Test-Path -LiteralPath $ini)) {
        $other = @(Get-Content -LiteralPath $ini | Where-Object { $_ -notmatch '^\s*(#.*)?$' -and $_ -notmatch '^\s*upscaler\s*=' })
        if ($other.Count -eq 0) { Remove-Item -LiteralPath $ini -Force }
    }
    # Our variables leave the launcher's Extra variables; the ones they replaced come back.
    $cur = Get-ExtraEnv
    if ($null -ne $cur) {
        $tokens = @(Split-Env $cur | Where-Object { -not (Test-RtToken $_) }) + @(Split-Env ([string]$state.env_replaced))
        Set-ExtraEnv ($tokens -join ' ')
    }
    Remove-Item -LiteralPath $backup -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $marker -Force
    Write-Host ''
    Write-Host "Path tracing removed: $n files restored. The folder is back to Bloodborne PC $folderVersion." -ForegroundColor Green
    Exit-Script 0
}

# Install.
$installed = Test-Path -LiteralPath $marker
if ($installed -and -not $stale -and $prev.rt_version -ne $man.rt_version) {
    # Another version's backup holds other files: its own uninstaller has to put them back first.
    Stop-Install "Path tracing $($prev.rt_version) is installed here. Run the Uninstall Path Tracing.bat of $($prev.rt_version) first, then install $($man.rt_version)."
}
if ($folderVersion -ne $man.base_version) {
    Stop-Install "This mod needs Bloodborne PC $($man.base_version); this folder has $folderVersion. Get $($man.base_version) from https://github.com/Supermedo/bloodborne_pc/releases/tag/windows-v$($man.base_version)"
}
if ($stale) {
    Write-Host "Bloodborne PC was updated to $folderVersion after path tracing $($prev.rt_version) was installed: installing fresh." -ForegroundColor Yellow
    Remove-Item -LiteralPath $backup -Recurse -Force -ErrorAction SilentlyContinue
    $installed = $false
}

# Files that are already there before the install: only these get backed up and put back.
$existed = @{}
foreach ($f in $files) { if (Test-Path -LiteralPath (Join-Path $Target $f.Name)) { $existed[$f.Name] = $true } }
$copying = $false
$bad = @()
try {
    if (-not $installed) {
        $changed = 0
        foreach ($f in $files) {
            if (-not $existed[$f.Name]) { continue }
            $dst = Join-Path $Target $f.Name
            if ($f.Value.stock -and (Get-Sha $dst) -ne $f.Value.stock) { $changed++ }
            $bk = Join-Path $backup $f.Name
            New-Item -ItemType Directory -Force -Path (Split-Path $bk -Parent) | Out-Null
            Copy-Item -LiteralPath $dst -Destination $bk -Force
        }
        if ($changed) { Write-Host "  $changed files differed from stock $($man.base_version); they are backed up too." -ForegroundColor Yellow }
        Write-Host "Backup of the replaced files: $backup"
    }
    $copying = $true
    foreach ($f in $files) {
        $src = Join-Path (Join-Path $here 'payload') $f.Name
        $dst = Join-Path $Target $f.Name
        New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
        Copy-Item -LiteralPath $src -Destination $dst -Force
        Unblock-File -LiteralPath $dst
        if ((Get-Sha $dst) -ne $f.Value.rt) { $bad += $f.Name }
    }
    if ($bad.Count) { throw "these files did not copy right: $($bad -join ', ')" }
} catch {
    $why = $_.Exception.Message
    if ($installed) {
        Write-Host ''
        Write-Host "ERROR: $why" -ForegroundColor Red
        Write-Host 'Run "Uninstall Path Tracing.bat" to go back to stock, or close what holds the files and install again.' -ForegroundColor Red
        Exit-Script 1
    }
    # First install failed half way: put the backed-up files back and remove the added ones.
    # A failure while backing up has changed nothing, so then only the backup goes.
    if ($copying) {
        foreach ($f in $files) {
            $dst = Join-Path $Target $f.Name
            $bk = Join-Path $backup $f.Name
            try {
                if ($existed[$f.Name]) {
                    if ((Test-Path -LiteralPath $bk) -and (Get-Sha $bk) -ne (Get-Sha $dst)) { Copy-Item -LiteralPath $bk -Destination $dst -Force }
                }
                elseif (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
            } catch { Write-Host "  could not restore $($f.Name)" -ForegroundColor Yellow }
        }
    }
    Remove-Item -LiteralPath $backup -Recurse -Force -ErrorAction SilentlyContinue
    Stop-Install "$why (is the game or an antivirus holding a file?)"
}

# Path tracing pt2 builds nothing under FSR 4.1, the launcher's own pick when no upscaler is set:
# switch to DLSS on NVIDIA, else FSR 3.1. The old value goes back on uninstall.
$state = @{ rt_version = $man.rt_version; base_version = $man.base_version; installed = (Get-Date).ToString('s') }
$curEnv = Get-ExtraEnv
if ($installed) {
    $prev = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    $state.upscaler = $prev.upscaler
    if ($null -ne $prev.ini_existed) { $state.ini_existed = $prev.ini_existed }
    $state.env_replaced = [string]$prev.env_replaced
} elseif ($stale) {
    # The old install already holds what the user had before path tracing.
    $state.upscaler = $prev.upscaler
    if ($null -ne $prev.ini_existed) { $state.ini_existed = $prev.ini_existed }
    $state.env_replaced = [string]$prev.env_replaced
} else {
    $state.ini_existed = Test-Path -LiteralPath $ini
    # The user's own values for our variables, put back on uninstall.
    $state.env_replaced = (@(Split-Env ([string]$curEnv) | Where-Object { Test-RtToken $_ }) -join ' ')
}
$keepEnv = @(Split-Env ([string]$curEnv) | Where-Object { -not (Test-RtToken $_) })
Set-ExtraEnv ((@($keepEnv) + $rtEnv) -join ' ')
Write-Host 'Launcher: path tracing variables added to Advanced > Diagnostics > Extra variables.'
$up = Get-Upscaler
if (-not $up -or $up -in @('fsr411', 'fsr412')) {
    $nvidia = @(Get-CimInstance Win32_VideoController | Where-Object { $_.Name -match 'NVIDIA' }).Count -gt 0
    $new = if ($nvidia) { 'dlss' } else { 'fsr3' }
    if (-not $installed -and -not $stale) { $state.upscaler = if ($null -eq $up) { '' } else { $up } }
    Set-Upscaler $new
    $was = if ($up) { $up } else { 'automatic' }
    Write-Host "Upscaler: $was -> $new (path tracing does not start with FSR 4.1 in this build)." -ForegroundColor Yellow
}
$state | ConvertTo-Json | Set-Content -LiteralPath $marker -Encoding ASCII
Write-Host ''
Write-Host "Path tracing $($man.rt_version) installed ($($files.Count) files checked)." -ForegroundColor Green
Write-Host 'Start Bloodborne.exe as usual. In game, F9 turns path tracing off and on.'
Write-Host 'To remove it, run "Uninstall Path Tracing.bat".'
Exit-Script 0
