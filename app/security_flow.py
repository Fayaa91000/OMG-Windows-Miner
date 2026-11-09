"""Display Windows Defender scan results in OMG."""

import queue
import threading
import tkinter as tk

from windows_security import scan_engine
from security_dialog import show_security_result


def request_security_scan(parent, engine_path):
    parent = parent.winfo_toplevel()
    results = queue.Queue(maxsize=1)

    progress = tk.Toplevel(parent)
    progress.title("OMG - Defender Scan")
    progress.geometry("390x130")
    progress.resizable(False, False)

    tk.Label(
        progress,
        text="Checking XMRig with Microsoft Defender...",
        wraplength=340
    ).pack(padx=15, pady=(18, 8))

    tk.Label(
        progress,
        text="Mining remains disabled during this check.",
        wraplength=340
    ).pack(padx=15, pady=4)

    progress.protocol("WM_DELETE_WINDOW", lambda: None)

    def worker():
        try:
            outcome = scan_engine(engine_path)
        except Exception:
            outcome = (
                "unknown",
                "Security check failed unexpectedly."
            )
        results.put(outcome)

    def poll():
        try:
            status, detail = results.get_nowait()
        except queue.Empty:
            if progress.winfo_exists():
                progress.after(150, poll)
            return

        progress.destroy()

        if parent.winfo_exists():
            show_security_result(
                parent,
                status,
                detail,
                retry=lambda: request_security_scan(
                    parent, engine_path
                )
            )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()

    progress.after(150, poll)
