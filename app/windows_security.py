"""Request a Microsoft Defender scan and inspect recorded detections.

Not a security certificate or Smart App Control approval.
"""

import os
import subprocess
import sys
from pathlib import Path


def scan_engine(path):
    if sys.platform != "win32":
        return "unavailable", "Microsoft Defender requires Windows."

    path = Path(path).resolve()
    if not path.is_file():
        return "missing", "XMRig executable not found."

    script = r"""
$ErrorActionPreference = 'Stop'
try {
    $status = Get-MpComputerStatus -ErrorAction Stop
    if (-not $status.AMServiceEnabled -or
        -not $status.AntivirusEnabled -or
        -not $status.RealTimeProtectionEnabled) {
        throw 'Microsoft Defender protection is unavailable'
    }

    $target = $env:OMG_ENGINE_SCAN_PATH

    # Inspect existing detections before scanning too.
    $before = @(Get-MpThreatDetection -ErrorAction Stop)
    $matches = @(
        $before | Where-Object {
            @($_.Resources) | Where-Object {
                $_ -and $_.ToLowerInvariant().Contains(
                    $target.ToLowerInvariant()
                )
            }
        }
    )
    if ($matches.Count -gt 0) {
        Write-Output 'OMG_SCAN_RESULT:DETECTION'
        exit 0
    }

    Start-MpScan -ScanType CustomScan `
        -ScanPath $target -ErrorAction Stop

    $after = @(Get-MpThreatDetection -ErrorAction Stop)
    $matches = @(
        $after | Where-Object {
            @($_.Resources) | Where-Object {
                $_ -and $_.ToLowerInvariant().Contains(
                    $target.ToLowerInvariant()
                )
            }
        }
    )

    if ($matches.Count -gt 0) {
        Write-Output 'OMG_SCAN_RESULT:DETECTION'
    }
    else {
        Write-Output 'OMG_SCAN_RESULT:NO_MATCHING_DETECTION'
    }
}
catch {
    Write-Output 'OMG_SCAN_RESULT:UNKNOWN'
    exit 1
}
"""

    env = os.environ.copy()
    env["OMG_ENGINE_SCAN_PATH"] = str(path)

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
            creationflags=getattr(
                subprocess, "CREATE_NO_WINDOW", 0
            ),
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown", "Defender scan failed or timed out."

    if "OMG_SCAN_RESULT:DETECTION" in result.stdout:
        return (
            "detected",
            "Defender has recorded a detection for this file. "
            "Installation must stop."
        )

    if not path.is_file():
        return (
            "missing",
            "Engine missing after scan. Check Windows Security."
        )

    if result.returncode != 0:
        return "unknown", "Defender security check failed."

    if "OMG_SCAN_RESULT:NO_MATCHING_DETECTION" in result.stdout:
        return (
            "scan_completed",
            "Defender scan completed with no matching detection "
            "in the records checked. This is not proof of safety "
            "or permission to execute."
        )

    return "unknown", "Defender returned an unexpected result."
