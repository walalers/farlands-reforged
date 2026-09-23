# Farlands Reforged — Forge 1.19 … 1.19.4

Forge build for **Minecraft 1.19 (Forge 41), 1.19.1 (42), 1.19.2 (43), 1.19.3 (44) and 1.19.4 (45)**, one
reobfuscated jar per version. It is `farlands-reforged-forge-1.20.1` (SRG at runtime, refmap and reobf,
Mixin 0.8.5, Java 17) with the 1.19 differences the Fabric projects have too:

- **No `Entity.level()`**; `FarlandsEvents` uses `ServerPlayer.server`.
- **`sendSuccess` takes a `Component`,** and `/farlands` answers through `sendSuccess(message, false)`
  because `sendSystemMessage` only arrives in 1.19.1.
- **`pack.mcmeta` carries that version's own formats.** They changed inside the family - resource / data
  9 / 10 on 1.19 - 1.19.2, 12 / 10 on 1.19.3, 13 / 12 on 1.19.4 - so they come from `gradle.properties`
  (`resource_pack_format`, `data_pack_format`) into vanilla's `pack_format` and Forge's
  `forge:resource_pack_format` / `forge:data_pack_format` keys. `tools/audit_release.py` checks them.

Every Forge 1.19.x build, first to last in each line, bundles Mixin 0.8.5 (read from the installers), so
the config declares `JAVA_17` and the `@Redirect` handlers are not static.

```bash
JAVA_HOME=/path/to/jdk-21 ./gradlew build -Pminecraft_version=1.19.2 -Pminecraft_version_range='[1.19.2]' \
  -Pforge_version=43.5.2 -Pforge_loader_major=43 -Pforge_version_min=43 \
  -Presource_pack_format=9 -Pdata_pack_format=10 -Pmod_version=0.5.0+mc1.19.2-forge
python scripts/verify_artifact.py
```
