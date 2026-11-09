"""OMG Security Guard: validate authorized mining commands.

Pure validation only. No mining, network, or system changes.
"""


class WalletGuardError(ValueError):
    pass


def verify_command(actual, approved):
    """Reject any change to an approved mining command."""
    if not isinstance(actual, (list, tuple)):
        raise WalletGuardError("Invalid mining command.")

    if not isinstance(approved, (list, tuple)):
        raise WalletGuardError("Invalid approved command.")

    if not approved or len(actual) != len(approved):
        raise WalletGuardError("Mining command integrity failed.")

    if not all(isinstance(x, str) for x in actual + list(approved)):
        raise WalletGuardError("Invalid mining command arguments.")

    if tuple(actual) != tuple(approved):
        raise WalletGuardError(
            "Mining command differs from the authorized session."
        )

    return True


def verify_gaza_handoff(actual, approved):
    """Allow only the scheduled wallet change to Gaza."""
    from sadaqah_config import GAZA_WALLET

    if not isinstance(approved, (list, tuple)):
        raise WalletGuardError("Invalid approved command.")

    if approved.count("-u") != 1:
        raise WalletGuardError("Wallet option invalid.")

    position = approved.index("-u") + 1

    if position >= len(approved):
        raise WalletGuardError("Wallet address missing.")

    expected = list(approved)
    expected[position] = GAZA_WALLET

    return verify_command(actual, expected)
