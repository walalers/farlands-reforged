# Farlands Reforged

A tiny NeoForge `26.1.2` mod that restores the classic Far Lands: the legacy 3D terrain noise overflows exactly as it did in Beta 1.7.3, and the rest of world generation treats that broken noise the way the old generator did.

## Status

Alpha build target: Minecraft `26.1.2`, NeoForge `26.1.2.76`.

## Features

- Restores the authentic Far Lands: stretched walls, stacked sheets and tunnels from ±12,550,821 on X and Z.
- Grass and trees on top, grass and dirt on every ledge, tunnels flooded to sea level, like Beta 1.7.3.
- Only the legacy 3D terrain noise breaks down; every other noise stays wrapped so nothing glitches early.
- Adds a small advancement, `...where am I?`, when a player reaches the configured Far Lands threshold.
- Adds `/farlands` for threshold/distance info and credits.
- Adds server/common config toggles for terrain and the advancement detector.

## Commands

```mcfunction
/farlands
/farlands set <threshold>
/farlands reset
```

`/farlands set` and `/farlands reset` require game master permissions. The threshold is used for the command readout and advancement detector; the terrain itself always breaks down at the classic threshold, like Beta.

## Config

Generated after first launch:

```txt
config/farlandsreforged-common.toml
```

Defaults:

```toml
enableFarlandsTerrain = true
enableWhereAmIAdvancement = true
farlandsStartCoordinate = 12550821
```

## Credits

Inspired by AdyTech99's MIT-licensed **Farlands Reborn**, whose core idea is to undo Mojang's far-coordinate Perlin noise precision wrapping.

## Build

```bash
./gradlew build
python scripts/verify_artifact.py
```

## Test in-game

1. Install the built jar from `build/libs/` into a Minecraft `26.1.2` NeoForge instance.
2. Generate a new world.
3. Teleport near the historical Far Lands threshold:

```mcfunction
/tp @s 12550821 120 0
```

Also test Z-axis, negative coordinates, and corners:

```mcfunction
/tp @s 0 120 12550821
/tp @s -12550821 120 0
/tp @s 12550821 120 12550821
```

Expected: distorted Far Lands-style terrain appears beyond/around the threshold, and the `...where am I?` advancement unlocks without chat spam.
