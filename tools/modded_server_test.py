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
import hashlib
import json
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rcon import Rcon, RconError  # noqa: E402
import farman_test  # noqa: E402
from server_test import (ERROR_PATTERNS, corrupt_advancement, free_port, java_for, probe_column,  # noqa: E402
                         summarize_column, vanilla_server_jar)

FORGE_MAVEN = "https://maven.minecraftforge.net/net/minecraftforge/forge"
NEOFORGE_MAVEN = "https://maven.neoforged.net/releases/net/neoforged/neoforge"


def log(message):
    print(message, flush=True)


# NeoForge's Minecraft 1.20.1 builds (47.1.x) are a fork of Forge 47, published as net.neoforged:forge
# rather than net.neoforged:neoforge. They still load Forge 1.20.1 mods, which is how this mod supports
# them - with the Forge jar.
NEOFORGE_1_20_1_MAVEN = "https://maven.neoforged.net/releases/net/neoforged/forge"


def installer_url(loader, mc, loader_version):
    if loader == "forge":
        full = f"{mc}-{loader_version}"
        return f"{FORGE_MAVEN}/{full}/forge-{full}-installer.jar", full
    if mc == "1.20.1":
        full = f"{mc}-{loader_version}"
        return f"{NEOFORGE_1_20_1_MAVEN}/{full}/forge-{full}-installer.jar", full
    return (f"{NEOFORGE_MAVEN}/{loader_version}/neoforge-{loader_version}-installer.jar",
            loader_version)


def launch_args(loader, workdir, full_version):
    """What goes after `java -Xmx2G` to start the installed server.

    Almost every installer writes a JVM args file. Forge 49.0.x (Minecraft 1.20.3 and early 1.20.4)
    instead writes a shim jar that is started with -jar, and no args file at all.
    """
    args = args_file(loader, workdir, full_version)
    if args.exists():
        return [f"@{args.relative_to(workdir)}"]
    shim = workdir / f"{'forge' if loader == 'forge' else 'neoforge'}-{full_version}-shim.jar"
    if shim.exists():
        return ["-jar", shim.name]
    return None


def args_file(loader, workdir, full_version):
    if loader == "forge":
        return workdir / f"libraries/net/minecraftforge/forge/{full_version}/unix_args.txt"
    if full_version.startswith("1.20.1-"):
        return workdir / f"libraries/net/neoforged/forge/{full_version}/unix_args.txt"
    return workdir / f"libraries/net/neoforged/neoforge/{full_version}/unix_args.txt"


def seed_server_jar(installer, mc, workdir, cache):
    """Put a checksum-verified vanilla server jar where the installer will look for it, so it never
    downloads its own. Installers running side by side have corrupted that download ("Downloading
    minecraft server failed, invalid checksum"). The path comes from the installer itself because it
    differs by loader: Forge wants `server-<mc>-bundled.jar`, NeoForge `server-<mc>.jar`.
    """
    with zipfile.ZipFile(installer) as z:
        path = json.loads(z.read("install_profile.json")).get("serverJarPath")
    if not path:
        return
    dest = workdir / path.replace("{LIBRARY_DIR}", "libraries").replace("{MINECRAFT_VERSION}", mc)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(vanilla_server_jar(mc, cache), dest)


def seed_bad_embedded_libraries(installer, workdir):
    """Some installers ship a library inside themselves (under maven/) that does not match the checksum
    in their own profile - NeoForge 20.4.0-beta's universal jar does - and they then fail instead of
    downloading it. Put the Maven copy in place first, but only if it matches the profile's SHA-1, so
    the installer finds a valid file and skips the extraction."""
    with zipfile.ZipFile(installer) as z:
        profile = json.loads(z.read("install_profile.json"))
        for library in profile.get("libraries", []):
            artifact = library.get("downloads", {}).get("artifact", {})
            path, sha1, url = artifact.get("path"), artifact.get("sha1"), artifact.get("url")
            embedded = f"maven/{path}"
            if not (path and sha1 and url) or embedded not in z.namelist():
                continue
            if hashlib.sha1(z.read(embedded)).hexdigest() == sha1:
                continue
            with urllib.request.urlopen(url, timeout=300) as response:
                data = response.read()
            if hashlib.sha1(data).hexdigest() != sha1:
                continue  # neither copy matches; let the installer report it
            log(f"    {library['name']}: embedded copy fails its checksum; seeding the Maven copy")
            dest = workdir / "libraries" / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)


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

    if launch_args(loader, workdir, full):
        return full

    seed_server_jar(installer, mc, workdir, cache)
    seed_bad_embedded_libraries(installer, workdir)
    log(f"    installing {loader} server (this pulls libraries; allow a few minutes)")
    # Installing several Minecraft servers at the same time corrupts the downloads - the piston-data
    # server jar comes back with an invalid checksum. Run these one at a time.
    command = [java, "-jar", str(installer), "--installServer", "."]
    result = subprocess.run(command, cwd=workdir, capture_output=True, text=True, timeout=1800)
    if not launch_args(loader, workdir, full) and f"UnknownHostException: {RETIRED_HOST}" in result.stdout:
        log(f"    installer crashed looking up {RETIRED_HOST}; retrying with a hosts file")
        hosts = write_hosts_file(installer, workdir)
        result = subprocess.run([java, f"-Djdk.net.hosts.file={hosts}"] + command[1:],
                                cwd=workdir, capture_output=True, text=True, timeout=1800)
    if not launch_args(loader, workdir, full):
        raise RuntimeError(f"install failed; no unix_args.txt or shim jar\n{result.stdout[-1500:]}")
    return full


# Mojang retired its old auth server, and installers from before that (NeoForge 20.4.0-beta, for one)
# resolve it on startup just to print a diagnostic, then crash on the null result. Every download host
# still works, so the fix is to resolve those ourselves and give the retired one a dummy address.
RETIRED_HOST = "authserver.mojang.com"
INSTALLER_HOSTS = {"launchermeta.mojang.com", "piston-meta.mojang.com", "piston-data.mojang.com",
                   "libraries.minecraft.net", "sessionserver.mojang.com", "files.minecraftforge.net",
                   "maven.minecraftforge.net", "maven.neoforged.net"}


def write_hosts_file(installer, workdir):
    """A hosts file for `-Djdk.net.hosts.file`, which makes the JVM resolve names from it alone - so it
    lists every host the installer downloads from, read out of its own profile, resolved just now."""
    hosts = set(INSTALLER_HOSTS)
    with zipfile.ZipFile(installer) as z:
        for member in ("install_profile.json", "version.json"):
            if member in z.namelist():
                hosts.update(re.findall(r"https?://([^/\"]+)", z.read(member).decode("utf-8")))
    lines = [f"127.0.0.1 {RETIRED_HOST}"]
    for host in sorted(hosts - {RETIRED_HOST}):
        try:
            lines.append(f"{socket.gethostbyname(host)} {host}")
        except OSError:
            pass
    path = workdir / "installer-hosts"
    path.write_text("\n".join(lines) + "\n")
    return path


def run_test(loader, mc, loader_version, jar, workdir, cache, port, rcon_port, password,
             boot_timeout, corrupt, probe=None, farman=False):
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
        "pause-when-empty-seconds=-1\nonline-mode=false\nwhite-list=false\nlevel-seed=1234\nview-distance=4\n"
        "simulation-distance=4\nmax-tick-time=-1\n"
    )

    log_path = workdir / "server.log"
    with open(log_path, "w") as log_file:
        process = subprocess.Popen(
            [java, "-Xmx2G", *launch_args(loader, workdir, full), "--nogui"],
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
                    if farman:
                        result.update(farman_test.run(rcon, mc, port, workdir, log_path))
            except (OSError, RconError) as exc:
                result["errors"].append(f"rcon: {exc}")
    finally:
        exit_code = process.poll()
        if exit_code is None:
            process.send_signal(signal.SIGKILL)
        process.wait(timeout=60)

    text = log_path.read_text(errors="replace")
    if not result["booted"]:
        # Say why. A server that dies of something ERROR_PATTERNS does not know used to come back as
        # booted=false with an empty error list, which says nothing about the mod either way.
        why = (f"server exited with code {exit_code} before booting" if exit_code is not None
               else f"server did not boot within {boot_timeout:.0f}s")
        tail = [line.strip()[:200] for line in text.splitlines()[-5:] if line.strip()]
        result["errors"].append(why + (": " + " | ".join(tail) if tail else " (no output)"))
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
    ap.add_argument("--farman", action="store_true",
                    help="put a headless player in the Far Lands and make FarMan appear (see farman_test.py)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    workdir = args.workdir or Path(f"/tmp/farlands-{args.loader}-{args.mc}")
    for port in (args.port, args.rcon_port):
        if not free_port(port):
            sys.exit(f"port {port} is already in use")

    result = run_test(args.loader, args.mc, args.loader_version, args.jar, workdir, args.cache,
                      args.port, args.rcon_port, args.password, args.boot_timeout,
                      args.corrupt_advancement, args.probe, args.farman)

    if args.json:
        print(json.dumps(result))
    else:
        log(f"  booted      : {result['booted']}")
        log(f"  /farlands   : {result['farlands'][:120].strip() or '(no answer)'}")
        log(f"  pack listed : {result['pack_listed']}   ({result['datapack'][:90].strip()})")
        if "column" in result:
            log(f"  column      : {summarize_column(result['column'])}")
        if "farman" in result:
            failing = [name for name, ok in result["farman_checks"].items() if not ok]
            log(f"  farman      : {result['farman']}" + (f"  (failing: {', '.join(failing)})" if failing else ""))
            for note in result["farman_notes"][:8]:
                log(f"    {note}")
        if args.corrupt_advancement:
            log(f"  parse error : {result['parse_error']}  (must be True)")
        for error in result["errors"][:5]:
            log(f"  ERROR       : {error}")

    ok = result["booted"] and result["command_ok"] and not result["errors"]
    ok = ok and (result["parse_error"] if args.corrupt_advancement else result["pack_listed"])
    ok = ok and (not args.farman or result.get("farman") != "failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
