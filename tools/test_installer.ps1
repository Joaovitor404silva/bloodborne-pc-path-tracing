# Install/uninstall test of a built installer folder on fresh copies of a stock Bloodborne PC folder.
# APPDATA is redirected, so the real launcher settings are never touched.
# usage: powershell -File tools\test_installer.ps1 -Package dist\Bloodborne-PC-Path-Tracing-X -Stock <stock bbport-windows> [-Work <scratch dir>]
param([Parameter(Mandatory)][string]$Package, [Parameter(Mandatory)][string]$Stock, [string]$Work = (Join-Path $env:TEMP 'rt-installer-test'))
$ErrorActionPreference = 'Stop'
$Package = (Resolve-Path -LiteralPath $Package).Path
$Stock = (Resolve-Path -LiteralPath $Stock).Path
$man = Get-Content -LiteralPath (Join-Path $Package 'manifest.json') -Raw | ConvertFrom-Json
$ships = @($man.files.PSObject.Properties | ForEach-Object { $_.Name })
$utf8 = New-Object Text.UTF8Encoding $false
$fail = 0
function Check($ok, $what) { if ($ok) { "  PASS $what" } else { "  FAIL $what"; $script:fail++ } }
function TreeHash($dir) {
    Get-ChildItem -LiteralPath $dir -Recurse -File | ForEach-Object {
        $_.FullName.Substring($dir.Length) + ' ' + (Get-FileHash -LiteralPath $_.FullName).Hash } | Sort-Object
}
function Run([string[]]$extra) {
    $out = powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Package 'install.ps1') -Target $script:t @extra 2>&1 | Out-String
    return @{ code = $LASTEXITCODE; out = $out }
}
$stockTree = TreeHash $Stock
$rtStart = 'BB_RT=1 BB_RT_DIRECT=1'
$t = Join-Path $Work 'game'
$app = Join-Path $Work 'appdata'
$origAppdata = $env:APPDATA
function Fresh {
    if (Test-Path $Work) { Remove-Item $Work -Recurse -Force }
    New-Item -ItemType Directory "$app\bbport-launcher" | Out-Null
    Copy-Item $Stock $t -Recurse
    $env:APPDATA = $app
}
$cfg = "$app\bbport-launcher\settings.json"
try {
    $cases = @(
        @{ name = 'settings with user tokens'; json = "{`n  `"fullscreen`": true,`n  `"extra_env`": `"FOO=1 BB_RT_GI=0 BAR=x`"`n}`n"; after = 'FOO=1 BAR=x BB_RT_GI=0' },
        @{ name = 'no settings.json'; json = $null; after = '' },
        @{ name = 'settings without extra_env'; json = "{`n  `"fullscreen`": true,`n  `"name`": `"A$([char]0xe7)$([char]0xe3)o`"`n}`n"; after = '' }
    )
    foreach ($c in $cases) {
        "== $($c.name)"
        Fresh
        if ($null -ne $c.json) { [IO.File]::WriteAllText($cfg, $c.json, $utf8) }
        $r = Run @()
        Check ($r.code -eq 0) 'install exit 0'
        $j = [IO.File]::ReadAllText($cfg) | ConvertFrom-Json
        Check ($j.extra_env -like "*$rtStart*") 'extra_env has the RT line'
        Check (-not (($j.extra_env -split ' ') -contains 'BB_RT_GI=0')) "user's BB_RT_GI=0 replaced"
        if ($c.json -like '*name*') { Check ($j.name -eq "A$([char]0xe7)$([char]0xe3)o" -and $j.fullscreen) 'other keys and unicode kept' }
        foreach ($f in $ships) { Check ((Get-FileHash "$t\$f").Hash -eq (Get-FileHash "$Package\payload\$f").Hash) "$f is ours" }
        Check (((Get-Content "$t\bbport.ini") -join ' ') -match 'upscaler=(dlss|fsr3)') 'upscaler set'
        $null = Run @()
        $j2 = [IO.File]::ReadAllText($cfg) | ConvertFrom-Json
        Check (@($j2.extra_env -split ' ' | Where-Object { $_ -eq 'BB_RT=1' }).Count -eq 1) 'reinstall: no duplicate tokens'
        $r = Run @('-Uninstall')
        Check ($r.code -eq 0) 'uninstall exit 0'
        $j3 = [IO.File]::ReadAllText($cfg) | ConvertFrom-Json
        Check ($j3.extra_env -eq $c.after) "extra_env after uninstall = [$($j3.extra_env)] (want [$($c.after)])"
        $d = Compare-Object $stockTree (TreeHash $t)
        Check (-not $d) "folder byte-identical to stock ($(@($d).Count) diffs)"
        if ($fail) { $r.out }
    }

    "== other path tracing version installed on this same Bloodborne PC version"
    Fresh
    "{`"rt_version`":`"pt0`",`"base_version`":`"$($man.base_version)`"}" | Set-Content "$t\rt-installed.json" -Encoding ASCII
    $before = TreeHash $t
    $r = Run @()
    Check ($r.code -ne 0) "install refused (exit $($r.code))"
    Check ($r.out -match 'pt0 is installed here') 'says to uninstall pt0 first'
    Check (-not (Compare-Object $before (TreeHash $t))) 'folder untouched'

    "== Bloodborne PC updated after an older path tracing install"
    Fresh
    # What an update leaves behind: the old marker and backup, our added DLL, our launcher variables.
    New-Item -ItemType Directory "$t\rt-backup\bin" -Force | Out-Null
    [IO.File]::WriteAllText("$t\rt-backup\bin\bb-probe.exe", 'old version exe')
    '{"rt_version":"pt0","base_version":"0.0.1","upscaler":"","ini_existed":false,"env_replaced":"BB_RT_GI=0"}' | Set-Content "$t\rt-installed.json" -Encoding ASCII
    foreach ($f in $ships) { if (-not (Test-Path "$t\$f")) { Copy-Item "$Package\payload\$f" "$t\$f" } }
    'upscaler=dlss' | Set-Content "$t\bbport.ini" -Encoding ASCII
    [IO.File]::WriteAllText($cfg, "{`n  `"extra_env`": `"FOO=1 BB_RT=1 BB_RT_GI=1`"`n}`n", $utf8)
    $r = Run @()
    Check ($r.code -eq 0) 'install exit 0'
    Check ($r.out -match 'installing fresh') 'says it installs fresh'
    $m = Get-Content "$t\rt-installed.json" -Raw | ConvertFrom-Json
    Check ($m.base_version -eq $man.base_version -and $m.rt_version -eq $man.rt_version) 'marker is the new version'
    Check ($m.env_replaced -eq 'BB_RT_GI=0' -and $m.upscaler -eq '' -and $m.ini_existed -eq $false) 'kept what the user had before the first install'
    Check ((Get-FileHash "$t\rt-backup\bin\bb-probe.exe").Hash -eq (Get-FileHash "$Stock\bin\bb-probe.exe").Hash) 'backup is the new stock exe'
    foreach ($f in $ships) { Check ((Get-FileHash "$t\$f").Hash -eq (Get-FileHash "$Package\payload\$f").Hash) "$f is ours" }
    $r = Run @('-Uninstall')
    Check ($r.code -eq 0) 'uninstall exit 0'
    $j = [IO.File]::ReadAllText($cfg) | ConvertFrom-Json
    Check ($j.extra_env -eq 'FOO=1 BB_RT_GI=0') "extra_env after uninstall = [$($j.extra_env)]"
    $d = Compare-Object $stockTree (TreeHash $t)
    Check (-not $d) "folder byte-identical to stock ($(@($d).Count) diffs)"
    if ($d) { $d | Select-Object -First 5 | Out-String }

    "== uninstall after an update, with the old install still in place"
    Fresh
    $old = Join-Path $Work 'oldpkg'
    New-Item -ItemType Directory "$t\rt-backup\bin" -Force | Out-Null
    Copy-Item "$Stock\bin\bb-probe.exe" "$t\rt-backup\bin\bb-probe.exe"
    [IO.File]::WriteAllText("$t\bin\bb-probe.exe", 'old path tracing exe the update did not replace')
    '{"rt_version":"pt0","base_version":"0.0.1","upscaler":"","ini_existed":false,"env_replaced":""}' | Set-Content "$t\rt-installed.json" -Encoding ASCII
    $r = Run @('-Uninstall')
    Check ($r.code -eq 0) 'uninstall exit 0'
    Check ($r.out -match 'bb-probe.exe is not Bloodborne PC') 'warns the exe is not the port own'
    Check (-not (Test-Path "$t\rt-installed.json") -and -not (Test-Path "$t\rt-backup")) 'marker and old backup gone'
} finally {
    $env:APPDATA = $origAppdata
    if (Test-Path $Work) { Remove-Item $Work -Recurse -Force }
}
"TOTAL FAILS: $fail"
if ($fail) { exit 1 }
