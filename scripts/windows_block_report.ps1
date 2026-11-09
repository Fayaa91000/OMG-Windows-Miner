# OMG Windows execution diagnostics.
# Read-only: no antivirus changes or exceptions.

param(
    [string]$FilePath = ""
)

Write-Output "=== OMG WINDOWS BLOCK DIAGNOSTICS ==="

Write-Output "`n=== CODE INTEGRITY EVENTS (LAST 24 HOURS) ==="
try {
    $events = Get-WinEvent -FilterHashtable @{
        LogName = "Microsoft-Windows-CodeIntegrity/Operational"
        Id = 3076, 3077, 3089
        StartTime = (Get-Date).AddHours(-24)
    } -ErrorAction Stop

    foreach ($event in ($events | Select-Object -First 20)) {
        Write-Output "Time: $($event.TimeCreated)"
        Write-Output "Event ID: $($event.Id)"
        Write-Output "Details: $($event.Message)"
        Write-Output "---"
    }
}
catch {
    Write-Output "No matching events or log unavailable."
}

Write-Output "`n=== DEFENDER DETECTIONS ==="
try {
    Get-MpThreatDetection -ErrorAction Stop |
        Select-Object -First 10 ThreatID, InitialDetectionTime, Resources |
        Format-List
}
catch {
    Write-Output "Defender detection information unavailable."
}

if ($FilePath -and (Test-Path -LiteralPath $FilePath)) {
    Write-Output "`n=== EXECUTABLE SIGNATURE ==="
    Get-AuthenticodeSignature -LiteralPath $FilePath |
        Select-Object Status, StatusMessage, SignerCertificate |
        Format-List
}

Write-Output "`nDiagnostics finished. No security settings changed."
