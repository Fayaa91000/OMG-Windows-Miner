import tkinter as tk
from tkinter import ttk, messagebox
from miner_controller import MinerController
from engine_verifier import verify_engine
import threading
import time
import webbrowser

BG = "#0A131F"
FG = "#ffffff"
ACCENT = "#30DAA9"

root = tk.Tk()
root.title("OMG Windows Miner")
root.geometry("520x620")
root.minsize(460, 550)
root.configure(bg=BG)

# Scrollable content keeps Start/Stop accessible on small screens.
scrollbar = tk.Scrollbar(root, orient="vertical")
scrollbar.pack(side="right", fill="y")

canvas = tk.Canvas(
    root, bg=BG, highlightthickness=0,
    yscrollcommand=scrollbar.set
)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.config(command=canvas.yview)

container = tk.Frame(canvas, bg=BG, padx=25, pady=20)
content_window = canvas.create_window(
    (0, 0), window=container, anchor="nw"
)

def update_scroll_region(event=None):
    canvas.configure(scrollregion=canvas.bbox("all"))

def resize_content(event):
    canvas.itemconfigure(content_window, width=event.width)

container.bind("<Configure>", update_scroll_region)
canvas.bind("<Configure>", resize_content)



# Official OMG logo, shared with the Android application.
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    logo_path = Path(sys._MEIPASS) / "app/assets/omg_logo_96.png"
else:
    logo_path = Path(__file__).resolve().parent / "assets/omg_logo_96.png"

if logo_path.is_file():
    omg_logo_image = tk.PhotoImage(file=str(logo_path))
    tk.Label(
        container,
        image=omg_logo_image,
        bg=BG
    ).pack(pady=(4, 6))

tk.Label(
    container, text="OMG SADAQAH FOUNDATION",
    font=("Arial", 25, "bold"),
    bg=BG, fg=FG
).pack(pady=10)

tk.Label(
    container,
    text="MONERO MINER  •  GAZA SADAQAH",
    bg=BG, fg="#b8c9d9"
).pack(pady=5)


wallet_card = tk.Frame(
    container, bg="#173747",
    padx=12, pady=12,
    highlightbackground="#246F72",
    highlightthickness=1
)
wallet_card.pack(fill="x", pady=(14, 8))

tk.Label(
    wallet_card,
    text="YOUR MONERO WALLET",
    bg="#173747", fg=FG,
    font=("Arial", 11, "bold")
).pack(anchor="w", pady=(0, 8))

wallet_row = tk.Frame(wallet_card, bg="#173747")
wallet_row.pack(fill="x")

wallet = tk.StringVar()

wallet_entry = tk.Entry(
    wallet_row,
    textvariable=wallet,
    font=("Arial", 11),
    bg="#1B3040",
    fg=FG,
    insertbackground=FG,
    relief="flat"
)
wallet_entry.pack(side="left", fill="x", expand=True, ipady=8)

def paste_wallet():
    try:
        value = root.clipboard_get().strip()
    except tk.TclError:
        messagebox.showwarning(
            "OMG Wallet", "Clipboard is empty."
        )
        return
    wallet.set(value)

tk.Button(
    wallet_row,
    text="PASTE",
    command=paste_wallet,
    bg="#224C58",
    fg=FG,
    font=("Arial", 10, "bold"),
    relief="flat",
    padx=12,
    pady=8
).pack(side="left", padx=(8, 0))

def show_wallet_guide():
    instructions = (
        "HOW TO CREATE YOUR MONERO WALLET\n\n"
        "1. Open the official Monero wallet website.\n"
        "2. Choose a wallet compatible with your device.\n"
        "3. Create a new wallet.\n"
        "4. Back up your recovery seed privately, offline.\n"
        "5. Find your public Monero receiving address.\n"
        "6. Copy it into OMG Miner.\n\n"
        "Never share your recovery seed or private keys.\n"
        "No central Monero account is required.\n\n"
        "Open the official Monero wallet download page?"
    )
    if messagebox.askyesno("Monero Wallet Guide", instructions):
        webbrowser.open("https://www.getmonero.org/downloads/")

tk.Button(
    container,
    text="CREATE MONERO WALLET / GUIDE",
    command=show_wallet_guide,
    bg="#24364c",
    fg=FG,
    font=("Arial", 10, "bold"),
    pady=7
).pack(fill="x", pady=(3, 8))

tk.Label(
    container,
    text="Use only your PUBLIC Monero receiving address.",
    bg=BG,
    fg="#b8c9d9",
    wraplength=430
).pack(pady=(0, 5))

tk.Label(
    container, text="Mining Mode",
    bg=BG, fg=FG
).pack(pady=(15, 5))

mode = tk.StringVar(value="AUTO")

ttk.Combobox(
    container, textvariable=mode,
    values=["AUTO", "LIGHT", "FAST"],
    state="readonly"
).pack(fill="x")

tk.Label(
    container, text="CPU Threads",
    bg=BG, fg=FG
).pack(pady=(15, 5))

# Conservative default based on available logical processors.
import os
available_cpus = os.cpu_count() or 2
recommended_threads = max(1, min(6, available_cpus // 2))
threads = tk.IntVar(value=recommended_threads)

tk.Scale(
    container, from_=1, to=6,
    orient="horizontal",
    variable=threads,
    bg=BG, fg=FG,
    highlightthickness=0
).pack(fill="x")



# Android-style live mining dashboard.
dashboard = tk.Frame(
    container, bg="#192D3F",
    padx=12, pady=12,
    highlightbackground="#246F72",
    highlightthickness=1
)
dashboard.pack(fill="x", pady=(12, 10))

tk.Label(
    dashboard,
    text="LIVE MINING DASHBOARD",
    bg="#192D3F",
    fg="#35DCAA",
    font=("Arial", 13, "bold")
).pack(pady=(0, 8))

status = tk.Label(
    dashboard,
    text="Status: Ready to start",
    font=("Arial", 11),
    bg="#192D3F",
    fg=FG,
    justify="center",
    wraplength=430
)
status.pack(pady=(0, 10))

stats_row = tk.Frame(dashboard, bg="#192D3F")
stats_row.pack(fill="x")

def create_stat_tile(title, initial):
    tile = tk.Frame(
        stats_row, bg="#254455",
        padx=5, pady=10,
        highlightbackground="#346273",
        highlightthickness=1
    )
    tile.pack(side="left", fill="both",
              expand=True, padx=3)

    tk.Label(
        tile, text=title,
        bg="#254455",
        fg="#AFCDD7",
        font=("Arial", 9, "bold")
    ).pack()

    value = tk.Label(
        tile, text=initial,
        bg="#254455",
        fg=FG,
        font=("Arial", 13, "bold")
    )
    value.pack(pady=(5, 0))
    return value

speed_tile = create_stat_tile("HASHRATE", "—")
shares_tile = create_stat_tile("SHARES", "0")
timer = create_stat_tile("REMAINING", "04:00:00")


# Mining-time allocation: 75% user, 25% Gaza.
allocation_bar = tk.Frame(
    container, bg="#203743", height=14
)
allocation_bar.pack(fill="x", pady=(8, 4))
allocation_bar.pack_propagate(False)

user_allocation = tk.Frame(
    allocation_bar, bg="#17D397"
)
user_allocation.pack(
    side="left", fill="both", expand=True
)

gaza_allocation = tk.Frame(
    allocation_bar, bg="#F6B541"
)
gaza_allocation.pack(
    side="left", fill="both"
)

def resize_allocation(event):
    width = max(4, event.width)
    user_allocation.pack_configure(
        expand=False
    )
    user_allocation.configure(width=width * 3 // 4)
    gaza_allocation.configure(
        width=width - width * 3 // 4
    )

allocation_bar.bind("<Configure>", resize_allocation)

tk.Label(
    container,
    text="YOUR WALLET 3 HOURS  •  GAZA SADAQAH 1 HOUR",
    bg=BG,
    fg="#3DE2AE",
    font=("Arial", 10, "bold")
).pack(pady=(0, 10))

# Independent XMRig disclosure and installation consent.
tk.Label(
    container,
    text="XMRig 6.26.0 - Independent Mining Engine",
    bg=BG, fg="#3DE2AE",
    font=("Arial", 11, "bold")
).pack(fill="x", pady=(10, 4))

tk.Label(
    container,
    text=(
        "Developer: XMRig Project\n"
        "License: GNU GPLv3\n"
        "Git verification: See official GitHub release\n"
        "Windows publisher signature: Unsigned"
    ),
    bg=BG, fg=FG,
    justify="left",
    wraplength=440
).pack(fill="x", pady=4)

tk.Button(
    container,
    text="VIEW XMRIG SOURCE AND RELEASE",
    command=lambda: webbrowser.open(
        "https://github.com/xmrig/xmrig/releases/tag/v6.26.0"
    ),
    bg="#224C58", fg=FG
).pack(fill="x", pady=3)

tk.Button(
    container,
    text="READ GNU GPLv3 LICENSE",
    command=lambda: webbrowser.open(
        "https://www.gnu.org/licenses/gpl-3.0.html"
    ),
    bg="#224C58", fg=FG
).pack(fill="x", pady=3)

xmrig_install_consent = tk.BooleanVar(value=False)

tk.Checkbutton(
    container,
    text=(
        "I understand XMRig is independent open-source "
        "mining software, and I agree to install it."
    ),
    variable=xmrig_install_consent,
    bg=BG, fg=FG,
    selectcolor=BG,
    activebackground=BG,
    activeforeground=FG,
    justify="left",
    wraplength=440
).pack(fill="x", pady=(8, 12))


# User-requested Defender scan.
from security_flow import request_security_scan

tk.Button(
    container,
    text="SCAN XMRIG WITH WINDOWS DEFENDER",
    command=lambda: request_security_scan(
        container, controller.binary_path()
    ),
    bg="#224C58",
    fg=FG
).pack(fill="x", pady=(3, 12))

sadaqah_consent = tk.BooleanVar(value=False)

tk.Checkbutton(
    container,
    text=(
        "I agree: 3 hours for my wallet and "
        "1 hour for Gaza Sadaqah.\n"
        "75% / 25% mining time. "
        "Rewards are not guaranteed."
    ),
    variable=sadaqah_consent,
    bg=BG,
    fg=FG,
    selectcolor=BG,
    activebackground=BG,
    activeforeground=FG,
    justify="left",
    wraplength=440
).pack(fill="x", pady=5)

controller = MinerController()

# User-approved independent XMRig installation.
from installer_flow import request_engine_install

tk.Button(
    container,
    text="INSTALL OFFICIAL XMRIG",
    command=lambda: request_engine_install(
        container, xmrig_install_consent.get()
    ),
    bg="#17644D",
    fg=FG
).pack(fill="x", pady=(4, 10))



# Fail closed until engine verification is implemented.
engine_security_approved = False

def can_start_mining():
    return (
        engine_security_approved
        and xmrig_install_consent.get()
        and sadaqah_consent.get()
        and not controller.is_running()
    )

accepted = 0
speed = "—"
last_phase = "idle"

# Explicit security verification of the installed engine.
def request_engine_approval():
    global engine_security_approved

    import os
    import queue
    from pathlib import Path
    from engine_installer import file_hash, EXE_HASH
    from windows_security import scan_engine
    from security_dialog import show_security_result

    engine_security_approved = False
    start_button.config(state="disabled")

    if not xmrig_install_consent.get():
        messagebox.showwarning(
            "XMRig Agreement",
            "Accept the XMRig agreement first."
        )
        return

    local = os.environ.get("LOCALAPPDATA")
    if not local:
        messagebox.showwarning(
            "Windows Required",
            "Security verification requires Windows."
        )
        return

    binary = (
        Path(local) / "OMG Windows Miner"
        / "engine" / "xmrig.exe"
    )

    if binary.is_symlink() or not binary.is_file():
        show_security_result(
            root, "missing",
            "Install the official XMRig engine first."
        )
        return

    results = queue.Queue(maxsize=1)

    verify_button.config(state="disabled")
    status.config(text="Verifying XMRig and Windows Defender...")

    def worker():
        try:
            if file_hash(binary) != EXE_HASH:
                result = (
                    "unknown",
                    "XMRig checksum mismatch. Mining blocked."
                )
            else:
                result = scan_engine(binary)

                if result[0] == "scan_completed":
                    if (
                        binary.is_symlink()
                        or not binary.is_file()
                        or file_hash(binary) != EXE_HASH
                    ):
                        result = (
                            "unknown",
                            "Engine changed or disappeared after scan."
                        )
        except Exception:
            result = (
                "unknown",
                "Unable to complete engine security verification."
            )

        results.put(result)

    def poll():
        global engine_security_approved

        try:
            result, detail = results.get_nowait()
        except queue.Empty:
            root.after(200, poll)
            return

        verify_button.config(state="normal")

        engine_security_approved = (
            result == "scan_completed"
        )

        if engine_security_approved:
            start_button.config(state="normal" if can_start_mining() else "disabled")
            status.config(
                text="XMRig verified. Windows execution "
                     "permission is still required."
            )
        else:
            start_button.config(state="disabled")
            status.config(text="Security verification incomplete.")
            show_security_result(root, result, detail)

    threading.Thread(
        target=worker, daemon=True
    ).start()

    root.after(200, poll)


verify_button = tk.Button(
    container,
    text="VERIFY XMRIG SECURITY",
    command=request_engine_approval,
    bg="#224C58",
    fg=FG
)
verify_button.pack(fill="x", pady=(4, 10))


# Refresh START whenever either agreement changes.
def update_start_permission():
    global engine_security_approved

    consent_valid = (
        xmrig_install_consent.get()
        and sadaqah_consent.get()
    )

    if not consent_valid:
        engine_security_approved = False
        start_button.config(state="disabled")

        if controller.is_running() or controller.phase in (
            "user", "switching", "gaza"
        ):
            stop_mining()
        return

    start_button.config(
        state="normal" if can_start_mining() else "disabled"
    )


xmrig_install_consent.trace_add(
    "write",
    lambda *_: update_start_permission()
)

sadaqah_consent.trace_add(
    "write",
    lambda *_: update_start_permission()
)


def start_mining():
    global accepted, speed

    if not xmrig_install_consent.get():
        messagebox.showwarning(
            "XMRig Installation Agreement",
            "Please accept the independent XMRig "
            "engine agreement first."
        )
        return

    if not engine_security_approved:
        messagebox.showwarning(
            "OMG Security Check",
            "Mining is blocked until XMRig verification "
            "and Windows security checks succeed."
        )
        return

    if not sadaqah_consent.get():
        messagebox.showwarning(
            "Gaza Sadaqah Agreement",
            "Please accept the mining-time allocation first."
        )
        return

    try:
        controller.start(
            wallet.get(),
            threads.get(),
            mode.get()
        )
    except Exception as error:
        messagebox.showerror("OMG Miner", str(error))
        return

    accepted = 0
    speed = "—"
    start_button.config(state="disabled")
    stop_button.config(state="normal")
    status.config(text="Starting XMRig...")
    timer.config(text=f"{controller.LIMIT_SECONDS // 3600:02d}:{(controller.LIMIT_SECONDS // 60) % 60:02d}:{controller.LIMIT_SECONDS % 60:02d}")


stop_pending = False
shutdown_done = threading.Event()

def stop_mining():
    global stop_pending

    if stop_pending:
        return

    stop_pending = True
    shutdown_done.clear()
    start_button.config(state="disabled")
    stop_button.config(state="disabled")
    status.config(text="Stopping XMRig safely...")

    def shutdown():
        global stop_pending
        try:
            controller.stop("Stopped by user")
        finally:
            shutdown_done.set()

    threading.Thread(
        target=shutdown,
        daemon=True,
        name="omg-stop-worker"
    ).start()




# Independent engine availability indicator.
# File existence does not establish security approval.
def engine_health_message():
    try:
        binary = controller.binary_path()
        verified, result = verify_engine(binary)

        if not verified:
            return (
                "ENGINE BLOCKED: " + result +
                " Mining is disabled. If missing, check "
                "Windows Security > Protection history."
            )

        return (
            "HASH VERIFIED: " + result +
            " Windows security approval is still "
            "required. Mining remains disabled."
        )

    except Exception:
        return (
            "ENGINE STATUS UNKNOWN: Verification failed. "
            "Mining remains disabled."
        )


engine_health_label = tk.Label(
    container,
    text=engine_health_message(),
    bg=BG,
    fg="#F0C674",
    font=("Arial", 10),
    justify="left",
    wraplength=440
)
engine_health_label.pack(fill="x", pady=(5, 10))


# Android-style START / STOP action row.
action_row = tk.Frame(container, bg=BG)
action_row.pack(fill="x", pady=(8, 10))

start_button = tk.Button(
    action_row,
    text="START MINING",
    command=start_mining,
    state="disabled",
    bg="#118866",
    fg=FG,
    activebackground="#16A47C",
    activeforeground=FG,
    font=("Arial", 12, "bold"),
    relief="flat",
    padx=8,
    pady=14
)
start_button.pack(
    side="left", fill="x", expand=True,
    padx=(0, 5)
)

stop_button = tk.Button(
    action_row,
    text="STOP MINING",
    command=stop_mining,
    state="disabled",
    bg="#A53B48",
    fg=FG,
    activebackground="#C34A59",
    activeforeground=FG,
    font=("Arial", 12, "bold"),
    relief="flat",
    padx=8,
    pady=14
)
stop_button.pack(
    side="left", fill="x", expand=True,
    padx=(5, 0)
)



tk.Button(
    container,
    text="CHECK MINING EARNINGS",
    command=lambda: webbrowser.open(
        "https://hashvault.pro/monero/"
    ),
    bg="#224C58",
    fg=FG,
    activebackground="#346273",
    activeforeground=FG,
    font=("Arial", 11, "bold"),
    relief="flat",
    pady=11
).pack(fill="x", pady=(5, 10))

last_engine_health_check = time.monotonic()

def refresh_status():
    global accepted, speed, stop_pending, last_phase

    if stop_pending and shutdown_done.is_set():
        stop_pending = False
        shutdown_done.clear()
        start_button.config(state="normal" if can_start_mining() else "disabled")
        stop_button.config(state="disabled")

    current_phase = controller.phase

    if current_phase != last_phase:
        if current_phase in ("user", "switching", "gaza"):
            accepted = 0
            speed = "—"
        last_phase = current_phase

    while not controller.events.empty():
        kind, value = controller.events.get_nowait()

        if kind == "hashrate":
            speed = str(value) + " H/s"
        elif kind == "accepted":
            accepted += int(value)
        elif kind in ("error", "log"):
            status.config(text=str(value))
        elif kind == "status":
            status.config(text=str(value))

    speed_tile.config(text=speed)
    shares_tile.config(text=str(accepted))

    running = controller.is_running()

    if running:
        start_button.config(state="disabled")
        stop_button.config(
            state="disabled" if stop_pending else "normal"
        )
        seconds = controller.remaining_seconds()

        timer.config(text=f"{seconds//3600:02d}:"
                          f"{(seconds//60)%60:02d}:"
                          f"{seconds%60:02d}")

        phase = controller.phase

        if phase == "user":
            phase_text = "YOUR WALLET MINING"
        elif phase == "gaza":
            phase_text = "GAZA SADAQAH MINING"
        elif phase == "switching":
            phase_text = "SWITCHING TO GAZA WALLET"
        else:
            phase_text = "MINING STATUS"

        status.config(
            text=f"{phase_text}\n"
                 f"Hashrate: {speed}\n"
                 f"Accepted shares: {accepted}"
        )

    elif not stop_pending:
        start_button.config(state="normal" if can_start_mining() else "disabled")
        stop_button.config(state="disabled")

    global last_engine_health_check
    now = time.monotonic()
    if now - last_engine_health_check >= 30:
        engine_health_label.config(text=engine_health_message())
        last_engine_health_check = now
    root.after(1000, refresh_status)


closing_app = False

def close_app():
    global closing_app

    if closing_app:
        return

    closing_app = True
    start_button.config(state="disabled")
    stop_button.config(state="disabled")
    status.config(text="Closing OMG Miner safely...")

    finished = threading.Event()
    errors = []

    def shutdown():
        try:
            controller.stop("Application closed")
        except Exception as exc:
            errors.append(str(exc))
        finally:
            finished.set()

    def check_shutdown():
        global closing_app

        if not finished.is_set():
            root.after(100, check_shutdown)
            return

        if errors or controller.is_running():
            closing_app = False
            status.config(
                text="Could not stop miner safely: " +
                (errors[0] if errors else "Process still running")
            )
            stop_button.config(state="normal")
            messagebox.showerror(
                "OMG Miner",
                "Mining may still be active. "
                "Please stop the miner before closing."
            )
            return

        root.destroy()

    threading.Thread(
        target=shutdown,
        daemon=True,
        name="omg-close-worker"
    ).start()

    root.after(100, check_shutdown)


root.protocol("WM_DELETE_WINDOW", close_app)
root.after(1000, refresh_status)

tk.Label(
    container,
    text="Developed by Hassanaat Gems",
    bg=BG, fg="#b8c9d9"
).pack(pady=15)

root.mainloop()
