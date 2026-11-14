# Live A/B of rt.cfg knobs on the running game (render-look skill). For each entry of -Sets
# (extra rt.cfg lines, ';' between keys, '' = base): apply, wait, take -N shots, print the
# averaged look_check stats. -Stock adds the F9 stock view. rt.cfg is restored at the end.
#   look_ab.ps1 -Sets '','BB_RT_GI_FILL_SKY=2','' -N 2 -Stock
param([string[]]$Sets, [int]$N = 3, [switch]$Stock, [string]$Dir = "$env:TEMP\bb-look-ab")
New-Item -ItemType Directory -Force $Dir | Out-Null
$cfg = 'D:\modding\bbport-rt\out\rt-live\rt.cfg'
$py = 'C:/msys64/clang64/bin/python.exe'; $lc = "$PSScriptRoot\look_check.py"
$orig = [IO.File]::ReadAllText($cfg)
function Avg($tag) {
    $rows = @()
    for ($i = 0; $i -lt $N; $i++) {
        Start-Sleep -Milliseconds 900
        um win shot --exe bb-probe.exe "$Dir\ab_$i.png" --scale 0.5 | Out-Null
        $o = (& $py $lc stats "$Dir\ab_${i}_small.png") -join ' '
        $m = [regex]::Match($o, 'p5 (\d+) p20 (\d+) p50 (\d+) p90 (\d+).*?top10% luma\s+([\d.]+) a ([+-][\d.]+) b ([+-][\d.]+) \| mid luma\s+([\d.]+)')
        $rows += , @($m.Groups[1..8] | ForEach-Object { [double]$_.Value })
    }
    $a = 0..7 | ForEach-Object { $k = $_; [math]::Round(($rows | ForEach-Object { $_[$k] } | Measure-Object -Average).Average, 1) }
    $sd = [math]::Round([math]::Sqrt((($rows | ForEach-Object { [math]::Pow($_[4] - $a[4], 2) }) | Measure-Object -Average).Average), 1)
    '{0,-34} p5 {1} p20 {2} p50 {3} p90 {4} | top10 {5} (sd {9}) a {6} b {7} | mid {8}' -f $tag, $a[0], $a[1], $a[2], $a[3], $a[4], $a[5], $a[6], $a[7], $sd
}
try {
    foreach ($x in $Sets) {
        [IO.File]::WriteAllText($cfg, $orig + ($x -replace ';', "`n") + "`n"); Start-Sleep 3
        Avg ($(if ($x) { $x } else { 'base' }))
    }
} finally {
    [IO.File]::WriteAllText($cfg, $orig)
}
if ($Stock) {
    Start-Sleep 2
    um win drive --proc bb-probe "focus" "key 0x78" | Out-Null; Start-Sleep 2
    Avg 'STOCK'
    um win drive --proc bb-probe "focus" "key 0x78" | Out-Null
}
Remove-Item "$Dir\ab_*.png" -ErrorAction SilentlyContinue
Remove-Item $Dir -ErrorAction SilentlyContinue
