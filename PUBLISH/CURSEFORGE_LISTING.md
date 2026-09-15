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
Restores classic Far Lands-style terrain by preserving full Perlin-noise coordinate precision. Fabric, NeoForge & Forge.
```

---

## 3) Description (paste into the description editor)

# Farlands Reforged

**Farlands Reforged** brings back the legendary **Far Lands** — the chaotic, stretched, glitched terrain that
generated at the extreme edges of old Minecraft worlds. It works by preserving full coordinate precision in
Minecraft's Perlin-noise wrapping, the exact behavior Mojang smoothed away years ago.

No new blocks, no resource pack, no fuss — just the classic terrain ghost, faithfully reforged for modern Minecraft.

## Features

- **Authentic Far Lands generation** — the stretched walls, stacked sheets and long tunnels of the Edge and
  Corner Far Lands, starting at the classic ±12,550,821 on X and Z.
- **Beta-style dressing** — grass and trees on top, grass and dirt on every ledge, tunnels flooded to sea level.
- **Stays classic by default** — normal terrain everywhere else is untouched.
- **`/farlands` command** — shows the Far Lands threshold and your distance from it, plus credits.
  `/farlands set <threshold>` and `/farlands reset` (game-master permission) tune the readout.
- **Config toggles** — turn the terrain effect and the advancement detector on/off.
- **"...where am I?" advancement** — unlocks when you reach the edge of sane terrain generation.

## How to reach the Far Lands

Head to the historical threshold and look around:

```
/tp @s 12550821 120 0
```

Try the Z-axis, negative coordinates, and the corners too:

```
/tp @s 0 120 12550821
/tp @s -12550821 120 0
/tp @s 12550821 120 12550821
```

## Config

Generated on first launch at `config/farlandsreforged-common.toml`:

```toml
enableFarlandsTerrain = true
enableWhereAmIAdvancement = true
farlandsStartCoordinate = 12550821
```

## Requirements

- **Java 25**
- **Fabric** builds: Fabric Loader only — **Fabric API is NOT required** (this mod is mixin-based).
- **NeoForge** builds: NeoForge for your Minecraft version.
- **Forge** builds: Forge for your Minecraft version (config lives in `config/farlandsreforged.properties`).

## Credits

Inspired by **AdyTech99's** MIT-licensed **Farlands Reborn**, whose core idea is to undo Mojang's far-coordinate
Perlin-noise precision wrapping. Respect to the old noise ghosts.

*MIT licensed. By Shigeo + Mob.*

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
