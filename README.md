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

| Minecraft        | Fabric | NeoForge | Forge | Java |
|------------------|:------:|:--------:|:-----:|:----:|
| 26.3             | ✅     | —        | —     | 25   |
| 26.2             | ✅     | ✅       | ✅    | 25   |
| 26.1.2           | ✅     | ✅       | ✅    | 25   |
| 26.1.1           | ✅     | ✅       | ✅    | 25   |
| 26.1             | ✅     | ✅       | ✅    | 25   |
| 1.21.11          | ✅     | ✅       | ✅    | 21   |
| 1.21 … 1.21.10   | ✅     | ✅       | ✅¹   | 21   |
| 1.20.6           | ✅     | ✅       | ✅    | 21   |
| 1.20.5           | ✅     | ✅²      | —     | 21   |
| 1.20.2 … 1.20.4  | ✅     | ✅³      | ✅    | 17   |
| 1.20.1           | ✅     | ✅⁴      | ✅    | 17   |
| 1.20             | ✅     | —        | ✅    | 17   |
| 1.19 … 1.19.4    | ✅     | —⁵       | ✅    | 17   |

¹ Except 1.21.2, which Forge never shipped a build for. On Minecraft **1.21** the Forge jar needs
**Forge 51.0.23 or newer** — earlier 51.x builds bundle Mixin 0.8.5, which does not understand this mod's
`JAVA_21` mixins and stops the server during bootstrap. NeoForge's 21.2, 21.6, 21.7 and 21.9 never left
beta, so the 1.21.2, 1.21.6, 1.21.7 and 1.21.9 NeoForge jars are built against those betas.

² NeoForge 1.20.5 never left beta either; the jar needs **20.5.14-beta or newer**, the first build with
the player tick event it uses. Forge never shipped a 1.20.5 build.

³ NeoForge 1.20.2 needs **20.2.86** (its first stable build) or newer; 1.20.3 never left beta, so that jar
targets NeoForge's 20.3 betas.

⁴ NeoForge for Minecraft 1.20.1 is a fork of Forge 47 and runs the **Forge 1.20.1 jar** — there is no
separate NeoForge jar for it. Tested on NeoForge 47.1.60 and 47.1.106; the first 1.20.1 builds (47.1.5 –
47.1.11) cannot start a dedicated server at all, with or without mods.

⁵ NeoForge does not exist before Minecraft 1.20.1.

The 26.x builds need **Java 25**, the 1.21, 1.20.5 and 1.20.6 builds **Java 21**, and 1.19 – 1.20.4
**Java 17** — whatever that Minecraft version ships with. Fabric builds need only Fabric Loader —
**Fabric API is not required** (this mod is mixin-based).

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
farlands-reforged-fabric-26.3/        Fabric source for Minecraft 26.3 (new worldgen engine, see below)
farlands-reforged-fabric-26.2/        Fabric source for Minecraft 26.2
farlands-reforged-fabric-26.1.2/      Fabric source for Minecraft 26.1.2
farlands-reforged-fabric-1.21.11/     Fabric source for Minecraft 1.21.11
farlands-reforged-fabric-1.21/        Fabric source for Minecraft 1.21 ... 1.21.10
farlands-reforged-fabric-1.20.6/      Fabric source for Minecraft 1.20.5 and 1.20.6
farlands-reforged-fabric-1.20.4/      Fabric source for Minecraft 1.20.2 ... 1.20.4 (Java 17)
farlands-reforged-fabric-1.20.1/      Fabric source for Minecraft 1.20 and 1.20.1 (Java 17)
farlands-reforged-fabric-1.19.4/      Fabric source for Minecraft 1.19.3 and 1.19.4 (Java 17)
farlands-reforged-fabric-1.19.2/      Fabric source for Minecraft 1.19 ... 1.19.2 (Java 17, File-based packs)
farlands-reforged-neoforge-26.3/      NeoForge source for Minecraft 26.3 (NeoForge beta, unreleased)
farlands-reforged-26.2/               NeoForge source for Minecraft 26.2
farlands-reforged-neoforge-26.1.2/    NeoForge source for Minecraft 26.1.2
farlands-reforged-neoforge-1.21.11/   NeoForge source for Minecraft 1.21.11
farlands-reforged-neoforge-1.21/      NeoForge source for Minecraft 1.21 ... 1.21.10
farlands-reforged-neoforge-1.20.6/    NeoForge source for Minecraft 1.20.6 (1.20.5 is retargeted)
farlands-reforged-neoforge-1.20.4/    NeoForge source for Minecraft 1.20.4 (1.20.2, 1.20.3 retargeted)
farlands-reforged-forge-26.2/         Forge source for Minecraft 26.x (built per version, see its README)
farlands-reforged-forge-1.21.11/      Forge source for Minecraft 1.21.11 (ForgeGradle 7)
farlands-reforged-forge-1.21/         Forge source for Minecraft 1.21 ... 1.21.10 (ForgeGradle 6, official names)
farlands-reforged-forge-1.20.6/       Forge source for Minecraft 1.20.6 (ForgeGradle 6, Mixin 0.8.5)
farlands-reforged-forge-1.20.4/       Forge source for Minecraft 1.20.2 ... 1.20.4 (SRG: reobf + refmap)
farlands-reforged-forge-1.20.1/       Forge source for Minecraft 1.20 and 1.20.1 (SRG: reobf + refmap)
farlands-reforged-forge-1.19.4/       Forge source for Minecraft 1.19 ... 1.19.4 (SRG: reobf + refmap)
tools/                                Scripts that verify a port before the game runs (see tools/README.md)
PUBLISH/                              Release jars + CurseForge listing assets
```

Each project shares the same source under `src/main/java/com/shigeo/farlandsreforged/` and is retargeted to its
Minecraft version through `gradle.properties`. The Fabric and NeoForge 26.1.1 and 26.1 release jars are
version-retargeted builds of the corresponding 26.1.2 artifacts (the classes the mod hooks are identical across
these point releases). The Forge jars are real builds of the Forge project for each version.

The Minecraft 1.21 releases are the first ones this mod targets that ship **obfuscated**, so the two 1.21
projects map Minecraft with `loom.officialMojangMappings()` (Fabric) rather than the no-op mapping the 26.x
projects use, and build on Java 21. Nothing in the six Far Lands mechanisms had to change: every mixin
target, `@Shadow` field and redirected call is identical across all twelve versions from 1.21 to 1.21.11.
Two pieces of loader glue do differ, which is why there are two project folders per loader — 1.21.11
renamed `ResourceLocation` to `Identifier` and turned command permission levels into `PermissionCheck`
objects, while 1.21 through 1.21.10 still use the old names.

Each version in that range gets its own real build. From 1.21.6 on, `ServerPlayer` overrides `level()`
covariantly to return `ServerLevel` instead of `Level`, so the advancement check compiles to a different
call even though its source never changes, and a jar built for 1.21.8 would not run on 1.21.5.

Minecraft 26.3 rewrote world generation (compiled float density samplers, material rules instead of surface
rules, the Perlin wrap moved inside the shared sampler), so `farlands-reforged-fabric-26.3` has its own mixins
aimed at the same six behaviours. The legacy terrain noise can no longer simply skip its wrap there, because the
overflowed values do not fit in a float; instead `FarlandsClassicNoise` re-evaluates that noise in double
precision from vanilla's own octaves wherever the wrap would change anything (beyond ±98,000 blocks), which
reproduces the 26.2 result. `farlands-reforged-neoforge-26.3` combines those 26.3 mixins with the NeoForge
config, commands and events from `farlands-reforged-26.2`. It targets the NeoForge `26.3.0.0-beta` and is not
released yet; with the same seed its Far Lands terrain matches the Fabric 26.3 build. Forge has no 26.3 release
yet.

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

- **0.4.0** — Minecraft **1.21 … 1.21.11** on all three loaders, and the **"...where am I?" advancement now
  actually works on Fabric**. It never had: Fabric Loader does not turn a mod's `data/` directory into a data
  pack — that is Fabric API's job, and this mod deliberately does not depend on Fabric API — so the advancement
  JSON sat unread in every Fabric jar and the detector quietly did nothing. A built-in pack is now registered
  in code, with no new dependency and no `pack.mcmeta` to go stale. Terrain is unchanged.
- **0.3.1** — No modern noodle caves inside the Far Lands, so the walls and sheets are solid the way Beta's were.
  Also available for Fabric 26.3, ported to its new world generation engine.
- **0.3.0** — Authentic Far Lands. Previous versions only unwrapped the noise, which in modern world generation
  produced a solid slab riddled with vanilla caves; this release restores the classic shapes, surface and water,
  and stops the early mountain glitching at ±2.86 million. Arriving in the Far Lands no longer stalls the server
  (no lava layer or magma bubble columns under the flood). Fabric builds target Fabric Loader 0.19.5.
- **0.2.0** — Initial public release: unwrapped Perlin noise, `/farlands`, config, advancement.

## Credits

- **Shigeo** — author.
- **AdyTech99** — original idea via the MIT-licensed *Farlands Reborn*. Respect to the old noise ghosts.

## License

[MIT](LICENSE).
