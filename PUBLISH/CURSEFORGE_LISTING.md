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
Brings back the Beta 1.7.3 Far Lands at ±12,550,821: stretched walls, stacked sheets and flooded tunnels. Fabric, NeoForge and Forge.
```

---

## 3) Description (paste into the description editor, Markdown mode)

# Farlands Reforged

Walk far enough in an old Beta world and the terrain broke. At 12,550,821 blocks out, the numbers behind world generation overflowed and you got the Far Lands: giant walls, floating sheets of stone stacked into the sky, and tunnels running for thousands of blocks. Mojang patched it out long ago.

This mod brings the Far Lands back in modern Minecraft, and makes them look like the Beta ones did, not a random glitch effect.

No new blocks and no resource pack. Everything before the Far Lands generates like normal Minecraft.

## What you get

- **The real shapes.** You get the Edge Far Lands on X and Z and the Corner Far Lands where they meet. They start at ±12,550,821, and the terrain breaks down a second time at ±25,101,648.
- **Beta-style dressing.** Grass and trees grow on top, every ledge has grass and dirt, and the tunnels are flooded up to sea level.
- **Nothing breaks early.** Mountains and caves stay normal until you reach the classic distance.
- **No modern noodle caves inside the Far Lands**, so the walls and sheets stay solid. Regular caves still generate.
- **No lag spike when you arrive.** The flooded terrain doesn't pile up tens of thousands of water and lava updates.
- **`/farlands` command.** It shows where the Far Lands start and how far away you are. `/farlands set <threshold>` and `/farlands reset` need operator permission.
- **"...where am I?" advancement** for reaching the edge of sane terrain.
- **Config** to turn the terrain or the advancement off.

## Getting there

Make a new world, then:

```
/tp @s 12550821 120 0
```

Try the other directions and a corner too:

```
/tp @s 0 120 12550821
/tp @s -12550821 120 0
/tp @s 12550821 120 12550821
```

The Far Lands only appear in chunks that haven't been generated yet. Chunks you already explored stay as they are.

## How it works

Beta's terrain noise multiplied block coordinates by 171.103. Around 12.5 million blocks that value goes past the integer limit, the math stops making sense, and the terrain goes wild. Modern Minecraft still has that same noise but clamps its inputs.

Farlands Reforged removes the clamp on that one noise and leaves every other noise alone. Then it adjusts modern world generation (density routing, surface rules, aquifers and noodle caves) so it handles the broken noise the way Beta's generator did. If you only remove the clamp, you get a solid slab of stone from bedrock to the build limit. Most "Far Lands" mods stop there.

## Versions

| Minecraft | Fabric | NeoForge | Forge |
|-----------|:------:|:--------:|:-----:|
| 26.3      | ✅ | | |
| 26.2      | ✅ | ✅ | ✅ |
| 26.1.2    | ✅ | ✅ | ✅ |
| 26.1.1    | ✅ | ✅ | ✅ |
| 26.1      | ✅ | ✅ | ✅ |

Requires **Java 25**. On Fabric you only need Fabric Loader. **Fabric API is not required.**

## Config

Fabric and NeoForge: `config/farlandsreforged-common.toml`
Forge: `config/farlandsreforged.properties`

```toml
enableFarlandsTerrain = true
enableWhereAmIAdvancement = true
farlandsStartCoordinate = 12550821
```

`farlandsStartCoordinate` only changes the `/farlands` readout and the advancement. The terrain always breaks where the noise overflows, same as in Beta.

## Credits

Inspired by AdyTech99's MIT-licensed **Farlands Reborn**, which first had the idea of undoing Minecraft's noise clamping.

MIT licensed. Made by Shigeo + Mob. Source on [GitHub](https://github.com/walalers/farlands-reforged).

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
