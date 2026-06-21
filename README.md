# Farlands Reforged

Restores the classic **Far Lands** — the chaotic, stretched, glitched terrain that generated at the extreme edges
of old Minecraft worlds — in modern Minecraft. It works by preserving full coordinate precision in Minecraft's
Perlin-noise wrapping, the exact behavior Mojang smoothed away years ago.

No new blocks, no resource pack, no fuss — just the classic terrain ghost, faithfully reforged. Available for
both **Fabric** and **NeoForge**.

> Inspired by [AdyTech99's](https://github.com/AdyTech99) MIT-licensed **Farlands Reborn**, whose core idea is to
> undo Mojang's far-coordinate Perlin-noise precision wrapping.

## Features

- **Authentic Far Lands generation** — restores the original stretched/distorted terrain by keeping the
  Perlin-noise coordinate precision Mojang rounded off.
- **Classic by default** — normal terrain everywhere else is untouched.
- **`/farlands` command** — shows the Far Lands threshold and your distance from it, plus credits.
  `/farlands set <threshold>` and `/farlands reset` require game-master permission.
- **Config toggles** — enable/disable the terrain effect and the advancement detector.
- **"...where am I?" advancement** — unlocks when you reach the edge of sane terrain generation.

## Supported versions

| Minecraft | Fabric | NeoForge |
|-----------|:------:|:--------:|
| 26.2      | ✅     | ✅       |
| 26.1.2    | ✅     | ✅       |
| 26.1.1    | ✅     | ✅       |
| 26.1      | ✅     | ✅       |

Requires **Java 25**. Fabric builds need only Fabric Loader — **Fabric API is not required** (this mod is
mixin-based).

## Download

Grab the latest release from [CurseForge](https://www.curseforge.com/) (search "Farlands Reforged"), or build
from source below. Pick the jar matching your Minecraft version **and** loader.

## How to reach the Far Lands

Generate or load a world and teleport to the historical threshold:

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

## Repository layout

Each loader/version pair is a self-contained Gradle project:

```
farlands-reforged-fabric-26.2/        Fabric source for Minecraft 26.2
farlands-reforged-fabric-26.1.2/      Fabric source for Minecraft 26.1.2
farlands-reforged-26.2/               NeoForge source for Minecraft 26.2
farlands-reforged-neoforge-26.1.2/    NeoForge source for Minecraft 26.1.2
PUBLISH/                              Release jars + CurseForge listing assets
```

Each project shares the same source under `src/main/java/com/shigeo/farlandsreforged/` and is retargeted to its
Minecraft version through `gradle.properties`. The 26.1.1 and 26.1 release jars are version-retargeted builds of
the corresponding 26.1.2 artifacts (the compiled bytecode is identical across these point releases).

## Building

From inside any project folder:

```bash
./gradlew build
python scripts/verify_artifact.py
```

The built jar lands in `build/libs/`. `verify_artifact.py` sanity-checks the jar's metadata, classes, mixin
config, advancement, and lang entries.

To retarget a build to a different Minecraft version, edit that project's `gradle.properties` (`minecraft_version`,
the dependency version ranges, and `mod_version`), then rebuild.

## Credits

- **Shigeo + Mob** — author.
- **AdyTech99** — original idea via the MIT-licensed *Farlands Reborn*. Respect to the old noise ghosts.

## License

[MIT](LICENSE).
