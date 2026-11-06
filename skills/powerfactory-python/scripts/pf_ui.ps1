# Entrada de escritorio autorizada para PF; observar captura antes de cada accion.
param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [ValidateSet('none','click','dclick','rclick','key')][string]$Action = 'none',
    [int]$X = 0,
    [int]$Y = 0,
    [string]$Key = '',
    [ValidateRange(0,5000)][int]$SleepMs = 400
)
$ErrorActionPreference = 'Stop'
$targetProcess = Get-Process -Id $TargetPid
if ($targetProcess.ProcessName -ne 'PowerFactory') {
    throw 'El PID indicado no pertenece a PowerFactory. Volver a identificar la instancia.'
}
if ($Action -eq 'none') {
    $targetProcess | Select-Object Id, ProcessName, MainWindowTitle
    return
}
if ($Action -eq 'key' -and [string]::IsNullOrWhiteSpace($Key)) { throw 'Falta -Key.' }
if ($targetProcess.MainWindowHandle -eq [IntPtr]::Zero) { throw 'PF no tiene ventana principal accesible.' }
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class PfUiInput {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int cmd);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
    [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(Pt point);
    public struct Pt { public int x; public int y; public Pt(int px, int py) { x = px; y = py; } }
    public static uint Owner(IntPtr hWnd) { uint id; GetWindowThreadProcessId(hWnd, out id); return id; }
    public static uint PointOwner(int x, int y) { return Owner(WindowFromPoint(new Pt(x,y))); }
}
'@
[void][PfUiInput]::SetProcessDPIAware()
if ([PfUiInput]::IsIconic($targetProcess.MainWindowHandle)) {
    [void][PfUiInput]::ShowWindow($targetProcess.MainWindowHandle, 9)
}
if ([PfUiInput]::Owner([PfUiInput]::GetForegroundWindow()) -ne $TargetPid) {
    [void][PfUiInput]::SetForegroundWindow($targetProcess.MainWindowHandle)
    Start-Sleep -Milliseconds 200
}
if ([PfUiInput]::Owner([PfUiInput]::GetForegroundWindow()) -ne $TargetPid) {
    throw 'PF no obtuvo el primer plano. No se envio entrada; capturar de nuevo.'
}
if ($Action -eq 'key') {
    [System.Windows.Forms.SendKeys]::SendWait($Key)
} else {
    if ([PfUiInput]::PointOwner($X, $Y) -ne $TargetPid) {
        throw 'El punto no pertenece a una ventana de PF. No se envio el clic; capturar de nuevo.'
    }
    if (-not [PfUiInput]::SetCursorPos($X, $Y)) { throw 'No se pudo colocar el cursor.' }
    $downFlag = [uint32]2
    $upFlag = [uint32]4
    if ($Action -eq 'rclick') { $downFlag = 8; $upFlag = 16 }
    $clickCount = 1
    if ($Action -eq 'dclick') { $clickCount = 2 }
    for ($clickIndex = 0; $clickIndex -lt $clickCount; $clickIndex++) {
        [PfUiInput]::mouse_event($downFlag, 0, 0, 0, [UIntPtr]::Zero)
        [PfUiInput]::mouse_event($upFlag, 0, 0, 0, [UIntPtr]::Zero)
        if ($clickCount -eq 2 -and $clickIndex -eq 0) { Start-Sleep -Milliseconds 100 }
    }
}
Start-Sleep -Milliseconds $SleepMs
