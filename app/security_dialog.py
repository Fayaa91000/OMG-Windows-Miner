"""User-facing Windows security results.

This dialog never overrides Windows security or starts mining.
"""

import os
import sys
import tkinter as tk
import webbrowser
from tkinter import messagebox

REVIEW_URL = "https://www.microsoft.com/en-us/wdsi/filesubmission"


def security_result(status):
    results = {
        "detected": (
            "Windows Defender reported a detection",
            "Installation is paused. Review the detection "
            "in Windows Security or request a Microsoft review."
        ),
        "missing": (
            "Mining engine unavailable",
            "The executable is missing or may have been "
            "removed by Windows security."
        ),
        "unknown": (
            "Security scan incomplete",
            "The Defender check failed, timed out, or "
            "could not be confirmed. You may retry."
        ),
        "unavailable": (
            "Windows Defender unavailable",
            "This security check cannot be completed here."
        ),
        "scan_completed": (
            "Defender scan completed",
            "No matching detection was found in the records "
            "checked. This is not a safety certificate "
            "or permission to execute."
        ),
    }
    return results.get(status, (
        "Security result unrecognized",
        "The check could not be confirmed."
    ))


def open_windows_security():
    if sys.platform != "win32":
        messagebox.showinfo(
            "Windows Security",
            "This option is available only on Windows."
        )
        return
    try:
        os.startfile("windowsdefender:")
    except OSError:
        messagebox.showwarning(
            "Windows Security",
            "Open Windows Security from the Windows Start menu."
        )


def show_security_result(parent, status, detail="", retry=None):
    title, explanation = security_result(status)

    window = tk.Toplevel(parent)
    window.title("OMG - Windows Security")
    window.geometry("480x350")
    window.resizable(False, False)
    window.transient(parent)
    window.grab_set()

    frame = tk.Frame(window, padx=20, pady=16)
    frame.pack(fill="both", expand=True)

    tk.Label(
        frame, text=title,
        font=("Arial", 13, "bold"),
        wraplength=425
    ).pack(pady=(0, 12))

    tk.Label(
        frame, text=explanation,
        wraplength=425, justify="left"
    ).pack(fill="x", pady=6)

    if detail:
        tk.Label(
            frame, text=str(detail),
            wraplength=425, justify="left",
            fg="#555555"
        ).pack(fill="x", pady=6)

    if status in ("detected", "missing"):
        tk.Button(
            frame, text="VIEW WINDOWS SECURITY",
            command=open_windows_security
        ).pack(fill="x", pady=3)

    if status == "detected":
        tk.Button(
            frame, text="REPORT INCORRECT DETECTION",
            command=lambda: webbrowser.open(REVIEW_URL)
        ).pack(fill="x", pady=3)

    if status in ("unknown", "unavailable", "missing") and retry:
        def retry_check():
            window.destroy()
            retry()

        tk.Button(
            frame, text="RETRY SECURITY CHECK",
            command=retry_check
        ).pack(fill="x", pady=3)

    tk.Button(
        frame, text="CLOSE",
        command=window.destroy
    ).pack(fill="x", pady=3)

    window.protocol("WM_DELETE_WINDOW", window.destroy)
    return window
