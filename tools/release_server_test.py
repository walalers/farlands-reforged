#!/usr/bin/env python3
"""Boot every jar in a release on a real server, and check each one works.

    release_server_test.py PUBLISH/jars --version 0.4.0
    release_server_test.py PUBLISH/jars --version 0.4.0 --only neoforge:26.2 fabric:1.21

This drives server_test.py (Fabric) and modded_server_test.py (Forge, NeoForge) across the whole
release, in three lanes - one per loader - running side by side. Each server is checked for:

  - no mixin error in the log, and `/farlands` answering with the mod's own text;
  - the mod's data pack listed by `/datapack list`;
  - one Far Lands column, read block by block (`--probe`), which must be identical on every jar;
  - on NeoForge, a second boot with the advancement JSON corrupted, which must log a parse error.
    NeoForge lists every mod's data under one `mod_data` pack, so the listing alone proves nothing.

All 48 jars of 0.4.0 took about 2.5 hours. Results go to a JSON-lines file as they arrive, and a
summary with a pass/fail per jar is printed at the end; the exit code is non-zero if anything failed.

Things this does because they went wrong once:
  - Every vanilla server jar is downloaded first, one at a time and checksum-verified, and
    modded_server_test.py copies it into each install before its installer runs. Concurrent installers
    downloading it have corrupted it, and two lanes fetching one jar at once would share a `.part` file.
  - Each modded install is deleted after its test, keeping only the logs. They are a few hundred MB
    each, and 31 of them do not fit on this disk at once.
  - A download that fails on a network error is retried rather than failing the jar - a Wi-Fi drop
    mid-run otherwise reads as three broken NeoForge builds.
"""

import argparse
import json
import shutil
import sys
import threading
import time
import traceback
import urllib.error
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import modded_server_test  # noqa: E402
import server_test  # noqa: E402

# The Far Lands column every jar is probed at. On seed 1234 it holds solid layers up to y=222;
# vanilla has plain ocean there, so a worldgen mixin that silently failed to apply cannot pass.
PROBE = (12550850, 0)

FABRIC = ["1.20", "1.20.1", "1.20.2", "1.20.3", "1.20.4", "1.20.5", "1.20.6", "1.21", "1.21.1", "1.21.2",
          "1.21.3", "1.21.4", "1.21.5", "1.21.6", "1.21.7", "1.21.8", "1.21.9", "1.21.10", "1.21.11", "26.1",
          "26.1.1", "26.1.2", "26.2", "26.3"]

# Loader versions to test against. Mostly the ones build_release.sh builds with; every 1.20.x entry,
# and Forge 1.21 (51.0.23), is the declared minimum - the oldest build a jar promises to run on is where
# a missing method or an older bundled Mixin shows up. NeoForge 26.x uses the newest build of each line.
# None means "read it from the 1.21.11 project's gradle.properties", which pins its own.
FORGE = [("1.20", "46.0.1"), ("1.20.1", "47.0.0"), ("1.20.2", "48.0.0"), ("1.20.3", "49.0.1"),
         ("1.20.4", "49.0.3"), ("1.20.6", "50.0.0"), ("1.21", "51.0.23"), ("1.21.1", "52.1.16"),
         ("1.21.3", "53.1.12"), ("1.21.4", "54.1.18"), ("1.21.5", "55.1.13"), ("1.21.6", "56.0.0"),
         ("1.21.7", "57.0.0"), ("1.21.8", "58.1.22"), ("1.21.9", "59.0.5"), ("1.21.10", "60.1.15"),
         ("1.21.11", None), ("26.1", "62.0.9"), ("26.1.1", "63.0.2"), ("26.1.2", "64.1.3"),
         ("26.2", "65.0.0")]
NEOFORGE = [("1.20.2", "20.2.86"), ("1.20.3", "20.3.1-beta"), ("1.20.4", "20.4.0-beta"),
            ("1.20.5", "20.5.14-beta"), ("1.20.6", "20.6.141"), ("1.21", "21.0.167"), ("1.21.1", "21.1.251"),
            ("1.21.2", "21.2.1-beta"), ("1.21.3", "21.3.97"), ("1.21.4", "21.4.157"), ("1.21.5", "21.5.98"),
            ("1.21.6", "21.6.20-beta"), ("1.21.7", "21.7.25-beta"), ("1.21.8", "21.8.54"),
            ("1.21.9", "21.9.16-beta"), ("1.21.10", "21.10.64"), ("1.21.11", None),
            ("26.1", "26.1.0.19-beta"), ("26.1.1", "26.1.1.15-beta"), ("26.1.2", "26.1.2.109"),
            ("26.2", "26.2.0.88")]

PORTS = {"fabric": 25611, "forge": 25621, "neoforge": 25631}  # RCON is each plus 100
NETWORK_RETRIES = 3

lock = threading.Lock()


def log(message):
    with lock:
        print(message, flush=True)


def gradle_prop(project, key):
    for line in (REPO / project / "gradle.properties").read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip()
    raise KeyError(f"{key} not in {project}/gradle.properties")


def passed(result):
    ok = result["booted"] and result.get("command_ok") and not result["errors"]
    return bool(ok and (result["parse_error"] if result["mode"] == "corrupt" else result["pack_listed"]))


def with_network_retries(run):
    """Call run(), retrying when a download fails on a network error rather than on the mod."""
    for attempt in range(1, NETWORK_RETRIES + 1):
        try:
            return run()
        except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
            if attempt == NETWORK_RETRIES:
                raise
            log(f"    network error ({exc}); retrying in 60s")
            time.sleep(60)


class Run:
    def __init__(self, jars, version, work, cache, results):
        self.jars, self.version, self.work, self.cache, self.results = jars, version, work, cache, results

    def record(self, result):
        with lock:
            with open(self.results, "a") as f:
                f.write(json.dumps(result) + "\n")
            column = result.get("column")
            print(f"[{result['loader']:8} {result['mc']:8} {result['mode']:7}] "
                  f"{'PASS' if passed(result) else 'FAIL'}"
                  + (f"  column: {server_test.summarize_column(column)[:70]}" if column else "")
                  + ("" if passed(result) else f"  {(result['errors'] or ['(no error text)'])[0][-200:]}"),
                  flush=True)

    def keep_logs(self, workdir, name):
        keep = self.work / "logs" / name
        keep.mkdir(parents=True, exist_ok=True)
        for server_log in workdir.glob("server*.log"):
            shutil.copy(server_log, keep / server_log.name)
        shutil.rmtree(workdir, ignore_errors=True)

    def jar(self, mc, loader):
        return self.jars / f"farlandsreforged-{self.version}+mc{mc}-{loader}.jar"

    def fabric_lane(self, versions):
        port = PORTS["fabric"]
        for mc in versions:
            workdir = self.work / f"fabric-{mc}"
            try:
                result = with_network_retries(lambda: server_test.run_test(
                    mc, self.jar(mc, "fabric"), workdir, self.cache, port, port + 100, "farlands",
                    300, False, probe=PROBE))
            except Exception:
                result = {"mc": mc, "booted": False, "pack_listed": False, "parse_error": False,
                          "errors": [traceback.format_exc()[-600:]]}
            result.update(loader="fabric", mode="normal")
            self.record(result)
            self.keep_logs(workdir, f"fabric-{mc}")

    def modded_lane(self, loader, versions):
        port = PORTS[loader]
        for mc, loader_version in versions:
            if loader_version is None:
                loader_version = gradle_prop(f"farlands-reforged-{loader}-1.21.11",
                                             f"{loader}_version")
            workdir = self.work / f"{loader}-{mc}"

            for mode in (["normal", "corrupt"] if loader == "neoforge" else ["normal"]):
                try:
                    result = with_network_retries(lambda: modded_server_test.run_test(
                        loader, mc, loader_version, self.jar(mc, loader), workdir, self.cache, port,
                        port + 100, "farlands", 900, mode == "corrupt",
                        probe=PROBE if mode == "normal" else None))
                except Exception:
                    result = {"mc": mc, "loader_version": loader_version, "booted": False,
                              "pack_listed": False, "parse_error": False,
                              "errors": [traceback.format_exc()[-600:]]}
                result.update(loader=loader, mode=mode)
                self.record(result)
                if (workdir / "server.log").exists():
                    (workdir / "server.log").rename(workdir / f"server-{mode}.log")
                if not result["booted"]:
                    break
            self.keep_logs(workdir, f"{loader}-{mc}")


def summarize(results_path, expected):
    latest = {}
    for line in results_path.read_text().splitlines():
        if line.strip():
            result = json.loads(line)
            latest[(result["loader"], result["mc"], result["mode"])] = result

    failed = [key for key, result in latest.items() if not passed(result)]
    missing = [key for key in expected if (*key, "normal") not in latest]
    columns = {key[:2]: r["column"] for key, r in latest.items() if r.get("column")}
    variants = {}
    for key, column in columns.items():
        variants.setdefault(column, []).append(key)

    print(f"\n{len(latest)} runs across {len({k[:2] for k in latest})} jars")
    for loader, mc, mode in failed:
        print(f"  FAIL     {loader} {mc} ({mode})")
    for loader, mc in missing:
        print(f"  MISSING  {loader} {mc}")
    if len(variants) == 1:
        print(f"  terrain: all {len(columns)} Far Lands columns identical")
    else:
        # A few seagrass-level differences between Minecraft versions would show up here too; read the
        # columns in the results file before calling it a regression.
        print(f"  terrain: {len(variants)} different columns")
        for column, keys in variants.items():
            print(f"    {server_test.summarize_column(column)[:90]}")
            print(f"      <- {', '.join(f'{l} {m}' for l, m in sorted(keys))}")
    return not failed and not missing and len(variants) <= 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("jars", type=Path, help="directory holding the release jars")
    ap.add_argument("--version", required=True, help="mod version in the jar names, e.g. 0.4.0")
    ap.add_argument("--only", nargs="+", metavar="LOADER[:MC]",
                    help="test only these, e.g. neoforge  or  forge:1.21 fabric:26.2")
    ap.add_argument("--workdir", type=Path, default=Path("/tmp/farlands-release-test"))
    ap.add_argument("--cache", type=Path, default=Path.home() / ".cache/farlands-server-test")
    ap.add_argument("--results", type=Path,
                    help="JSON-lines results file (default: <workdir>/results.jsonl)")
    args = ap.parse_args()

    def wanted(loader, mc):
        return not args.only or any(o == loader or o == f"{loader}:{mc}" for o in args.only)

    fabric = [mc for mc in FABRIC if wanted("fabric", mc)]
    forge = [(mc, v) for mc, v in FORGE if wanted("forge", mc)]
    neoforge = [(mc, v) for mc, v in NEOFORGE if wanted("neoforge", mc)]
    expected = ([("fabric", mc) for mc in fabric] + [("forge", mc) for mc, _ in forge]
                + [("neoforge", mc) for mc, _ in neoforge])

    missing_jars = [f"{l} {mc}" for l, mc in expected
                    if not (args.jars / f"farlandsreforged-{args.version}+mc{mc}-{l}.jar").exists()]
    if missing_jars:
        sys.exit(f"no jar for: {', '.join(missing_jars)}")

    args.workdir.mkdir(parents=True, exist_ok=True)
    results = args.results or args.workdir / "results.jsonl"
    results.unlink(missing_ok=True)
    run = Run(args.jars.resolve(), args.version, args.workdir, args.cache, results)

    for mc in sorted({mc for _, mc in expected}):
        with_network_retries(lambda: server_test.vanilla_server_jar(mc, args.cache))
    log(f"testing {len(expected)} jars; results in {results}")

    lanes = [threading.Thread(target=run.fabric_lane, args=(fabric,)),
             threading.Thread(target=run.modded_lane, args=("forge", forge)),
             threading.Thread(target=run.modded_lane, args=("neoforge", neoforge))]
    for lane in lanes:
        lane.start()
    for lane in lanes:
        lane.join()

    return 0 if summarize(results, expected) else 1


if __name__ == "__main__":
    sys.exit(main())
