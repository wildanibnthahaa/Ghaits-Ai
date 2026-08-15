"""Generate pairing codes for the running Ghaits MT5 Bridge."""

from __future__ import annotations

import argparse
import socket
import json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18788)
    args = parser.parse_args()

    message = {
        "v": 1,
        "type": "pairing_create",
        "id": "pairing_cli_001",
    }

    with socket.create_connection(
        (args.host, args.port),
        timeout=3,
    ) as sock:
        sock.sendall(
            (json.dumps(message) + "\n").encode()
        )

        response = json.loads(
            sock.recv(4096).decode()
        )

    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
