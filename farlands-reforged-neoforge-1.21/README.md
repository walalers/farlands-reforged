# Farlands Reforged — NeoForge 1.21 … 1.21.10

NeoForge build for the older half of the Minecraft 1.21 family. Minecraft 1.21.11 lives in
`farlands-reforged-neoforge-1.21.11` instead, because it renamed `ResourceLocation` to `Identifier`
and turned command permission levels into `PermissionCheck` objects.

Same terrain code as every other project — `FarlandsRegion` plus the seven worldgen mixins — with the
NeoForge glue from `farlands-reforged-neoforge-26.1.2`: `ModConfigSpec` config, `RegisterCommandsEvent`
for `/farlands`, and `PlayerTickEvent.Post` for the advancement, so no `CommandsMixin` or
`ServerPlayerMixin` is needed here. Builds on **Java 21**.

NeoForge runs on Mojang's own names, so nothing is remapped on the way out — but a jar is still only
valid for the versions it was built against. See the note in the Fabric 1.21 project about
`ServerPlayer.level()` becoming covariant in 1.21.6; the same bytecode difference applies here.

## Build

`gradle.properties` targets 1.21 / NeoForge 21.0.167. Every other version is a real build of this same
project with the versions passed on the command line:

```bash
./gradlew build -Pminecraft_version=1.21.4 -Pminecraft_version_range='[1.21.4]' \
  -Pneoforge_version=21.4.157 -Pneoforge_version_range='[21.4.0,21.5)' \
  -Pmod_version=0.3.1+mc1.21.4-neoforge
python scripts/verify_artifact.py
```

| Minecraft | neoforge_version | note                        |
|-----------|------------------|-----------------------------|
| 1.21      | 21.0.167         |                             |
| 1.21.1    | 21.1.251         |                             |
| 1.21.2    | 21.2.1-beta      | NeoForge never went stable  |
| 1.21.3    | 21.3.97          |                             |
| 1.21.4    | 21.4.157         |                             |
| 1.21.5    | 21.5.98          |                             |
| 1.21.6    | 21.6.20-beta     | NeoForge never went stable  |
| 1.21.7    | 21.7.25-beta     | NeoForge never went stable  |
| 1.21.8    | 21.8.54          |                             |
| 1.21.9    | 21.9.16-beta     | NeoForge never went stable  |
| 1.21.10   | 21.10.64         |                             |
