#!/usr/bin/env python3
"""Put a headless player in the Far Lands of a running test server and make FarMan appear to it.

Called by server_test.py and modded_server_test.py with `--farman`, once the server is up and the Far
Lands column has been probed. FarMan needs a real player - he is driven from the player tick - so this
starts tools/farman_bot.cjs (mineflayer) against the server and drives it over RCON:

  1. `/farlands farman on`, and the config file on disk says so (the toggle is saved, not just set);
  2. the bot is teleported onto the Far Lands and `/farlands farman summon` is run as it: an armor
     stand tagged as FarMan must exist, carrying his profile (name and skin) and the dyed armor. This
     is the item-building code, which is different in every API era;
  3. `/farlands farman scare` puts him behind the bot, and the bot is turned to face him. The jump scare
     happens in the player tick, so the bot getting Blindness (and Darkness, 1.19+) proves the tick
     hook runs, and he must be gone afterwards;
  4. with nothing else going on, "FarMan joined the game" must reach the bot's chat within the first
     event window (60 - 120 s in the Far Lands): the unprompted haunting works;
  5. `/farlands farman off`, saved to disk too.

The mineflayer build decides which Minecraft versions the bot can play; see BOT_VERSION. For newer ones
a real client stands in (CLIENT_PROJECT): Loom's runClient from that version's Fabric project, joining with
--quickPlayMultiplayer. It opens a Minecraft window, and is turned by the server (a real client, unlike
mineflayer, keeps the rotation a teleport gives it). The 26.x client does not log chat, so with it step 4
cannot be seen and is reported as a note rather than a check; the scare in step 3 still proves the tick.
"""

import glob
import json
import os
import queue
import re
import signal
import subprocess
import threading
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
NODE_PREFIX = Path.home() / ".cache/farlands-server-test/node"
BOT = "FarBot"
TAG = "farlandsreforged_farman"
FARMAN = f"@e[type=armor_stand,tag={TAG},limit=1]"
# Where the bot stands: the probed Far Lands column, facing +X, deeper into the Far Lands.
SPOT = (12550850, 0)

# mineflayer speaks one protocol per entry in minecraft-data; these versions share a protocol with the
# one they map to. Anything not listed and not supported is reported as skipped, not failed.
BOT_VERSION = {"1.19.1": "1.19.2", "1.21.2": "1.21.3", "1.21.7": "1.21.8", "26.1.1": "26.1", "26.1.2": "26.1"}

# Versions mineflayer cannot play, and the Fabric project whose dev client joins instead.
CLIENT_PROJECT = {"26.2": "farlands-reforged-fabric-26.2", "26.3": "farlands-reforged-fabric-26.3"}

TICK_ERRORS = [r"NoSuchMethodError", r"NoSuchFieldError", r"AbstractMethodError", r"IncompatibleClassChangeError",
               r"Exception ticking", r"Encountered an unexpected exception", r"ClassCastException"]


def supported_versions():
    out = subprocess.run(["node", "-e", "console.log(require('minecraft-data').supportedVersions.pc.join(' '))"],
                         env=_node_env(), capture_output=True, text=True)
    return set(out.stdout.split())


def _node_env():
    env = dict(os.environ)
    env["NODE_PATH"] = str(NODE_PREFIX / "node_modules")
    return env


class Bot:
    spawn_timeout = 120
    sees_chat = True

    def __init__(self, port, version):
        self.events = queue.Queue()
        self.seen = []
        self.proc = subprocess.Popen(["node", str(TOOLS / "farman_bot.cjs"), "127.0.0.1", str(port), version, BOT],
                                     env=_node_env(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True)
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                event = {"event": "stderr", "text": line.rstrip()[:300]}
            self.events.put(event)

    def wait_for(self, predicate, timeout):
        """The first event, from now on or already seen, that matches."""
        for event in self.seen:
            if predicate(event):
                return event
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                event = self.events.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                break
            self.seen.append(event)
            if predicate(event):
                return event
            if event["event"] in ("kicked", "end"):
                break
        return None

    def send(self, command):
        self.proc.stdin.write(json.dumps(command) + "\n")
        self.proc.stdin.flush()

    def drain(self):
        while True:
            try:
                self.seen.append(self.events.get_nowait())
            except queue.Empty:
                return

    def stop(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


class RealClient(Bot):
    """A real client in place of the bot, with the same events. Only its arrival is observed, from the server log."""
    spawn_timeout = 900  # the first launch of a version downloads its assets
    sees_chat = False
    # One client per project at a time: two lanes testing 26.2 on different loaders would share run/.
    locks = {name: threading.Lock() for name in CLIENT_PROJECT.values()}

    def __init__(self, project, port, rcon, server_log):
        self.server_log = server_log
        self.lock = self.locks[project]
        self.lock.acquire()
        self.events = queue.Queue()
        self.seen = []
        self.rcon = rcon
        run_dir = REPO / project / "run"
        (run_dir / "logs").mkdir(parents=True, exist_ok=True)
        options = run_dir / "options.txt"
        # Without this a fresh client stops on the accessibility onboarding screen and never joins.
        text = options.read_text() if options.exists() else ""
        if "onboardAccessibility:false" not in text:
            options.write_text(re.sub(r"(?m)^onboardAccessibility:.*\n?", "", text) + "onboardAccessibility:false\n")
        gradle = sorted(glob.glob(str(Path.home() / ".gradle/wrapper/dists/gradle-9.7.1-bin/*/gradle-9.7.1/bin/gradle")))[0]
        self.output = open(run_dir / "logs" / "farman-runClient.out", "w")
        self.proc = subprocess.Popen(
            [gradle, "--no-daemon", "--console=plain", "runClient",
             f"--args=--quickPlayMultiplayer 127.0.0.1:{port} --username {BOT}"],
            cwd=REPO / project, stdout=self.output, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            start_new_session=True)
        threading.Thread(target=self._tail, daemon=True).start()

    def _tail(self):
        """The client logs no chat, so its arrival is read from the server's log instead."""
        with open(self.server_log, errors="replace") as log:
            log.seek(0, os.SEEK_END)
            while True:
                line = log.readline()
                if not line:
                    if self.proc.poll() is not None:
                        self.events.put({"event": "end", "reason": f"client exited with {self.proc.returncode}"})
                        return
                    time.sleep(0.5)
                    continue
                if f"{BOT} joined the game" in line:
                    self.events.put({"event": "spawn"})
                elif f"{BOT} lost connection" in line:
                    self.events.put({"event": "kicked", "reason": line.strip()[-200:]})

    def send(self, command):
        # `tp ... facing <x y z>` aims from the player's feet, not its eyes, so the point the bot looks at
        # would tilt this client's gaze over his head. Facing him by entity keeps it level, on his face.
        if "lookAt" in command:
            self.rcon.command(f"execute as {BOT} at @s run tp @s ~ ~ ~ facing entity {FARMAN} eyes")
            self.events.put({"event": "looked"})

    def stop(self):
        try:
            os.killpg(self.proc.pid, signal.SIGKILL)  # Gradle and the game JVM both; a TERM is ignored
        except ProcessLookupError:
            pass
        self.proc.wait(timeout=60)
        self.output.close()
        self.lock.release()


def config_says(workdir, enabled):
    """The FarMan toggle as written to disk: a .properties file on Fabric and Forge, TOML on NeoForge."""
    want = "true" if enabled else "false"
    for path in (workdir / "config").glob("farlandsreforged*"):
        text = path.read_text(errors="replace")
        if re.search(rf"^\s*enableFarMan\s*[=:]\s*{want}\s*$", text, re.M):
            return path.name
    return None


def position(rcon, selector):
    """An entity's position, from `/data get entity <selector> Pos`, or None."""
    reply = rcon.command(f"data get entity {selector} Pos")
    numbers = re.findall(r"(-?[0-9.]+(?:E-?[0-9]+)?)d", reply)
    return tuple(float(n) for n in numbers[:3]) if len(numbers) >= 3 else None


BLINDNESS = r"blindness|\bId: 15b?(?!\d)"
DARKNESS = r"darkness|\bId: 33b?(?!\d)"


def effects(rcon):
    """The bot's active effects as saved data. The key was ActiveEffects before 1.20.5, active_effects after."""
    return rcon.command(f"data get entity {BOT} active_effects") + rcon.command(f"data get entity {BOT} ActiveEffects")


def run(rcon, mc, port, workdir, log_path, join_timeout=180):
    result = {"farman": "failed", "farman_checks": {}, "farman_notes": []}
    version = BOT_VERSION.get(mc, mc)
    if version not in supported_versions() and mc not in CLIENT_PROJECT:
        result["farman"] = f"skipped: nothing can play {mc}"
        return result
    checks = result["farman_checks"]
    checks["off_by_default"] = "is off" in rcon.command("farlands farman")
    checks["turned_on"] = "is on" in rcon.command("farlands farman on")
    checks["on_saved"] = bool(config_says(workdir, True))
    try:
        player = (Bot(port, version) if version in supported_versions()
                  else RealClient(CLIENT_PROJECT[mc], port, rcon, log_path))
        result["farman_player"] = type(player).__name__
        _haunt(rcon, mc, player, result, join_timeout)
    finally:
        # Even after a failure: the world and its config are kept if the test is run again.
        checks["turned_off"] = "is off" in rcon.command("farlands farman off")
    checks["off_saved"] = bool(config_says(workdir, False))

    text = log_path.read_text(errors="replace")
    tick_errors = [line.strip()[:200] for pattern in TICK_ERRORS for line in re.findall(rf".*{pattern}.*", text)]
    checks["no_tick_errors"] = not tick_errors
    result["farman_notes"].extend(tick_errors[:5])
    result["farman"] = "passed" if all(checks.values()) else "failed"
    return result


def _retry(rcon, command, attempts=12):
    """Run a FarMan command as the bot, turning it a little between attempts if he found nowhere to stand."""
    reply = ""
    for attempt in range(attempts):
        # Silent when it works, and Forge then sends no reply at all: fence it.
        reply = rcon.command(f"execute as {BOT} run {command}", fence="list")
        if "nowhere" not in reply:
            break
        rcon.command(f"execute as {BOT} at @s run tp @s ~ ~ ~ {-90 + (attempt % 5 - 2) * 25} 0")
        time.sleep(1)
    return reply


def _haunt(rcon, mc, bot, result, join_timeout):
    checks = result["farman_checks"]
    notes = result["farman_notes"]
    try:
        if not bot.wait_for(lambda e: e["event"] == "spawn", bot.spawn_timeout):
            checks["bot_spawned"] = False
            notes.append("bot never spawned: " + json.dumps(bot.seen[-5:])[:600])
            return
        rcon.command(f"gamemode creative {BOT}")
        x, z = SPOT
        rcon.command(f"tp {BOT} {x}.5 300 {z}.5 -90 0")
        entered = time.time()
        time.sleep(20)  # fall onto the Far Lands and let the chunks around arrive

        # 2. a sighting, and what he is made of
        summoned = _retry(rcon, "farlands farman summon")
        data = rcon.command(f"data get entity {FARMAN}")
        notes.append("summon: " + (summoned.strip() or "(no reply)")[:200])
        notes.append("figure: " + data[:400])
        checks["summon_spawned"] = "has the following entity data" in data
        checks["has_profile"] = "FarMan" in data and "textures" in data
        checks["black_armor"] = bool(re.search(r"dyed_color|color: 0\b", data))
        checks["is_marker"] = "Marker: 1b" in data

        # 3. behind the player, then the player turns round - its own head, as a real player would
        _retry(rcon, "farlands farman scare")
        figure = position(rcon, FARMAN)
        checks["scare_spawned"] = figure is not None
        # The blindness lasts 1.5 s (3 s on 1.18.2), so poll from the moment the head turns rather than
        # look once afterwards. Before 1.20.2 effects are saved by number (15 blindness, 33 darkness) - a byte
        # on 1.18.2, an int on 1.19 - 1.20.1 - and Forge adds a "forge:id" string beside it.
        seen = ""
        if figure:
            bot.send({"lookAt": [figure[0], figure[1] + 1.0, figure[2]]})
            deadline = time.time() + 6
            while time.time() < deadline:
                seen += effects(rcon)
                if re.search(BLINDNESS, seen, re.I):
                    break
                time.sleep(0.2)
            seen += effects(rcon)
        checks["blinded"] = bool(re.search(BLINDNESS, seen, re.I))
        if not mc.startswith("1.18"):
            checks["darkness"] = bool(re.search(DARKNESS, seen, re.I))
        time.sleep(1)
        checks["vanished_after_scare"] = "failed" in rcon.command(f"execute if entity {FARMAN}").lower()

        # 4. the unprompted haunting: the first event is always the join message
        if not bot.sees_chat:
            notes.append("join message not checked: this client does not log chat")
            return
        joined = bot.wait_for(lambda e: e["event"] == "message" and "FarMan joined the game" in e.get("text", ""),
                              max(5, join_timeout - (time.time() - entered)))
        checks["joined_message"] = joined is not None
        notes.append(f"join message after {time.time() - entered:.0f}s in the Far Lands" if joined
                     else f"no join message within {join_timeout}s")
    finally:
        bot.drain()
        bot.stop()
        messages = [e.get("text", "") for e in bot.seen if e["event"] == "message"]
        if messages:
            notes.append("bot chat: " + " | ".join(messages[-6:])[:400])
        trouble = [e for e in bot.seen if e["event"] in ("kicked", "error")]
        if trouble:
            notes.append("bot trouble: " + json.dumps(trouble[:3])[:400])
