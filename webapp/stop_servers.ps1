$ports = @(3000, 8000, 5173)
foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        $pids_ = $conns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($p in $pids_) {
            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped process $p on port $port"
        }
    } else {
        Write-Host "No process on port $port"
    }
}
