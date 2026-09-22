# Farlands Reforged — NeoForge 1.20.2 … 1.20.4

NeoForge build for **Minecraft 1.20.4**, retargeted to **1.20.2 and 1.20.3**. It is a copy of
`farlands-reforged-neoforge-1.20.6`, reworked for the older NeoForge. Every change was read out of the
loader's own jars or found on a real server:

- **Java 17** (toolchain, `JAVA_17`), an `{"item": ...}` advancement icon, and the plural `advancements/`
  folder, as for every Minecraft before 1.20.5.
- **`META-INF/mods.toml`, not `neoforge.mods.toml`.** The rename came with NeoForge 20.5.
- **`loaderVersion = "[1,)"`.** NeoForge 20.2 – 20.4 ships FancyModLoader 1.0.x, and 2.x late in 20.4.
- **Each dependency carries both `mandatory = true` and `type = "required"`.** FML 1.x requires
  `mandatory` and never reads `type`; FML 2.x reads only `type`. Each looks up only the key it knows.
- **`TickEvent.PlayerTickEvent` with a phase check**, because `PlayerTickEvent.Post` only exists from 20.5.
- **The mod constructor takes just `IEventBus`**, and the config is registered through
  `ModLoadingContext.get().registerConfig`. FML 1.0.2 onward injects the mod bus, while
  `ModContainer.registerConfig` is newer.
- **Config values are read with `get()`**, not `getAsBoolean()`/`getAsLong()`, which only arrive partway
  through NeoForge 20.4 (20.4.0-beta lacks them). The first retargeted jars called them, and NeoForge 20.2
  and 20.3 died with a `NoSuchMethodError` during mod loading.
- **The jar has a `pack.mcmeta`** (format 18, supporting 18 – 26). NeoForge 20.2 and 20.3 turn a mod's
  resources into a pack only if one is there; without it they log `Missing metadata in pack` and drop it,
  and the server otherwise runs perfectly. Later 20.4 builds merge every mod into one `mod_data` pack and
  do not care. The 1.20.5+ projects deliberately have none.
- The two `@Redirect` handlers are not `static`: NeoForge 20.x bundles Mixin 0.8.5.

```bash
./gradlew build
python scripts/verify_artifact.py
```

## 1.20.2 and 1.20.3 are retargeted copies

ModDevGradle can only build against NeoForge versions published with a `neoforge-moddev-bundle`, and no
20.2 or 20.3 build (nor early 20.4) was. So `gradle.properties` builds against 20.4.251, and
`tools/retarget_jar.py` rewrites the metadata for the other two:

| Minecraft | NeoForge range           | why that floor                                      |
|-----------|--------------------------|-----------------------------------------------------|
| 1.20.2    | `[20.2.86,20.3)`         | the first build whose loader reads `[[mixins]]`     |
| 1.20.3    | `[20.3.1-beta,20.4)`     | 20.3 never left beta                                |
| 1.20.4    | `[20.4.0-beta,20.5)`     |                                                     |

That is sound for two reasons, and it was proven on real servers at each floor:

- **Minecraft side:** the Fabric 1.20.2, 1.20.3 and 1.20.4 builds compile to byte-identical classes.
- **NeoForge side:** `tools/verify_loader_api.py` resolves every NeoForge, FML and event-bus method and
  field the jar calls against all 330 NeoForge 20.2 – 20.4 builds. That is the check that would have
  caught the `getAsBoolean()` mistake before a server did.
