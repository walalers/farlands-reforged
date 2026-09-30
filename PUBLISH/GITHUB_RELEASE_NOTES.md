# GitHub Release v0.7.0 — paste-ready

To publish the release page:

1. Go to **https://github.com/walalers/farlands-reforged/releases/new**, create tag `v0.7.0` on `main`.
2. **Release title:** `Farlands Reforged 0.7.0`
3. Paste the notes below into the description.
4. Under **Attach binaries**, drag in the 80 `0.7.0` jars from `PUBLISH/jars/`.
5. **Publish release**.

---

## Farlands Reforged 0.7.0: Far Lands at the edge of the world

One new feature, on all 80 builds (Minecraft 1.18.2 to 26.3, Fabric, Forge and NeoForge).

### Push the Far Lands further out

Requested on CurseForge. In 0.6.0, `farlandsStartX` and `farlandsStartZ` could only bring the Far Lands
closer. Now they also push them further out, anywhere up to 30,000,000, the edge of the world.

- The land between the classic 12,550,821 and your start is plain vanilla terrain, block for block. The real
  Far Lands (the wall, the stacked sheets, the flooded tunnels) begin exactly at the start.
- The world border stands at 29,999,984. Set a start just past it, say `/farlands set 29999985`, and the Far
  Lands stand behind the border: you can see them but not reach them.
- As before, the start snaps outwards by at most 3 blocks onto the 4-block grid the terrain noise is sampled
  on, only newly generated chunks change, and `/farlands`, the advancement and FarMan all follow it.

### Unchanged

With the default settings the Far Lands generate exactly as in 0.6.0, block for block. All 80 jars ran on
real servers of their own version and loader: the classic Far Lands column came out identical on every one,
the walls at a start of 1,000,000 and of 20,000,000 match the classic wall, and with a start of 20,000,000
the land at the classic corner is the vanilla terrain.

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
