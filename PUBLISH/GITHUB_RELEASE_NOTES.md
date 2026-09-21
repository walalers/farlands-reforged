# GitHub Release v0.4.0 — paste-ready

To publish the release page:

1. Go to **https://github.com/walalers/farlands-reforged/releases/new**, create tag `v0.4.0` on `main`.
2. **Release title:** `Farlands Reforged 0.4.0`
3. Paste the notes below into the description.
4. Under **Attach binaries**, drag in the 48 `0.4.0` jars from `PUBLISH/jars/`.
5. **Publish release**.

---

## Farlands Reforged 0.4.0 — Minecraft 1.21, and the advancement finally works

Two things in this release: the mod now runs on the whole **Minecraft 1.21 family**, and the
**"...where am I?" advancement works on Fabric** — which, it turns out, it never had.

### Minecraft 1.21 … 1.21.11

Every version from **1.21 to 1.21.11** is supported on **Fabric**, **NeoForge** and **Forge**, as its own
build. The Far Lands themselves are the same code as the 26.x releases — the same seven worldgen
mechanisms, unchanged — so the terrain you get at ±12,550,821 is identical.

These builds need **Java 21**; the 26.x builds still need Java 25.

### The "...where am I?" advancement now works on Fabric

The advancement has been advertised since 0.2.0 and has never once fired on Fabric.

Fabric Loader, unlike Forge and NeoForge, does not turn a mod's `data/` directory into a data pack. That
is Fabric API's resource loader — and this mod deliberately does not depend on Fabric API. So the
advancement JSON sat in the jar unread, `server.getAdvancements().get(...)` returned null, and the
detector returned early every tick. Nothing crashed, nothing was logged, and the terrain half of the mod
worked perfectly, which is exactly why it went unnoticed for three releases. The only visible symptom was
that `/datapack list` showed `vanilla` and nothing else.

Fabric builds now register a built-in pack in code, which is what Fabric API does internally — so there is
still **no Fabric API dependency**. The pack carries no `pack.mcmeta` on purpose: `pack_format` numbers
change nearly every release, and a stale one silently drops the pack instead of failing loudly.

If you play on Fabric, this is the release where the advancement starts existing. **Forge and NeoForge
were never affected** — both loaders expose mod data packs themselves.

### Unchanged

Terrain generation is untouched. A world generated with 0.3.1 generates identically under 0.4.0.

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

¹ Except 1.21.2 — Forge never shipped a build for it.

NeoForge has no stable 26.3 yet, so there is no NeoForge 26.3 jar. The NeoForge jars for 1.21.2, 1.21.6,
1.21.7 and 1.21.9 are built against those versions' beta NeoForge releases, because NeoForge never took
them to stable.

Fabric builds need only Fabric Loader — **Fabric API is not required**.

### Install

Download the jar matching your **Minecraft version and loader**, drop it in your `mods/` folder, and remove
any older Farlands Reforged jar. The jars are version-specific on purpose: a 1.21.8 jar will not work
correctly on 1.21.5, so take the one that names your version.

### Reach the Far Lands

```
/tp @s 12550800 100 0
/tp @s 0 100 12550800
/tp @s -12550800 100 0
/tp @s 12550900 100 12550900
```

*Inspired by AdyTech99's MIT-licensed Farlands Reborn. MIT licensed. By Shigeo.*
