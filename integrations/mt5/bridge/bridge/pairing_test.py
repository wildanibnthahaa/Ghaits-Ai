"""Pairing lifecycle test for Ghaits MT5 Bridge V1."""

from .pairing import PairingManager


def main() -> None:
    manager = PairingManager(ttl_seconds=600)

    pairing = manager.create(
        account="12345678",
        broker="TEST_BROKER",
        server="TEST-SERVER",
    )

    print("=== GENERATED PAIRING ===")
    print(pairing.code)

    print()
    print("=== VALID PAIRING ===")

    valid, error = manager.validate(
        code=pairing.code,
        account="12345678",
        broker="TEST_BROKER",
        server="TEST-SERVER",
    )

    print({
        "valid": valid,
        "error": error,
    })

    print()
    print("=== CONSUME ===")

    consumed = manager.consume(pairing.code)

    print({
        "consumed": consumed,
    })

    print()
    print("=== REUSE TEST ===")

    valid, error = manager.validate(
        code=pairing.code,
        account="12345678",
        broker="TEST_BROKER",
        server="TEST-SERVER",
    )

    print({
        "valid": valid,
        "error": error,
    })

    print()
    print("=== ACCOUNT MISMATCH TEST ===")

    pairing2 = manager.create(
        account="12345678",
        broker="TEST_BROKER",
        server="TEST-SERVER",
    )

    valid, error = manager.validate(
        code=pairing2.code,
        account="99999999",
        broker="TEST_BROKER",
        server="TEST-SERVER",
    )

    print({
        "valid": valid,
        "error": error,
    })


if __name__ == "__main__":
    main()
