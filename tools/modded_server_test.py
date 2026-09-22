#!/usr/bin/env python3
"""Boot a real Forge or NeoForge server with a built jar and check the mod works on it.

The Fabric equivalent is `server_test.py`. Forge and NeoForge need their own script because they are
installed rather than launched: you run an installer that writes a `libraries/` tree and an argument
file, and then start the JVM with `@libraries/.../unix_args.txt`.

Testing a Forge jar on a real server is not optional caution. ForgeGradle 6's own `runServer` does not
work here at all (`FindException: Module jopt.simple not found`), and would not be a valid test if it
did - the development run and the shipped jar use different naming. Three separate bugs that made the
Forge jars completely unloadable were all found exactly this way and no other.

What it checks, same as the Fabric script:

  1. The mod loaded with no mixin error.
  2. `/farlands` answers.
  3. The mod's data pack is actually being read. The name differs per loader - Forge lists
     `mod:farlandsreforged`, NeoForge merges everything into one pack called `mod_data` - so a missing
     name does not always mean failure, which is why `--corrupt-advancement` exists.

Usage:
    modded_server_test.py --loader forge    --mc 1.21 --loader-version 51.0.0 --jar mod.jar
    modded_server_test.py --loader neoforge --mc 1.21 --loader-version 21.0.167 --jar mod.jar
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rcon import Rcon, RconError  # noqa: E402
from server_test import (ERROR_PATTERNS, corrupt_advancement, free_port, probe_column,  # noqa: E402
                         summarize_column)

FORGE_MAVEN = "https://maven.minecraftforge.net/net/minecraftforge/forge"
NEOFORGE_MAVEN = "https://maven.neoforged.net/releases/net/neoforged/neoforge"


def log(message):
    print(message, flush=True)


def installer_url(loader, mc, loader_version):
    if loader == "forge":
        full = f"{mc}-{loader_version}"
        return f"{FORGE_MAVEN}/{full}/forge-{full}-installer.jar", full
    return (f"{NEOFORGE_MAVEN}/{loader_version}/neoforge-{loader_version}-installer.jar",
            loader_version)


def args_file(loader, workdir, full_version):
    if loader == "forge":
        return workdir / f"libraries/net/minecraftforge/forge/{full_version}/unix_args.txt"
    return workdir / f"libraries/net/neoforged/neoforge/{full_version}/unix_args.txt"


def java_for(mc):
    home = os.environ.get("JDK21" if mc.startswith("1.21") else "JDK25")
    if home and Path(home, "bin/java").exists():
        return str(Path(home, "bin/java"))
    return "java"


def install(loader, mc, loader_version, workdir, cache, java):
    url, full = installer_url(loader, mc, loader_version)
    installer = cache / Path(url).name
    if not installer.exists():
        log(f"    downloading {loader} {loader_version} installer")
        installer.parent.mkdir(parents=True, exist_ok=True)
        # maven.minecraftforge.net answers urllib's default User-Agent with 403, so send a real one.
        request = urllib.request.Request(url, headers={"User-Agent": "farlands-reforged-tools"})
        with urllib.request.urlopen(request, timeout=300) as response, open(installer, "wb") as out:
            shutil.copyfileobj(response, out)

    marker = args_file(loader, workdir, full)
    if marker.exists():
        return full

    log(f"    installing {loader} server (this pulls libraries; allow a few minutes)")
    # Installing several Minecraft servers at the same time corrupts the downloads - the piston-data
    # server jar comes back with an invalid checksum. Run these one at a time.
    result = subprocess.run(
        [java, "-jar", str(installer), "--installServer", "."],
        cwd=workdir, capture_output=True, text=True, timeout=1800,
    )
    if not marker.exists():
        raise RuntimeError(f"install failed; no {marker.name}\n{result.stdout[-1500:]}")
    return full


def run_test(loader, mc, loader_version, jar, workdir, cache, port, rcon_port, password,
             boot_timeout, corrupt, probe=None):
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "mods").mkdir(exist_ok=True)
    java = java_for(mc)

    full = install(loader, mc, loader_version, workdir, cache, java)

    mod_dest = workdir / "mods" / jar.name
    if corrupt:
        corrupt_advancement(jar, mod_dest)
    else:
        shutil.copy(jar, mod_dest)

    (workdir / "eula.txt").write_text("eula=true\n")
    (workdir / "server.properties").write_text(
        f"server-port={port}\nenable-rcon=true\nrcon.port={rcon_port}\nrcon.password={password}\n"
        "pause-when-empty-seconds=-1\nonline-mode=false\nlevel-seed=1234\nview-distance=4\n"
        "simulation-distance=4\nmax-tick-time=-1\n"
    )

    log_path = workdir / "server.log"
    with open(log_path, "w") as log_file:
        process = subprocess.Popen(
            [java, "-Xmx2G", f"@{args_file(loader, workdir, full).relative_to(workdir)}", "--nogui"],
            cwd=workdir, stdout=log_file, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
        )

    result = {"loader": loader, "mc": mc, "loader_version": loader_version, "jar": jar.name,
              "booted": False, "farlands": "", "datapack": "", "errors": [],
              "pack_listed": False, "parse_error": False}
    try:
        deadline = time.time() + boot_timeout
        while time.time() < deadline:
            if process.poll() is not None:
                break
            text = log_path.read_text(errors="replace")
            if "RCON running" in text or re.search(r"Done \([0-9.]+s\)", text):
                result["booted"] = True
                break
            time.sleep(2)

        if result["booted"]:
            time.sleep(3)
            try:
                with Rcon("127.0.0.1", rcon_port, password, timeout=60) as rcon:
                    result["farlands"] = rcon.command("farlands")
                    result["datapack"] = rcon.command("datapack list")
                    if probe:
                        result["column"] = probe_column(rcon, *probe)
            except (OSError, RconError) as exc:
                result["errors"].append(f"rcon: {exc}")
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGKILL)
        process.wait(timeout=60)

    text = log_path.read_text(errors="replace")
    for pattern in ERROR_PATTERNS:
        for line in re.findall(rf".*{pattern}.*", text):
            result["errors"].append(line.strip()[:200])
    # Forge lists the pack as `mod:farlandsreforged`; NeoForge merges mod data into one `mod_data`.
    listing = result["datapack"]
    result["pack_listed"] = "farlandsreforged" in listing or "mod_data" in listing
    # Any reply counts as an answer, "Unknown or incomplete command" included, so check it is ours.
    result["command_ok"] = "Farlands Reforged" in result["farlands"]
    result["parse_error"] = "farlandsreforged:farlands/where_am_i" in text and "arse" in text
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loader", required=True, choices=["forge", "neoforge"])
    ap.add_argument("--mc", required=True)
    ap.add_argument("--loader-version", required=True)
    ap.add_argument("--jar", required=True, type=Path)
    ap.add_argument("--workdir", type=Path)
    ap.add_argument("--cache", type=Path, default=Path.home() / ".cache/farlands-server-test")
    ap.add_argument("--port", type=int, default=25565)
    ap.add_argument("--rcon-port", type=int, default=25575)
    ap.add_argument("--password", default="farlands")
    ap.add_argument("--boot-timeout", type=float, default=600)
    ap.add_argument("--corrupt-advancement", action="store_true")
    ap.add_argument("--probe", nargs=2, type=int, metavar=("X", "Z"),
                    help="read this terrain column block by block (see server_test.probe_column)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    workdir = args.workdir or Path(f"/tmp/farlands-{args.loader}-{args.mc}")
    for port in (args.port, args.rcon_port):
        if not free_port(port):
            sys.exit(f"port {port} is already in use")

    result = run_test(args.loader, args.mc, args.loader_version, args.jar, workdir, args.cache,
                      args.port, args.rcon_port, args.password, args.boot_timeout,
                      args.corrupt_advancement, args.probe)

    if args.json:
        print(json.dumps(result))
    else:
        log(f"  booted      : {result['booted']}")
        log(f"  /farlands   : {result['farlands'][:120].strip() or '(no answer)'}")
        log(f"  pack listed : {result['pack_listed']}   ({result['datapack'][:90].strip()})")
        if "column" in result:
            log(f"  column      : {summarize_column(result['column'])}")
        if args.corrupt_advancement:
            log(f"  parse error : {result['parse_error']}  (must be True)")
        for error in result["errors"][:5]:
            log(f"  ERROR       : {error}")

    ok = result["booted"] and result["command_ok"] and not result["errors"]
    ok = ok and (result["parse_error"] if args.corrupt_advancement else result["pack_listed"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
