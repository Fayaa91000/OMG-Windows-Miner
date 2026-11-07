import tkinter as tk
from tkinter import ttk, messagebox
from miner_controller import MinerController
import threading

BG = "#101827"
FG = "#ffffff"
ACCENT = "#13a884"

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


tk.Label(
    container, text="OMG MINER",
    font=("Arial", 25, "bold"),
    bg=BG, fg=FG
).pack(pady=10)

tk.Label(
    container,
    text="Open Mining Gateway | Windows Edition",
    bg=BG, fg="#b8c9d9"
).pack(pady=5)

tk.Label(
    container,
    text="Your Monero Wallet Address",
    bg=BG, fg=FG
).pack(pady=(20, 5))

wallet = tk.StringVar()
tk.Entry(
    container,
    textvariable=wallet,
    font=("Arial", 11),
    width=50
).pack(fill="x", pady=5)

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

tk.Label(
    container,
    text="Session Remaining",
    font=("Arial", 12),
    bg=BG, fg="#b8c9d9"
).pack(pady=(15, 0))

timer = tk.Label(
    container,
    text="00:05:00",
    font=("Arial", 28, "bold"),
    bg=BG, fg=ACCENT
)
timer.pack(pady=5)

status = tk.Label(
    container,
    text="Status: Mining engine not connected\n"
         "Hashrate: —\nAccepted shares: 0",
    font=("Arial", 11),
    bg=BG, fg=FG,
    justify="center"
)
status.pack(pady=15)

sadaqah_consent = tk.BooleanVar(value=False)

tk.Checkbutton(
    container,
    text=(
        "I agree: 2 minutes for my wallet and "
        "3 minutes for Gaza Sadaqah.\n"
        "40% / 60% mining time. "
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
accepted = 0
speed = "—"
last_phase = "idle"

def start_mining():
    global accepted, speed

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


start_button = tk.Button(
    container,
    text="START MINING",
    command=start_mining,
    bg=ACCENT,
    fg=FG,
    font=("Arial", 11, "bold")
)
start_button.pack(fill="x", pady=5)

stop_button = tk.Button(
    container,
    text="STOP MINING",
    command=stop_mining,
    state="disabled"
)
stop_button.pack(fill="x", pady=5)


def refresh_status():
    global accepted, speed, stop_pending, last_phase

    if stop_pending and shutdown_done.is_set():
        stop_pending = False
        shutdown_done.clear()
        start_button.config(state="normal")
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
        start_button.config(state="normal")
        stop_button.config(state="disabled")

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
