# GitHub Release v0.6.0 — paste-ready

To publish the release page:

1. Go to **https://github.com/walalers/farlands-reforged/releases/new**, create tag `v0.6.0` on `main`.
2. **Release title:** `Farlands Reforged 0.6.0`
3. Paste the notes below into the description.
4. Under **Attach binaries**, drag in the 80 `0.6.0` jars from `PUBLISH/jars/`.
5. **Publish release**.

---

## Farlands Reforged 0.6.0: FarMan, and Far Lands wherever you want them

Two new features, on all 80 builds (Minecraft 1.18.2 to 26.3, Fabric, Forge and NeoForge).

### FarMan (off by default)

The pitch-black, red-eyed figure from the old Far Lands creepypastas. Turn him on and he haunts anyone who
stays out in the Far Lands: first "FarMan joined the game", then cave noises, footsteps behind you, whispers
in chat and redstone torches on the ledges, then him standing far off, watching. Then right behind you.
Walk up to him or stare too long and he's gone. He never hurts anyone: the worst he does is a scare.

- Turn him on with `/farlands farman on` (operators), or `enableFarMan = true` in the config.
  `/farlands farman summon` and `/farlands farman scare` call him right now.
- Built from vanilla parts, so the mod is still **server-side only**: players need nothing installed to see him.
- He only walks the Overworld Far Lands, and nothing about him is saved to your world.

### Choose where the Far Lands start

Requested on CurseForge. Don't want to travel 12.5 million blocks? `farlandsStartX` and `farlandsStartZ`
(or `/farlands set x|z <distance>`) bring the Far Lands closer on each axis, and the real terrain moves with
them: the same wall, the same stacked sheets, the same flooded tunnels, just starting where you said.

- Anywhere from 1 up to the classic 12,550,821. They can only come closer, not go further out.
- The start snaps outwards by at most 3 blocks, onto the 4-block grid the terrain noise is sampled on, so the
  wall stands exactly on it.
- Chunks that already exist keep their terrain; only newly generated ones change.
- `/farlands`, the advancement and FarMan all follow the new start.
- **Config change:** these replace `farlandsStartCoordinate`, which only ever moved the `/farlands` readout and
  the advancement. It no longer does anything; if you had changed it, set `farlandsStartX` and
  `farlandsStartZ` instead (they move the terrain too).

### Unchanged

With the default settings the Far Lands generate exactly as in 0.5.0, block for block: all 80 jars were run
on real servers of their own version and loader, and the terrain came out identical.

### Supported versions

| Minecraft        | Fabric | NeoForge | Forge | Java |
|------------------|:------:|:--------:|:-----:|:----:|
| 26.3             | ✅     | ✅⁶      | ✅⁶   | 25   |
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
| 1.18.2           | ✅     | —⁵       | ✅    | 17   |

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

⁵ NeoForge does not exist before Minecraft 1.20.1. Minecraft 1.18 and 1.18.1 are not supported: their
world generator predates the density functions the Far Lands mechanisms hook into.

⁶ NeoForge 26.3 has not left beta, so that jar is built against **26.3.0.10-beta** and runs on the 26.3 betas from 26.3.0.0-beta on. Forge 26.3 needs **Forge 66** or newer.

The 26.x builds need **Java 25**, the 1.21, 1.20.5 and 1.20.6 builds **Java 21**, and 1.18.2 to 1.20.4
**Java 17**, whatever that Minecraft version ships with. Fabric builds need only Fabric Loader.
**Fabric API is not required.**

### Install

Download the jar matching your **Minecraft version and loader**, drop it in your `mods/` folder, and remove
any older Farlands Reforged jar. The jars are version-specific on purpose, so take the one that names your
version.

### Reach the Far Lands

```
/tp @s 12550800 100 0
/tp @s 0 100 12550800
/tp @s -12550800 100 0
/tp @s 12550900 100 12550900
```

*Inspired by AdyTech99's MIT-licensed Farlands Reborn. MIT licensed. By Shigeo.*
