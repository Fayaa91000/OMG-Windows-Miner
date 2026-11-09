"""User-approved XMRig installation interface."""

import queue
import threading
import tkinter as tk
from tkinter import messagebox

from engine_installer import install_engine
from security_dialog import show_security_result


def request_engine_install(parent, consent):
    parent = parent.winfo_toplevel()

    if not consent:
        messagebox.showwarning(
            "XMRig Agreement",
            "Please accept the XMRig installation agreement.",
            parent=parent
        )
        return

    progress = tk.Toplevel(parent)
    progress.title("OMG - Installing XMRig")
    progress.geometry("420x150")

    tk.Label(
        progress,
        text="Downloading and verifying official XMRig...",
        wraplength=370
    ).pack(padx=15, pady=20)

    progress.protocol("WM_DELETE_WINDOW", lambda: None)

    results = queue.Queue(maxsize=1)

    def worker():
        try:
            result = install_engine(consent=True)
        except Exception:
            result = ("unknown", "Installation failed.")
        results.put(result)

    def poll():
        try:
            status, detail = results.get_nowait()
        except queue.Empty:
            if progress.winfo_exists():
                progress.after(200, poll)
            return

        progress.destroy()

        if not parent.winfo_exists():
            return

        if status in (
            "installed_pending_runtime_checks",
            "already_installed"
        ):
            messagebox.showinfo(
                "XMRig Installation",
                detail + "\nMining remains disabled.",
                parent=parent
            )
        else:
            show_security_result(parent, status, detail)

    threading.Thread(target=worker, daemon=True).start()
    progress.after(200, poll)
