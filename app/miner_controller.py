import os
import sys
import time
import queue
import re
import subprocess
import threading
from pathlib import Path
from sadaqah_config import GAZA_WALLET


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
        self._stop_requested = threading.Event()
        self.phase = "idle"
        self.user_wallet = None
        self._approved_mining_command = None
        self.selected_threads = 3
        self.selected_mode = "auto"

    def binary_path(self):
        # Independent XMRig location for Windows.
        if sys.platform == "win32":
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                external = (
                    Path(local_appdata)
                    / "OMG Windows Miner"
                    / "engine"
                    / "xmrig.exe"
                )
                if external.is_file():
                    return external

        # Preserve compatibility with existing bundled builds.
        base = Path(
            getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
        )
        return base / "xmrig.exe"

    def _launch_xmrig(self, command, binary, flags):
        """Launch only the verified official XMRig executable."""
        import hashlib

        expected = (
            "6fa80698d7268f6e88aa88c06fb27ee99e1bcee747c"
            "2e76911e6206a5b1aeeb3"
        )

        if binary.is_symlink() or not binary.is_file():
            raise RuntimeError(
                "XMRig engine missing or unsupported file link."
            )

        digest = hashlib.sha256()
        with binary.open("rb") as stream:
            for chunk in iter(
                lambda: stream.read(1048576), b""
            ):
                digest.update(chunk)

        if digest.hexdigest() != expected:
            raise RuntimeError(
                "XMRig SHA-256 verification failed. "
                "Mining was not started."
            )

        if not command or str(command[0]) != str(binary):
            raise RuntimeError(
                "XMRig launch path does not match verified engine."
            )

        return subprocess.Popen(
            command,
            cwd=str(binary.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            creationflags=flags,
        )

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

            self._stop_requested.clear()

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

            process = self._launch_xmrig(
                command, binary, flags
            )

            self._approved_mining_command = tuple(command)
            self._mining_command = list(command)
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

    def _switch_to_gaza(self):
        """Replace user XMRig only after its process exits."""
        with self._lock:
            if (
                self.phase != "user"
                or self.process is None
                or self._stopping
                or self._stop_requested.is_set()
            ):
                return False

            old = self.process
            self._stopping = True
            self.phase = "switching"

            command = list(self._mining_command)
            command[command.index("-u") + 1] = GAZA_WALLET
            binary = self.binary_path()
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        new_process = None

        try:
            if old.poll() is None:
                old.terminate()
                try:
                    old.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    old.kill()
                    old.wait()

            with self._lock:
                if self.process is old:
                    self.process = None

            if self._stop_requested.is_set():
                return False

            with self._lock:
                if self._stop_requested.is_set():
                    return False

                new_process = self._launch_xmrig(
                    command, binary, flags
                )
                self.process = new_process
                self.phase = "gaza"

            threading.Thread(
                target=self._read_output,
                args=(new_process,),
                daemon=True
            ).start()

            threading.Thread(
                target=self._watch_session,
                args=(new_process,),
                daemon=True
            ).start()

            self.events.put((
                "status", "Gaza Sadaqah mining started"
            ))
            return True

        except Exception as error:
            self.events.put((
                "error", "Gaza handoff failed: " + str(error)
            ))
            return False

        finally:
            with self._lock:
                if self.phase == "switching":
                    self.phase = "idle"
                self._stopping = False

            if self._stop_requested.is_set():
                self.stop("Stopped by user")

    def _watch_session(self, process):
        while True:
            with self._lock:
                if self.process is not process:
                    return

                remaining = self.remaining_seconds()

            if remaining <= 0:
                self.stop("Four-hour Sadaqah session completed")
                return

            with self._lock:
                switch_due = (
                    self.phase == "user"
                    and not self._stopping
                    and not self._stop_requested.is_set()
                    and self.started_at is not None
                    and time.monotonic() - self.started_at
                        >= self.USER_SECONDS
                )

            if switch_due:
                self._switch_to_gaza()
                return

            time.sleep(1)

    def remaining_seconds(self):
        if self.started_at is None:
            return self.LIMIT_SECONDS

        elapsed = time.monotonic() - self.started_at
        return max(0, int(self.LIMIT_SECONDS - elapsed))

    def stop(self, reason="Stopped by user"):
        self._stop_requested.set()
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
