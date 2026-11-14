# Drive the game through the live pad file (src/runtime_pad.c) for the debug free camera.
# Needs bbport.ini debug_camera=1 at boot. Run from the PowerShell tool.
#   freecam.ps1 cycle               normal -> fly -> fixed -> normal (Cross held + L3)
#   freecam.ps1 hold 'r2' 1500      hold tokens for N ms, then release
#   freecam.ps1 hold 'ly=0 rx=200' 800
#   freecam.ps1 release
# Fly: ly/lx move, rx/ry look, r2 up, l2 down. Fixed: camera stays, sticks walk the player.
# Normal mode: r2/l2 attack and fire, so only send them in fly mode.
param(
    [Parameter(Mandatory)][ValidateSet('cycle', 'hold', 'release')][string]$Cmd,
    [string]$Tokens = '',
    [int]$Ms = 1000,
    [string]$Pad = 'D:\modding\bbport-rt\out\rt-live\pad'
)

function Put([string]$t, [int]$ms) {
    [IO.File]::WriteAllText($Pad, $t)
    Start-Sleep -Milliseconds $ms
}

switch ($Cmd) {
    'cycle' { Put 'cross' 300; Put 'cross l3' 250; Put 'cross' 150; Put '' 1200 }
    'hold' { Put $Tokens $Ms; Put '' 300 }
    'release' { Put '' 100 }
}
