# Farlands Reforged — NeoForge 1.21.11

NeoForge build for Minecraft `1.21.11`, the last release before the 26.x versioning, on NeoForge
`21.11.45`. Its sources are identical to the `farlands-reforged-neoforge-26.1.2` project: 1.21.11
already renamed `ResourceLocation` to `Identifier` and already has
`Commands.hasPermission(PermissionCheck)`. Builds on **Java 21**.

## Build

```bash
./gradlew build
python scripts/verify_artifact.py
```
