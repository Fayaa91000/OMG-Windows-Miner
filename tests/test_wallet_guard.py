import sys
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "app")
)

from wallet_guard import verify_command, WalletGuardError


class WalletGuardTests(unittest.TestCase):

    def setUp(self):
        self.approved = [
            "xmrig.exe",
            "-o", "pool.hashvault.pro:443",
            "-u", "4" + "A" * 94,
            "--threads=3",
        ]

    def test_authorized_command(self):
        self.assertTrue(
            verify_command(self.approved, self.approved)
        )

    def check_rejected(self, position, replacement):
        altered = self.approved.copy()
        altered[position] = replacement

        with self.assertRaises(WalletGuardError):
            verify_command(altered, self.approved)

    def test_wallet_substitution_rejected(self):
        self.check_rejected(4, "4" + "B" * 94)

    def test_pool_substitution_rejected(self):
        self.check_rejected(2, "unauthorized.example:443")

    def test_resource_change_rejected(self):
        self.check_rejected(5, "--threads=6")


    def test_authorized_gaza_handoff(self):
        from wallet_guard import verify_gaza_handoff
        from sadaqah_config import GAZA_WALLET

        command = self.approved.copy()
        command[4] = GAZA_WALLET

        self.assertTrue(
            verify_gaza_handoff(command, self.approved)
        )

    def test_unknown_gaza_wallet_rejected(self):
        from wallet_guard import verify_gaza_handoff

        command = self.approved.copy()
        command[4] = "8" + "B" * 94

        with self.assertRaises(WalletGuardError):
            verify_gaza_handoff(command, self.approved)

    def test_modified_pool_during_handoff_rejected(self):
        from wallet_guard import verify_gaza_handoff
        from sadaqah_config import GAZA_WALLET

        command = self.approved.copy()
        command[4] = GAZA_WALLET
        command[2] = "unauthorized.example:443"

        with self.assertRaises(WalletGuardError):
            verify_gaza_handoff(command, self.approved)

    def test_modified_threads_during_handoff_rejected(self):
        from wallet_guard import verify_gaza_handoff
        from sadaqah_config import GAZA_WALLET

        command = self.approved.copy()
        command[4] = GAZA_WALLET
        command[5] = "--threads=6"

        with self.assertRaises(WalletGuardError):
            verify_gaza_handoff(command, self.approved)


if __name__ == "__main__":
    unittest.main()
