# GitHub Release v0.2.0 — paste-ready

Tag `v0.2.0` is already pushed. To publish the release page:

1. Go to **https://github.com/walalers/farlands-reforged/releases/new?tag=v0.2.0**
2. **Release title:** `Farlands Reforged 0.2.0`
3. Paste the notes below into the description.
4. Under **Attach binaries**, drag in all 8 jars from `PUBLISH\jars\`.
5. Check **"Set as a pre-release"** (this is an alpha), then **Publish release**.

---

## Farlands Reforged 0.2.0

Restores the classic **Far Lands** — the chaotic, stretched terrain from old Minecraft — by preserving full
coordinate precision in Minecraft's Perlin-noise wrapping. For **Fabric** and **NeoForge**.

### Supported versions
| Minecraft | Fabric | NeoForge |
|-----------|:------:|:--------:|
| 26.2      | ✅     | ✅       |
| 26.1.2    | ✅     | ✅       |
| 26.1.1    | ✅     | ✅       |
| 26.1      | ✅     | ✅       |

Requires **Java 25**. Fabric builds need only Fabric Loader — **Fabric API is not required**.

### What's included
- Authentic Far Lands terrain generation (Perlin-noise coordinate precision restored).
- `/farlands` command — threshold + distance readout; `set`/`reset` with game-master permission.
- Config toggles for the terrain effect and the advancement detector.
- The `...where am I?` advancement when you reach the edge of sane terrain generation.

### Install
Download the jar matching your **Minecraft version and loader**, drop it in your `mods/` folder.

### Reach the Far Lands
```
/tp @s 12550821 120 0
```

*Inspired by AdyTech99's MIT-licensed Farlands Reborn. MIT licensed. By Shigeo + Mob.*
