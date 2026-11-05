import tkinter as tk
from tkinter import ttk

BG = "#101827"
FG = "#ffffff"
ACCENT = "#13a884"

root = tk.Tk()
root.title("OMG Windows Miner")
root.geometry("520x620")
root.minsize(460, 550)
root.configure(bg=BG)

container = tk.Frame(root, bg=BG, padx=25, pady=20)
container.pack(fill="both", expand=True)

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

threads = tk.IntVar(value=3)

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
    text="02:00:00",
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

tk.Button(
    container,
    text="START MINING — ENGINE NOT READY",
    state="disabled",
    bg=ACCENT, fg=FG,
    font=("Arial", 11, "bold")
).pack(fill="x", pady=5)

tk.Button(
    container,
    text="STOP MINING",
    state="disabled"
).pack(fill="x", pady=5)

tk.Label(
    container,
    text="Developed by Hassanaat Gems",
    bg=BG, fg="#b8c9d9"
).pack(pady=15)

root.mainloop()
