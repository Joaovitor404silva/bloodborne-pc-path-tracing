param(
    [string]$OutDir = 'D:\modding\bbport-rt\out\rt-live\shaders',
    [string]$SourceDir = (Join-Path $PSScriptRoot '..\gpu\shadps4\video_core\host_shaders'),
    [string]$Glslang = 'C:\msys64\clang64\bin\glslang.exe',
    [switch]$Once
)
$SourceDir = (Resolve-Path $SourceDir).Path
New-Item -ItemType Directory -Force $OutDir | Out-Null
$variants = @(
    @('rt_gather.comp', 'rt_gather_comp', @()),
    @('rt_omm_bake.comp', 'rt_omm_bake_comp', @()),
    @('rt_debug.comp', 'rt_debug_comp', @()),
    @('rt_probe.comp', 'rt_probe_comp', @()),
    @('rt_gi.comp', 'rt_gi_comp', @()),
    @('rt_gi_apply.comp', 'rt_gi_apply_comp', @()),
    @('rt_gi.comp', 'rt_reflect_comp', @('RT_REFLECT=1')),
    @('rt_gi.comp', 'rt_restir_gi_init_comp', @('RT_RESTIR_GI=1', 'RT_RESTIR_INIT=1')),
    @('rt_gi.comp', 'rt_restir_gi_resolve_comp', @('RT_RESTIR_GI=1', 'RT_RESTIR_RESOLVE=1')),
    @('rt_gi.comp', 'rt_light_vis_comp', @('RT_LIGHT_VIS=1')),
    @('rt_restir_gi.comp', 'rt_restir_gi_temporal_comp', @()),
    @('rt_restir_gi.comp', 'rt_restir_gi_spatial_comp', @('RT_RESTIR_SPATIAL=1')),
    @('rt_shadow.comp', 'rt_shadow_comp', @()),
    @('rt_fog.comp', 'rt_fog_comp', @()),
    @('rt_fog.comp', 'rt_fog_apply_comp', @('RT_FOG_APPLY=1')),
    @('rt_fog.comp', 'rt_fog_opaque_comp', @('RT_FOG_OPAQUE=1')),
    @('rt_sky.comp', 'rt_sky_comp', @()),
    @('rt_direct.comp', 'rt_direct_comp', @()),
    @('rt_ao.comp', 'rt_ao_comp', @()),
    @('rt_direct.comp', 'rt_restir_temporal_comp', @('RT_RESTIR_PASS=1')),
    @('rt_direct.comp', 'rt_restir_spatial_comp', @('RT_RESTIR_PASS=2'))
)
function Compile-Source([string]$file) {
    $src = Join-Path $SourceDir $file
    foreach ($v in $variants) {
        if ($v[0] -ne $file) { continue }
        $name = $v[1]
        $tmp = Join-Path $OutDir "$name.tmp"
        $out = Join-Path $OutDir "$name.spv"
        $defs = @($v[2] | ForEach-Object { "-D$_" })
        $log = & $Glslang --target-env vulkan1.3 @defs -o $tmp $src 2>&1
        if ($LASTEXITCODE -eq 0 -and (Test-Path $tmp)) {
            Move-Item -Force $tmp $out
            Write-Host ("{0:HH:mm:ss} {1} -> {2}" -f (Get-Date), $file, "$name.spv")
        } else {
            Remove-Item $tmp -ErrorAction SilentlyContinue
            Write-Host ("{0:HH:mm:ss} {1} ({2}) FAILED" -f (Get-Date), $file, $name) -ForegroundColor Red
            $log | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
        }
    }
}
$stamps = @{}
$sources = $variants | ForEach-Object { $_[0] } | Sort-Object -Unique
foreach ($s in $sources) { $stamps[$s] = (Get-Item (Join-Path $SourceDir $s)).LastWriteTimeUtc }
if ($Once) { foreach ($s in $sources) { Compile-Source $s }; exit 0 }
Write-Host "watching $SourceDir -> $OutDir (Ctrl+C stops; shaders reload in the game within ~30 frames)"
while ($true) {
    Start-Sleep -Milliseconds 500
    foreach ($s in $sources) {
        $t = (Get-Item (Join-Path $SourceDir $s)).LastWriteTimeUtc
        if ($t -ne $stamps[$s]) {
            Start-Sleep -Milliseconds 200
            $stamps[$s] = (Get-Item (Join-Path $SourceDir $s)).LastWriteTimeUtc
            Compile-Source $s
        }
    }
}
