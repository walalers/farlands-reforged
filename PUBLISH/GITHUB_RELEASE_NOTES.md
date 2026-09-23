# GitHub Release v0.5.0 — paste-ready

To publish the release page:

1. Go to **https://github.com/walalers/farlands-reforged/releases/new**, create tag `v0.5.0` on `main`.
2. **Release title:** `Farlands Reforged 0.5.0`
3. Paste the notes below into the description.
4. Under **Attach binaries**, drag in the 78 `0.5.0` jars from `PUBLISH/jars/`.
5. **Publish release**.

---

## Farlands Reforged 0.5.0: back to Minecraft 1.18.2

This release adds **30 new builds, covering every Minecraft version from 1.18.2 to 1.20.6**. With the
1.21 and 26.x builds, that makes 78 jars.

### What's new

- **Minecraft 1.20 to 1.20.6** on Fabric, Forge and NeoForge (where NeoForge exists).
- **Minecraft 1.19 to 1.19.4** on Fabric and Forge.
- **Minecraft 1.18.2** on Fabric and Forge.

The Far Lands are the same code as in every other build. Each new jar was run on a real server, and the
terrain at x = 12,550,850 came out identical, block for block, to the 1.21 and 26.x builds on the same seed.
The "...where am I?" advancement and `/farlands` work on every version, including Fabric without Fabric API.

### Not supported: 1.18 and 1.18.1

Minecraft rewrote its terrain generator between 1.18.1 and 1.18.2. The code this mod hooks to make the
Far Lands doesn't exist in 1.18 or 1.18.1, so 1.18.2 is the oldest version it runs on.

### Unchanged

Nothing changed in the 1.21 and 26.x builds except the version number. If you are on one of those
versions, 0.4.0 and 0.5.0 behave identically, and terrain generation is the same.

### Supported versions

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
