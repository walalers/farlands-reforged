# Farlands Reforged

A tiny NeoForge `26.2` mod that restores classic Far Lands-style terrain generation by preserving full coordinate precision in Minecraft's Perlin noise wrapping method.

## Status

Alpha build target: Minecraft `26.2`, NeoForge `26.2.0.6-beta`.

## Features

- Restores Far Lands-style terrain generation by preserving Perlin noise coordinate precision.
- Keeps the default terrain behavior classic/authentic.
- Adds a small advancement, `...where am I?`, when a player reaches the configured Far Lands threshold.
- Adds `/farlands` for threshold/distance info and credits.
- Adds server/common config toggles for terrain and the advancement detector.

## Commands

```mcfunction
/farlands
/farlands set <threshold>
/farlands reset
```

`/farlands set` and `/farlands reset` require game master permissions. The threshold is used for the command readout and advancement detector; the actual terrain effect intentionally remains the classic coordinate-precision behavior.

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

1. Install the built jar from `build/libs/` into a Minecraft `26.2` NeoForge instance.
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
