#!/usr/bin/env python3
"""Boot a real Fabric server with a built jar and check that the mod actually works on it.

This exists because the two worst bugs this mod has shipped were both invisible to every other kind of
test. The advancement never registered on Fabric for three releases - no crash, no log line, terrain
perfect - and the Forge jars silently dropped their data pack for the same reason. A jar that compiles,
passes verify_artifact.py and generates correct terrain can still be broken in a way only a running
server shows.

So each run asks three questions:

  1. Did the mod load without a mixin error?          (scan the log)
  2. Does `/farlands` answer?                         (RCON)
  3. Is the mod's data pack actually being read?      (`/datapack list` must name it)

Question 3 is the whole point. On Fabric the answer was "no" for every release before 0.4.0.

Why not Loom's `runServer`: it runs the *development* classes, not the jar that ships, and for Forge the
two use different naming entirely. Only a real server tests the artifact.

Usage:
    server_test.py --mc 1.21 --jar path/to/mod.jar [--port 25565] [--rcon-port 25575]
    server_test.py --mc 1.21 --jar ... --corrupt-advancement   # the loader-independent pack probe
"""

import argparse
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile
from hashlib import sha1
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rcon import Rcon, RconError  # noqa: E402

MANIFEST = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
FABRIC_META = "https://meta.fabricmc.net/v2/versions"
ADVANCEMENT = "data/farlandsreforged/advancement/farlands/where_am_i.json"

# Mixin failures are fatal but the server keeps writing for a while, so match the shapes rather than
# waiting for a crash. "No refMap loaded" is a warning on a healthy server, so it is deliberately not
# here - it was, and it produced false alarms.
ERROR_PATTERNS = [
    r"Mixin apply failed", r"was not located in the target class", r"@Redirect target",
    r"Critical injection failure", r"InvalidInjectionException", r"MixinApplyError",
    r"Failed to load mod", r"NoSuchMethodException", r"MixinTransformerError",
]


def log(message):
    print(message, flush=True)


def download(url, dest, expect_sha1=None):
    """Download once, and verify. Mojang's CDN has handed back truncated jars under load before."""
    if dest.exists() and expect_sha1:
        if sha1(dest.read_bytes()).hexdigest() == expect_sha1:
            return dest
        dest.unlink()
    elif dest.exists():
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=180) as response, open(tmp, "wb") as out:
        shutil.copyfileobj(response, out)

    if expect_sha1:
        got = sha1(tmp.read_bytes()).hexdigest()
        if got != expect_sha1:
            tmp.unlink()
            raise RuntimeError(f"checksum mismatch for {url}: got {got}, want {expect_sha1}")
    tmp.rename(dest)
    return dest


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def vanilla_server_jar(mc, cache):
    dest = cache / f"minecraft_server.{mc}.jar"
    if dest.exists():
        return dest
    manifest = fetch_json(MANIFEST)
    entry = next((v for v in manifest["versions"] if v["id"] == mc), None)
    if entry is None:
        raise RuntimeError(f"Minecraft {mc} is not in the version manifest")
    server = fetch_json(entry["url"])["downloads"]["server"]
    log(f"    downloading Minecraft {mc} server ({server['size'] // (1 << 20)} MB)")
    return download(server["url"], dest, server["sha1"])


def fabric_launcher(mc, cache):
    dest = cache / f"fabric-server-launch-{mc}.jar"
    if dest.exists():
        return dest
    loader = fetch_json(f"{FABRIC_META}/loader/{mc}")[0]["loader"]["version"]
    installer = fetch_json(f"{FABRIC_META}/installer")[0]["version"]
    log(f"    downloading Fabric launcher (loader {loader}, installer {installer})")
    return download(f"{FABRIC_META}/loader/{mc}/{loader}/{installer}/server/jar", dest)


def corrupt_advancement(src, dest):
    """Rewrite a jar with deliberately invalid advancement JSON.

    This is the only loader-independent proof that a data pack is being read: a server that reads it
    logs a parse error, and a server that does not stays completely silent and starts normally.
    """
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = b"{ this is not valid json" if item.filename == ADVANCEMENT else zin.read(item.filename)
            zout.writestr(item, data)
    return dest


def free_port(port):
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) != 0


def java_for(mc):
    """1.21.x needs Java 21; the 26.x family needs Java 25."""
    home = os.environ.get("JDK21" if mc.startswith("1.21") else "JDK25")
    if home and Path(home, "bin/java").exists():
        return str(Path(home, "bin/java"))
    return "java"


def run_test(mc, jar, workdir, cache, port, rcon_port, password, boot_timeout, corrupt):
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "mods").mkdir(exist_ok=True)

    server_jar = vanilla_server_jar(mc, cache)
    launcher = fabric_launcher(mc, cache)

    mod_dest = workdir / "mods" / jar.name
    if corrupt:
        corrupt_advancement(jar, mod_dest)
    else:
        shutil.copy(jar, mod_dest)

    (workdir / "eula.txt").write_text("eula=true\n")
    # pause-when-empty-seconds=-1 matters: an empty server otherwise pauses itself and every RCON
    # command hangs forever, which looks exactly like a crash.
    (workdir / "server.properties").write_text(
        f"server-port={port}\nenable-rcon=true\nrcon.port={rcon_port}\nrcon.password={password}\n"
        "pause-when-empty-seconds=-1\nonline-mode=false\nlevel-seed=1234\nview-distance=4\n"
        "simulation-distance=4\nsync-chunk-writes=false\nmax-tick-time=-1\n"
    )

    log_path = workdir / "server.log"
    with open(log_path, "w") as log_file:
        process = subprocess.Popen(
            [java_for(mc), f"-Dfabric.installer.server.gameJar={server_jar}",
             "-Xmx2G", "-jar", str(launcher), "nogui"],
            cwd=workdir, stdout=log_file, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
        )

    result = {"mc": mc, "jar": jar.name, "booted": False, "farlands": "", "datapack": "",
              "errors": [], "pack_listed": False, "parse_error": False}
    try:
        deadline = time.time() + boot_timeout
        while time.time() < deadline:
            if process.poll() is not None:
                break
            if 'RCON running' in log_path.read_text(errors="replace") or \
               re.search(r'Done \([0-9.]+s\)', log_path.read_text(errors="replace")):
                result["booted"] = True
                break
            time.sleep(2)

        if result["booted"]:
            time.sleep(3)  # RCON binds a moment after the log line
            try:
                with Rcon("127.0.0.1", rcon_port, password, timeout=60) as rcon:
                    result["farlands"] = rcon.command("farlands")
                    result["datapack"] = rcon.command("datapack list")
            except (OSError, RconError) as exc:
                result["errors"].append(f"rcon: {exc}")
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGKILL)  # a plain TERM is ignored while the server is busy
        process.wait(timeout=60)

    text = log_path.read_text(errors="replace")
    for pattern in ERROR_PATTERNS:
        for line in re.findall(rf".*{pattern}.*", text):
            result["errors"].append(line.strip()[:200])
    result["pack_listed"] = "farlandsreforged" in result["datapack"]
    result["parse_error"] = "farlandsreforged:farlands/where_am_i" in text and "arse" in text
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mc", required=True)
    ap.add_argument("--jar", required=True, type=Path)
    ap.add_argument("--workdir", type=Path)
    ap.add_argument("--cache", type=Path, default=Path.home() / ".cache/farlands-server-test")
    ap.add_argument("--port", type=int, default=25565)
    ap.add_argument("--rcon-port", type=int, default=25575)
    ap.add_argument("--password", default="farlands")
    ap.add_argument("--boot-timeout", type=float, default=300)
    ap.add_argument("--corrupt-advancement", action="store_true")
    ap.add_argument("--json", action="store_true", help="print the result as one JSON line")
    args = ap.parse_args()

    workdir = args.workdir or Path(f"/tmp/farlands-test-{args.mc}")
    for port in (args.port, args.rcon_port):
        if not free_port(port):
            sys.exit(f"port {port} is already in use")

    result = run_test(args.mc, args.jar, workdir, args.cache, args.port, args.rcon_port,
                      args.password, args.boot_timeout, args.corrupt_advancement)

    if args.json:
        print(json.dumps(result))
    else:
        log(f"  booted      : {result['booted']}")
        log(f"  /farlands   : {result['farlands'][:120].strip() or '(no answer)'}")
        log(f"  pack listed : {result['pack_listed']}")
        if args.corrupt_advancement:
            log(f"  parse error : {result['parse_error']}  (must be True - proves the pack is read)")
        for error in result["errors"][:5]:
            log(f"  ERROR       : {error}")

    ok = result["booted"] and result["farlands"] and not result["errors"]
    ok = ok and (result["parse_error"] if args.corrupt_advancement else result["pack_listed"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
