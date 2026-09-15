# GitHub Release v0.3.1 — paste-ready

To publish the release page:

1. Go to **https://github.com/walalers/farlands-reforged/releases/new**, create tag `v0.3.1` on `main`.
2. **Release title:** `Farlands Reforged 0.3.1`
3. Paste the notes below into the description.
4. Under **Attach binaries**, drag in the 12 `0.3.1` jars from `PUBLISH/jars/`.
5. **Publish release**.

---

## Farlands Reforged 0.3.1 — Authentic Far Lands

The Far Lands now look like the originals: stretched walls, stacked sheets and long tunnels on the Edge and
Corner Far Lands, starting at ±12,550,821 on X and Z. For **Fabric**, **NeoForge** and **Forge**.

### What's new in 0.3.1
- **No modern noodle caves inside the Far Lands.** The thin noodle tunnels modern Minecraft carves everywhere
  bored through the walls and sheets; Beta never had them. Beta-era caves are still there.

### Included from 0.3.0
- **Authentic shapes.** 0.2.0 only unwrapped the noise, which modern world generation turned into a solid slab
  full of vanilla caves. 0.3.0 lets the legacy terrain noise overflow the way Beta 1.7.3's did and passes the
  broken density through, so the walls, sheets and tunnels come back.
- **Beta-style dressing.** Grass and trees on top, grass and dirt on every ledge, tunnels flooded to sea level.
- **No early glitching.** Mountains stay normal until the real Far Lands (0.2.0 broke them at ±2.86 million).
- **No freeze on arrival.** The flooded Far Lands no longer queue tens of thousands of water/lava and bubble
  column updates, which stalled the server and left players looking at nothing.
- Fabric builds target Fabric Loader 0.19.5.

### Supported versions
| Minecraft | Fabric | NeoForge | Forge |
|-----------|:------:|:--------:|:-----:|
| 26.2      | ✅     | ✅       | ✅    |
| 26.1.2    | ✅     | ✅       | ✅    |
| 26.1.1    | ✅     | ✅       | ✅    |
| 26.1      | ✅     | ✅       | ✅    |

Requires **Java 25**. Fabric builds need only Fabric Loader — **Fabric API is not required**.

### Install
Download the jar matching your **Minecraft version and loader**, drop it in your `mods/` folder, and remove any
older Farlands Reforged jar. Use a **new world** (or unexplored chunks) to see the new terrain.

### Reach the Far Lands
```
/tp @s 12550800 100 0
/tp @s 0 100 12550800
/tp @s -12550800 100 0
/tp @s 12550900 100 12550900
```

*Inspired by AdyTech99's MIT-licensed Farlands Reborn. MIT licensed. By Shigeo + Mob.*
