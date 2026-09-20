# Farlands Reforged — Fabric 1.21.11

Fabric build for Minecraft `1.21.11`, the last release before the 26.x versioning.

Its sources are identical to the 26.1.2 / 26.2 projects: 1.21.11 already renamed `ResourceLocation` to
`Identifier` and already has `Commands.hasPermission(PermissionCheck)`, so nothing in the mod had to
change. Minecraft 1.21 … 1.21.10 still use the old names and live in `farlands-reforged-fabric-1.21`.

Unlike the 26.x jars, 1.21.11 Minecraft is obfuscated, so this project maps it with
`loom.officialMojangMappings()` and Loom remaps the finished jar to intermediary. It builds on **Java 21**.

## Build

```bash
./gradlew build
python scripts/verify_artifact.py
```
