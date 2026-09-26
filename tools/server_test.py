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
import farman_test  # noqa: E402
from rcon import Rcon, RconError  # noqa: E402

MANIFEST = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
FABRIC_META = "https://meta.fabricmc.net/v2/versions"
# Minecraft 1.21 renamed the folder from advancements/ to advancement/; a jar carries whichever its
# version reads.
ADVANCEMENTS = {f"data/farlandsreforged/{folder}/farlands/where_am_i.json"
                for folder in ("advancement", "advancements")}

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
    corrupted = 0
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename in ADVANCEMENTS:
                data, corrupted = b"{ this is not valid json", corrupted + 1
            else:
                data = zin.read(item.filename)
            zout.writestr(item, data)
    if corrupted != 1:
        # Corrupting nothing would make a working pack look unread, so refuse rather than mislead.
        raise SystemExit(f"{src}: expected one where_am_i.json to corrupt, found {corrupted}")
    return dest


def free_port(port):
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) != 0


# The blocks of 1.20's #minecraft:replaceable tag, copied from the 1.20 server jar, less the air
# variants, water and lava, which the probe tests first. "grass" became short_grass only in 1.20.3.
REPLACEABLE_BEFORE_1_20 = ("grass", "fern", "dead_bush", "seagrass", "tall_seagrass", "fire", "soul_fire",
                           "snow", "vine", "glow_lichen", "light", "tall_grass", "large_fern",
                           "structure_void", "bubble_column", "warped_roots", "nether_sprouts",
                           "crimson_roots", "hanging_roots")


def chunk_loaded(rcon, x, z):
    """True once the chunk holding (x, z) is loaded and generated.

    `execute if loaded` only exists from 1.19.4; before that it is a syntax error, which once made every
    1.19 - 1.19.3 terrain probe time out on a chunk that had long since generated. There, any block test
    answers "That position is not loaded" until the chunk is loaded, and passes or fails after.
    """
    reply = rcon.command(f"execute if loaded {x} 0 {z}")
    if "passed" in reply or "failed" in reply:
        return "passed" in reply
    reply = rcon.command(f"execute if block {x} 0 {z} minecraft:air")
    return "passed" in reply or "failed" in reply


def probe_column(rcon, x, z, y_min=-64, y_max=319, load_timeout=300):
    """Read one column of generated terrain over RCON, top down, as a string with one character per
    block: '.' air, '~' water or lava, ',' a plant, tree or other replaceable block, '#' anything solid.

    This proves the terrain half of the mod on the shipped jar, which the other checks cannot: a
    worldgen mixin that silently fails to apply leaves a server that boots, answers `/farlands` and
    lists the pack perfectly. Only vanilla commands are used, so it works the same on every loader.
    Plants get their own class because two Minecraft versions on one seed disagree about seagrass
    and flowers, but never about where the walls are. Trees (logs and leaves) count as plants too: they
    depend on the biome, and whether a neighbouring tree has reached into the column depends on which
    chunks happened to generate first.
    """
    rcon.command(f"forceload add {x} {z}")
    deadline = time.time() + load_timeout
    while not chunk_loaded(rcon, x, z):
        if time.time() > deadline:
            raise RconError(f"chunk at {x} {z} never finished generating")
        time.sleep(2)

    # Air by name, not #minecraft:air: that tag only exists from 1.21, and on older versions the test
    # errors, air falls through to #replaceable, and every air block reads as a plant.
    tests = ((".", "minecraft:air"), (".", "minecraft:cave_air"), (".", "minecraft:void_air"),
             ("~", "minecraft:water"), ("~", "minecraft:lava"), (",", "#minecraft:replaceable"))
    # #minecraft:replaceable itself only exists from 1.20. Before that, test its members by name.
    if "Unknown block tag" in rcon.command(f"execute if block {x} 0 {z} #minecraft:replaceable"):
        tests = tests[:-1] + tuple((",", f"minecraft:{name}") for name in REPLACEABLE_BEFORE_1_20)
    tests += ((",", "#minecraft:logs"), (",", "#minecraft:leaves"))
    column = []
    for y in range(y_max, y_min - 1, -1):
        for char, test in tests:
            reply = rcon.command(f"execute if block {x} {y} {z} {test}")
            if "passed" in reply:
                column.append(char)
                break
            if "failed" not in reply:
                # Anything else is an error (an unknown block or tag), not an answer.
                raise RconError(f"`execute if block ... {test}` answered {reply!r}")
        else:
            column.append("#")
    return "".join(column)


CLASSIC_START = 12_550_821


def moved_start(rcon, start_x, start_z):
    """Move where the Far Lands start, then read the column 29 blocks past the new wall on X.

    The mod snaps a start out to the 4-block noise grid the classic one sits on, so the wall is at
    start + (classic - start) mod 4, and the column 29 blocks beyond it reads the same legacy noise as the
    classic probe at 12,550,850. Its upper half - the wall and the stacked sheets - must match that probe.
    The lower half also depends on the local continent and depth noise, so it differs from place to place.
    """
    replies = [rcon.command(f"farlands set x {start_x}"), rcon.command(f"farlands set z {start_z}")]
    wall = start_x + (CLASSIC_START - start_x) % 4
    column = probe_column(rcon, wall + 29, 0)
    rcon.command("farlands reset")
    return {"start_replies": replies, "moved_probe": [wall + 29, 0], "moved_column": column}


def summarize_column(column, y_max=319):
    """Run-length form of probe_column's output, e.g. '. 319..178 | # 177..94 | . 93..64 ...'."""
    runs, start = [], 0
    for i in range(1, len(column) + 1):
        if i == len(column) or column[i] != column[start]:
            runs.append(f"{column[start]} {y_max - start}..{y_max - i + 1}")
            start = i
    return " | ".join(runs)


DEFAULT_JDKS = {
    "JDK17": Path.home() / "Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home",
    "JDK21": Path.home() / "Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home",
    "JDK25": Path("/Library/Java/JavaVirtualMachines/jdk-25.jdk/Contents/Home"),
}


def java_for(mc):
    """The Java each Minecraft version ships with: 17 before 1.20.5, 21 up to 1.21.11, 25 for 26.x.

    Testing on the oldest Java a version supports is the point - that is what its players run.

    Never falls back to whatever `java` is on the PATH. It used to, and a 1.20.6 Forge server quietly
    ran on Java 25, where Forge 50.0.0's ASM cannot even read java/lang/Boolean ("Unsupported class
    file major version 69") - a failure that looks exactly like a broken mod.
    """
    parts = tuple(int(p) for p in mc.split("."))
    var = "JDK17" if parts < (1, 20, 5) else "JDK21" if parts[0] == 1 else "JDK25"
    home = Path(os.environ.get(var) or DEFAULT_JDKS[var])
    if not (home / "bin/java").exists():
        raise SystemExit(f"no Java for Minecraft {mc}: set {var} to a JDK home ({home} does not exist)")
    return str(home / "bin/java")


def run_test(mc, jar, workdir, cache, port, rcon_port, password, boot_timeout, corrupt,
             forceload=None, settle=90, probe=None, farman=False, start=None):
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
        "pause-when-empty-seconds=-1\nonline-mode=false\nwhite-list=false\nlevel-seed=1234\nview-distance=4\n"
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
                with Rcon("127.0.0.1", rcon_port, password, timeout=120) as rcon:
                    result["farlands"] = rcon.command("farlands")
                    result["datapack"] = rcon.command("datapack list")
                    if probe:
                        result["column"] = probe_column(rcon, *probe)
                    if start:
                        result.update(moved_start(rcon, *start))
                    if farman:
                        result.update(farman_test.run(rcon, mc, port, workdir, log_path))
                    if forceload:
                        # Generate a patch of the Far Lands so region_slice.py has chunks to read.
                        # forceload generates them in the background, so give it time and then flush
                        # to disk - unsaved chunks are not in the region files yet.
                        x0, z0, x1, z1 = forceload
                        result["forceload"] = rcon.command(f"forceload add {x0} {z0} {x1} {z1}")
                        time.sleep(settle)
                        result["save"] = rcon.command("save-all flush")
                        time.sleep(5)
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
    # Any reply counts as an answer, "Unknown or incomplete command" included, so check it is ours.
    result["command_ok"] = "Farlands Reforged" in result["farlands"]
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
    ap.add_argument("--forceload", nargs=4, type=int, metavar=("X1", "Z1", "X2", "Z2"),
                    help="generate this block region, so its chunks land in the region files")
    ap.add_argument("--settle", type=float, default=90,
                    help="seconds to let forceload finish generating before saving")
    ap.add_argument("--probe", nargs=2, type=int, metavar=("X", "Z"),
                    help="read this terrain column block by block (see probe_column)")
    ap.add_argument("--start", nargs=2, type=int, metavar=("X", "Z"),
                    help="after the probe, move where the Far Lands start (/farlands set x|z) and probe just past it too")
    ap.add_argument("--farman", action="store_true",
                    help="put a headless player in the Far Lands and make FarMan appear (see farman_test.py)")
    ap.add_argument("--json", action="store_true", help="print the result as one JSON line")
    args = ap.parse_args()

    workdir = args.workdir or Path(f"/tmp/farlands-test-{args.mc}")
    for port in (args.port, args.rcon_port):
        if not free_port(port):
            sys.exit(f"port {port} is already in use")

    result = run_test(args.mc, args.jar, workdir, args.cache, args.port, args.rcon_port,
                      args.password, args.boot_timeout, args.corrupt_advancement,
                      args.forceload, args.settle, args.probe, args.farman, args.start)

    if args.json:
        print(json.dumps(result))
    else:
        log(f"  booted      : {result['booted']}")
        log(f"  /farlands   : {result['farlands'][:120].strip() or '(no answer)'}")
        log(f"  pack listed : {result['pack_listed']}")
        if "column" in result:
            log(f"  column      : {summarize_column(result['column'])}")
        if "farman" in result:
            failing = [name for name, ok in result["farman_checks"].items() if not ok]
            log(f"  farman      : {result['farman']}" + (f"  (failing: {', '.join(failing)})" if failing else ""))
            for note in result["farman_notes"][:8]:
                log(f"    {note}")
        if args.corrupt_advancement:
            log(f"  parse error : {result['parse_error']}  (must be True - proves the pack is read)")
        for error in result["errors"][:5]:
            log(f"  ERROR       : {error}")

    ok = result["booted"] and result["command_ok"] and not result["errors"]
    ok = ok and (result["parse_error"] if args.corrupt_advancement else result["pack_listed"])
    ok = ok and (not args.farman or result.get("farman") != "failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
