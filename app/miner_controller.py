import os
import sys
import time
import queue
import re
import subprocess
import threading
from pathlib import Path


class MinerController:
    # Production Sadaqah schedule
    USER_SECONDS = 3 * 60 * 60
    GAZA_SECONDS = 1 * 60 * 60
    LIMIT_SECONDS = USER_SECONDS + GAZA_SECONDS

    def __init__(self):
        self.process = None
        self.events = queue.Queue()
        self.started_at = None
        self._lock = threading.Lock()
        self._stopping = False
        self.phase = "idle"
        self.user_wallet = None
        self.selected_threads = 3
        self.selected_mode = "auto"

    def binary_path(self):
        base = Path(
            getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
        )
        return base / "xmrig.exe"

    def start(self, wallet, threads=3, mode="auto"):
        wallet = wallet.strip()
        mode = mode.lower()

        if not (
            len(wallet) in (95, 106)
            and wallet[0] in "489"
            and wallet.isalnum()
        ):
            raise ValueError("Enter a valid-looking Monero wallet address")

        if not 1 <= threads <= 6:
            raise ValueError("CPU threads must be between 1 and 6")

        if mode not in ("auto", "light", "fast"):
            raise ValueError("Invalid mining mode")

        binary = self.binary_path()

        if not binary.is_file():
            raise FileNotFoundError(
                "Windows XMRig executable not installed"
            )

        with self._lock:
            if self.process is not None or self._stopping:
                raise RuntimeError(
                    "Miner is running or still stopping"
                )

            command = [
                str(binary),
                "-o", "pool.hashvault.pro:443",
                "--tls",
                "--coin", "monero",
                "--algo", "rx/0",
                "-u", wallet,
                "-p", "OMG-Windows",
                "--threads=" + str(threads),
                "--randomx-mode=" + mode,
                "--print-time=10",
                "--no-color",
                "--pause-on-battery",
            ]

            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            process = subprocess.Popen(
                command,
                cwd=str(binary.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                creationflags=flags,
            )

            self.process = process
            self.started_at = time.monotonic()
            self.phase = "user"
            self.user_wallet = wallet
            self.selected_threads = threads
            self.selected_mode = mode
            self.events.put(("status", "Mining started"))

        threading.Thread(
            target=self._read_output,
            args=(process,),
            daemon=True
        ).start()

        threading.Thread(
            target=self._watch_session,
            args=(process,),
            daemon=True
        ).start()

    def _read_output(self, process):
        speed_pattern = re.compile(
            r"speed\s+10s/60s/15m\s+(\S+)"
        )

        try:
            for line in process.stdout:
                with self._lock:
                    if self.process is not process:
                        break

                match = speed_pattern.search(line)

                if match:
                    self.events.put(
                        ("hashrate", match.group(1))
                    )

                if "accepted (" in line:
                    self.events.put(("accepted", 1))

                if "error" in line.lower():
                    self.events.put(
                        ("log", line.strip()[:250])
                    )

            exit_code = process.wait()

            with self._lock:
                if self.process is process and not self._stopping:
                    self.process = None
                    self.phase = "idle"
                    self.events.put((
                        "status",
                        f"XMRig exited (code {exit_code})"
                    ))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _watch_session(self, process):
        while True:
            with self._lock:
                if self.process is not process:
                    return

                remaining = self.remaining_seconds()

            if remaining <= 0:
                self.stop("Two-hour session completed")
                return

            time.sleep(1)

    def remaining_seconds(self):
        if self.started_at is None:
            return self.LIMIT_SECONDS

        elapsed = time.monotonic() - self.started_at
        return max(0, int(self.LIMIT_SECONDS - elapsed))

    def stop(self, reason="Stopped by user"):
        with self._lock:
            if self._stopping:
                return

            process = self.process

            if process is None:
                return

            self._stopping = True

        try:
            if process.poll() is None:
                process.terminate()

                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

            self.events.put(("status", reason))

        finally:
            with self._lock:
                if self.process is process:
                    self.process = None
                    self.phase = "idle"

                self._stopping = False

    def is_running(self):
        with self._lock:
            return (
                self.process is not None
                and self.process.poll() is None
            )
