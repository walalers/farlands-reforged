# Farlands Reforged — CurseForge publish pack

Everything here is paste-ready. The `jars/` folder holds the 12 files you upload.
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

You'll need **Java 25**. On Fabric, Fabric Loader is all you need. No Fabric API.

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

## 4) Upload the files — settings per jar

Upload each jar from the `jars/` folder as a **separate file**. Set **Release type = Release** on all.
**Java = 25** on all. **No required dependencies on any** (do NOT add Fabric API).

| File | Game Version | Modloader |
|------|--------------|-----------|
| `farlandsreforged-0.3.1+mc26.1-fabric.jar`     | 26.1   | Fabric   |
| `farlandsreforged-0.3.1+mc26.1-neoforge.jar`   | 26.1   | NeoForge |
| `farlandsreforged-0.3.1+mc26.1.1-fabric.jar`   | 26.1.1 | Fabric   |
| `farlandsreforged-0.3.1+mc26.1.1-neoforge.jar` | 26.1.1 | NeoForge |
| `farlandsreforged-0.3.1+mc26.1.2-fabric.jar`   | 26.1.2 | Fabric   |
| `farlandsreforged-0.3.1+mc26.1.2-neoforge.jar` | 26.1.2 | NeoForge |
| `farlandsreforged-0.3.1+mc26.2-fabric.jar`     | 26.2   | Fabric   |
| `farlandsreforged-0.3.1+mc26.2-neoforge.jar`   | 26.2   | NeoForge |
| `farlandsreforged-0.3.1+mc26.3-fabric.jar`     | 26.3   | Fabric   |
| `farlandsreforged-0.3.1+mc26.1-forge.jar`     | 26.1   | Forge    |
| `farlandsreforged-0.3.1+mc26.1.1-forge.jar`   | 26.1.1 | Forge    |
| `farlandsreforged-0.3.1+mc26.1.2-forge.jar`   | 26.1.2 | Forge    |
| `farlandsreforged-0.3.1+mc26.2-forge.jar`     | 26.2   | Forge    |

> If CurseForge's version dropdown doesn't yet list 26.1 or 26.1.1, those tags aren't available to publish
> against until CurseForge adds them — upload the ones that are present and add the rest when they appear.

---

## 5) Changelog (paste into each file's changelog box)

```
Farlands Reforged 0.3.1

- No modern noodle caves inside the Far Lands: the walls and sheets are solid like Beta's.
- Includes 0.3.0: authentic Far Lands walls, sheets and tunnels; Beta-style grass, dirt and flooding;
  no early mountain glitching; no server freeze on arrival.
- Built for this Minecraft version on Fabric, NeoForge and Forge. Fabric API not required.
```

---

## 6) Before you flip it public

- **Distribution:** leave third-party distribution **enabled** if you want launchers/modpacks to use it.
- **Moderation:** your first project + files go through a quick manual CurseForge review before they appear publicly.
- **Smoke test:** the 26.2 Fabric jar is in-game tested and its worldgen verified headlessly on all four sides
  and corners. The 26.1 and 26.1.1 jars target identical Minecraft code — a 30-second world-gen check is still
  worth doing before they're public.
- **Checksums:** `SHA256SUMS.txt` (in `farlands-reforged-releases`) lists hashes for every jar if you want to
  post them for verification.
