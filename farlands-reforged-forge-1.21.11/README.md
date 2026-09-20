# Farlands Reforged — Forge 1.21.11

Forge build for Minecraft `1.21.11` on Forge `61.2.1`, the last release before the 26.x versioning.

Identical to `farlands-reforged-forge-1.21` — ForgeGradle 6, remapped mixins with a generated SRG refmap,
Gradle on Java 21 — except that the sources use the newer names 1.21.11 introduced: `Identifier` rather
than `ResourceLocation`, and `Commands.hasPermission(PermissionCheck)` rather than an int permission level.
Forge still runs on SRG here, so the refmap is just as necessary as it is for the older versions.

## Build

```bash
JAVA_HOME=/path/to/jdk-21 ./gradlew build
python scripts/verify_artifact.py
```
