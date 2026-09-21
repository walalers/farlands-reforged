# Farlands Reforged — CurseForge publish pack

Everything here is paste-ready. The `jars/` folder holds the 48 files you upload.
`logo.png` is your 400×400 project logo. Work top-to-bottom and you're live.

---

## 1) Create the project

- CurseForge Author dashboard → **Create Project** → Minecraft → **Mods**
- **Name:** `Farlands Reforged`
- **Logo:** upload `logo.png` (in this folder)
- **License:** MIT
- **Categories:** World Gen (primary); optionally Map and Information (for the `/farlands` command)

---

## 2) Summary (paste into the "Summary" field)

```
The real Beta Far Lands are back: towering walls, floating sheets and flooded tunnels at ±12,550,821. Fabric, NeoForge and Forge.
```

---

## 3) Description (paste into the description editor, Markdown mode)

# Farlands Reforged

Remember the Far Lands? Walk about 12.5 million blocks from spawn in an old Beta world and the terrain just fell apart. Stone walls as tall as the world, huge floating sheets stacked on top of each other, dark tunnels that went on forever. Beta 1.8 fixed it, and they've been gone ever since.

This mod puts them back. It isn't a "glitchy terrain" imitation. It uses the same overflowing noise Beta used, at the same coordinates, with the same grassy ledges and flooded caves.

There are no new blocks and you don't need a resource pack. The rest of your world generates like normal, and you won't notice anything until you get really, really far out.

## What's in it

- The Edge Far Lands along X and Z, and the Corner Far Lands where they meet, starting at ±12,550,821. Keep going to ±25,101,648 and everything breaks a second time.
- Grass and trees on top, grass and dirt on every ledge, and water filling everything up to sea level, just like Beta.
- Mountains and caves stay normal until you reach the right distance. Nothing starts glitching early.
- Modern noodle caves don't cut through the Far Lands, so the walls stay solid. Regular caves are still there.
- Arriving doesn't freeze your server. All that water doesn't turn into a flood of block updates.
- `/farlands` tells you where the Far Lands start and how far away you are. Operators also get `/farlands set <threshold>` and `/farlands reset`.
- A hidden advancement, "...where am I?", for making it out there.
- Config options to turn off the terrain or the advancement.

## Getting there

You could walk. It's only 12.5 million blocks. Or make a new world and run:

```
/tp @s 12550821 120 0
```

Then try the other axis, the negative side, and a corner:

```
/tp @s 0 120 12550821
/tp @s -12550821 120 0
/tp @s 12550821 120 12550821
```

Only chunks that haven't been generated yet turn into Far Lands. Places you've already explored won't change.

## How it works

In Beta, the terrain noise multiplied your block coordinate by 171.103. Somewhere past 12.5 million blocks that number got too big for an integer, the math broke, and out came the Far Lands. Modern Minecraft still has that exact noise. It just wraps the coordinates so they never get that big.

Removing the wrap sounds like it should be enough, but it isn't. On its own, modern world generation treats the broken values as "deep underground", and you get a solid block of stone from bedrock to the build limit. So the mod also changes how terrain density is handled, how grass and dirt get placed, and how water fills in, and it keeps noodle caves out of the Far Lands. That's what makes it look like Beta again.

## Versions

| Minecraft | Fabric | NeoForge | Forge |
|-----------|:------:|:--------:|:-----:|
| 26.3      | ✅ | | |
| 26.2      | ✅ | ✅ | ✅ |
| 26.1.2    | ✅ | ✅ | ✅ |
| 26.1.1    | ✅ | ✅ | ✅ |
| 26.1      | ✅ | ✅ | ✅ |
| 1.21.11   | ✅ | ✅ | ✅ |
| 1.21 … 1.21.10 | ✅ | ✅ | ✅* |

\* Forge never shipped a 1.21.2 build, so there is no 1.21.2 Forge jar. NeoForge has no stable 26.3 yet,
so there is no NeoForge 26.3 jar either.

The 26.x builds need **Java 25**; the 1.21 builds need **Java 21**. On Fabric, Fabric Loader is all you
need. No Fabric API.

Take the jar that names **your exact Minecraft version** — these are not interchangeable. A jar built
against 1.21.8 will not behave correctly on 1.21.5.

## Config

Fabric and NeoForge: `config/farlandsreforged-common.toml`
Forge: `config/farlandsreforged.properties`

```toml
enableFarlandsTerrain = true
enableWhereAmIAdvancement = true
farlandsStartCoordinate = 12550821
```

`farlandsStartCoordinate` only moves the `/farlands` readout and the advancement. The terrain always breaks at the real spot, same as in Beta.

## Credits

Big thanks to AdyTech99, whose MIT-licensed **Farlands Reborn** had the original idea of undoing the noise wrap.

MIT licensed. Made by Shigeo. The source is on [GitHub](https://github.com/walalers/farlands-reforged).

---

## 4) Upload the files

`tools/upload_curseforge.py` does this over the API rather than by hand — 48 files is too many to click
through, and each one needs three tags set correctly:

```bash
python3 tools/upload_curseforge.py build-release --version 0.4.0 \
    --changelog PUBLISH/GITHUB_RELEASE_NOTES.md          # dry run, uploads nothing
python3 tools/upload_curseforge.py ... --go              # actually upload
```

It reads the token from `~/.curseforge-token`, works out each jar's Minecraft version and loader from its
filename, resolves those to CurseForge's numeric game-version ids, and refuses to upload anything at all if
a single jar does not resolve. It builds the multipart request itself instead of shelling out to `curl`,
because `curl -F` truncates a value at the first `;` and the metadata is JSON full of them.

Every file gets **Release type = Release**, no required dependencies (do **not** add Fabric API), and three
tags: its Minecraft version, its modloader, and its Java version — **Java 21** for the 1.21 family, **Java
25** for 26.x.

The release is 48 files: Minecraft 1.21 … 1.21.11 on Fabric (12), NeoForge (12) and Forge (11 — Forge never
shipped a 1.21.2), plus 26.1 / 26.1.1 / 26.1.2 / 26.2 on all three loaders and 26.3 on Fabric. There is no
NeoForge 26.3 jar: NeoForge has no stable 26.3 yet.

---

## 5) Changelog (sent with every file by the upload script)

```
Farlands Reforged 0.4.0

- Minecraft 1.21 - 1.21.11 on Fabric, NeoForge and Forge. Same Far Lands code as the 26.x builds;
  these need Java 21.
- The "...where am I?" advancement now works on Fabric. It never had: Fabric Loader does not expose a
  mod's data directory as a data pack (that is Fabric API, which this mod deliberately does not need),
  so the advancement JSON was never read and the detector quietly did nothing. Fabric builds now
  register a built-in pack in code - still no Fabric API dependency. Forge and NeoForge were unaffected.
- Terrain generation is unchanged: a 0.3.1 world generates identically under 0.4.0.
```


## 6) Before you flip it public

- **Distribution:** leave third-party distribution **enabled** if you want launchers/modpacks to use it.
- **Moderation:** your first project + files go through a quick manual CurseForge review before they appear publicly.
- **Smoke test:** every Fabric jar in this release was booted on a real Fabric server of its own Minecraft
  version, and checked for three things: no mixin errors, `/farlands` answers, and `/datapack list` names
  `farlandsreforged` — the last of which is the bug 0.4.0 fixes. `tools/server_test.py` does this.
- **Checksums:** `SHA256SUMS.txt` (in `farlands-reforged-releases`) lists hashes for every jar if you want to
  post them for verification.
