# Farlands Reforged

Restores the classic **Far Lands** — the chaotic, stretched, glitched terrain that generated at the extreme edges
of old Minecraft worlds — in modern Minecraft. It lets the legacy 3D terrain noise overflow exactly the way it did
in Beta 1.7.3, then makes the rest of modern world generation treat that broken noise the way the old generator did.

No new blocks, no resource pack, no fuss — just the classic terrain ghost, faithfully reforged. Available for
**Fabric**, **NeoForge** and **Forge**.

> Inspired by [AdyTech99's](https://github.com/AdyTech99) MIT-licensed **Farlands Reborn**, whose core idea is to
> undo Mojang's far-coordinate Perlin-noise precision wrapping.

## Features

- **Authentic Far Lands generation** — the stretched walls, stacked sheets and long tunnels of the Edge and
  Corner Far Lands, starting at the classic ±12,550,821 on X and Z, with the second breakdown at ±25,101,648.
- **Beta-style dressing** — grass and trees on top, grass and dirt on every ledge inside, and the tunnels flooded
  up to sea level, just like the originals.
- **Classic by default** — normal terrain everywhere else is untouched, and nothing glitches early.
- **`/farlands` command** — shows the Far Lands threshold and your distance from it, plus credits.
  `/farlands set <threshold>` and `/farlands reset` require game-master permission.
- **Config toggles** — enable/disable the terrain effect and the advancement detector.
- **"...where am I?" advancement** — unlocks when you reach the edge of sane terrain generation.

## Supported versions

| Minecraft | Fabric | NeoForge | Forge |
|-----------|:------:|:--------:|:-----:|
| 26.2      | ✅     | ✅       | ✅    |
| 26.1.2    | ✅     | ✅       | ✅    |
| 26.1.1    | ✅     | ✅       | ✅    |
| 26.1      | ✅     | ✅       | ✅    |

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

`farlandsStartCoordinate` only moves the `/farlands` readout and the advancement. The terrain itself always
breaks down where the noise overflows, like it did in Beta.

## How it works

Beta's terrain noise sampled its first octave at `blockX * 171.103`. At 12,550,824 that passes 2^31, the
integer cast inside the Perlin sampler saturates, the fractional part stops being a fraction, and the fade curve
explodes. Modern Minecraft still ships that exact noise as `old_blended_noise`, but wraps its coordinates first.
Farlands Reforged does six small things to bring the original behavior back:

1. **Unwraps only the legacy 3D terrain noise.** Every other noise keeps its wrap, so features that did not exist
   in Beta (jaggedness, noise caves, aquifers) do not break early. Without this, mountain terrain starts glitching
   at ±2.86 million because the `jagged` noise runs at 750× block scale.
2. **Uses the Beta-era floor** inside the Perlin sampler, so the negative-coordinate Far Lands wrap around the
   integer limit the way they originally did instead of clamping.
3. **Passes the overflowed density straight through.** Modern world generation feeds the density into a
   `range_choice` whose "negative infinity" is -1,000,000. Exploded noise blows past that on both sides, so
   vanilla routes every Far Lands sample into the deep-underground branch and the result is a featureless solid
   slab from bedrock to the build limit. Letting the sign of the classic noise decide solid-versus-air again is
   what restores the walls, sheets and tunnels.
4. **Dresses every ledge.** Modern surface rules only run near the "preliminary surface", which ignores the 3D
   noise and points at ordinary terrain height. Inside the Far Lands every column is treated as above it, giving
   the grassy, tree-covered top and the grass-and-dirt ledges Beta had.
5. **Floods to sea level.** Modern aquifers treat anything below that preliminary surface as underground and hand
   out scattered pockets of water, lava and air. Inside the Far Lands the dimension's global fluid rule is used
   instead: water up to sea level, exactly what Beta did. Beta had no deep lava layer or magma either, and in a
   world flooded from bedrock up they are what freezes the server (water meeting lava, and bubble columns rising
   from every flooded cave floor queue tens of thousands of block updates), so inside the Far Lands the lava layer
   is water too and underwater magma is not placed.
6. **Keeps modern noodle caves out.** The long, thin noodle tunnels are carved straight into the final terrain
   density, so they bored through every Far Lands wall and sheet. Beta never had them; inside the Far Lands the
   noodle noise reports "no tunnel" instead. Beta-era caves (the cave carver) are still there.

Set `enableFarlandsTerrain = false` to turn all six off and get vanilla generation.

## Repository layout

Each loader/version pair is a self-contained Gradle project:

```
farlands-reforged-fabric-26.2/        Fabric source for Minecraft 26.2
farlands-reforged-fabric-26.1.2/      Fabric source for Minecraft 26.1.2
farlands-reforged-26.2/               NeoForge source for Minecraft 26.2
farlands-reforged-neoforge-26.1.2/    NeoForge source for Minecraft 26.1.2
farlands-reforged-forge-26.2/         Forge source (built for every Minecraft version, see its README)
PUBLISH/                              Release jars + CurseForge listing assets
```

Each project shares the same source under `src/main/java/com/shigeo/farlandsreforged/` and is retargeted to its
Minecraft version through `gradle.properties`. The Fabric and NeoForge 26.1.1 and 26.1 release jars are
version-retargeted builds of the corresponding 26.1.2 artifacts (the classes the mod hooks are identical across
these point releases). The Forge jars are real builds of the Forge project for each version.

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

## Changelog

- **0.3.1** — No modern noodle caves inside the Far Lands, so the walls and sheets are solid the way Beta's were.
- **0.3.0** — Authentic Far Lands. Previous versions only unwrapped the noise, which in modern world generation
  produced a solid slab riddled with vanilla caves; this release restores the classic shapes, surface and water,
  and stops the early mountain glitching at ±2.86 million. Arriving in the Far Lands no longer stalls the server
  (no lava layer or magma bubble columns under the flood). Fabric builds target Fabric Loader 0.19.5.
- **0.2.0** — Initial public release: unwrapped Perlin noise, `/farlands`, config, advancement.

## Credits

- **Shigeo + Mob** — author.
- **AdyTech99** — original idea via the MIT-licensed *Farlands Reborn*. Respect to the old noise ghosts.

## License

[MIT](LICENSE).
