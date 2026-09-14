# Farlands Reforged Fabric

Fabric build for Minecraft `26.1.2`.

Tiny Fabric version of Farlands Reforged. Restores the classic Far Lands: the legacy 3D terrain noise overflows exactly as it did in Beta 1.7.3, the overflowed density decides solid-versus-air, and the surface and water follow the old rules (grass on every ledge, flooded to sea level). See the repository README for the full explanation. Includes `/farlands`, config, and the `...where am I?` advancement.

## Build

```bash
./gradlew build
python scripts/verify_artifact.py
```
