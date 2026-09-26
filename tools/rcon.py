#!/usr/bin/env python3
"""A minimal Minecraft RCON client, enough to drive a test server headlessly.

Used to check a built jar on a real server: run `/farlands`, confirm `/datapack list` mentions the
mod's pack, and `forceload add` chunks so the region files exist for tools/region_slice.py.

Two things about the server side are worth knowing, because both look like a hang:

  * `pause-when-empty-seconds=-1` must be in server.properties. An empty server otherwise pauses
    itself and RCON commands never come back.
  * `/advancement grant @a only <id>` is useless here. The selector resolves first and always fails
    with "No player was found" before the advancement id is ever looked at, so it can neither confirm
    nor deny that an advancement registered.

Usage:
    rcon.py --port 25575 --password PW "farlands" "datapack list"
"""

import argparse
import select
import socket
import struct
import sys

LOGIN, COMMAND = 3, 2
MAX_CHUNK = 4096  # RconClient.sendCmdResponse splits replies into packets of this many bytes
AUTH_FAILED = -1
FENCE_WAIT = 2.0  # seconds to wait for a reply before deciding a command was silent


class RconError(Exception):
    pass


class Rcon:
    def __init__(self, host="127.0.0.1", port=25575, password="", timeout=30.0):
        self.host, self.port, self.password, self.timeout = host, port, password, timeout
        self.sock = None
        self._next_id = 0
        self._last_body_bytes = 0

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.close()

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        request_id = self._send(LOGIN, self.password)
        response_id, _ = self._recv()
        # The server answers a failed login with -1, and a successful one by echoing the request id.
        if response_id == AUTH_FAILED or response_id != request_id:
            raise RconError("RCON authentication failed")

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def command(self, text, fence=None):
        """Run one command and return its reply.

        Forge 1.20.6 and later send no RCON reply at all to a command that produces no output - where
        vanilla and NeoForge send an empty one - so waiting for it hangs until the socket times out. For
        a command that may succeed silently, pass `fence`: a command that always answers (`list`, say).
        If nothing has come back after FENCE_WAIT seconds the fence is sent, and its reply marks the end.
        It cannot be sent together with the command: the server reads one packet per socket read and
        drops the connection when a second arrives in the same one.
        """
        request_id = self._send(COMMAND, text)
        if fence is not None and not select.select([self.sock], [], [], FENCE_WAIT)[0]:
            fence_id = self._send(COMMAND, fence)
            chunks = []
            while True:
                response_id, body = self._recv()
                if response_id == request_id:
                    chunks.append(body)
                elif response_id == fence_id and self._last_body_bytes < MAX_CHUNK:
                    return "".join(chunks)
        chunks = []
        while True:
            response_id, body = self._recv()
            if response_id == request_id:
                chunks.append(body)
                # The server splits a reply into packets of at most MAX_CHUNK bytes, so a shorter one
                # is the last. Stopping there, rather than always waiting for the socket to go quiet,
                # takes a flat 0.3s off every command - most of the time of a terrain probe.
                if self._last_body_bytes < MAX_CHUNK:
                    break
            # A full-size packet may or may not be followed by more; silence is the only other
            # end-of-reply signal the protocol offers.
            if not select.select([self.sock], [], [], 0.3)[0]:
                break
        return "".join(chunks)

    def _send(self, kind, body):
        self._next_id += 1
        payload = struct.pack("<ii", self._next_id, kind) + body.encode("utf-8") + b"\x00\x00"
        self.sock.sendall(struct.pack("<i", len(payload)) + payload)
        return self._next_id

    def _recv_exactly(self, count):
        buffer = b""
        while len(buffer) < count:
            part = self.sock.recv(count - len(buffer))
            if not part:
                raise RconError("connection closed by server")
            buffer += part
        return buffer

    def _recv(self):
        (length,) = struct.unpack("<i", self._recv_exactly(4))
        payload = self._recv_exactly(length)
        response_id, _kind = struct.unpack("<ii", payload[:8])
        # Raw size, not the decoded text's: a character split across two packets decodes with
        # replacement characters and would throw the length check in command() off.
        self._last_body_bytes = len(payload) - 10
        return response_id, payload[8:-2].decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=25575)
    ap.add_argument("--password", required=True)
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("commands", nargs="+")
    args = ap.parse_args()

    try:
        with Rcon(args.host, args.port, args.password, args.timeout) as rcon:
            for command in args.commands:
                print(f"> {command}")
                print(rcon.command(command))
    except (OSError, RconError) as exc:
        sys.exit(f"rcon: {exc}")


if __name__ == "__main__":
    main()
