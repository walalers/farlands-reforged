# Farlands Reforged — Forge 1.21.11

Forge build for Minecraft `1.21.11` on Forge `61.2.1`, the last release before the 26.x versioning.

**This project has more in common with `farlands-reforged-forge-26.2` than with
`farlands-reforged-forge-1.21`**, because Forge changed twice at once here:

- **ForgeGradle 7, not 6.** ForgeGradle 6 cannot even assemble Forge 61's userdev jar — it fails with
  `ZipException: duplicate entry: mcp/client/Start.class`. ForgeGradle 7 is what the 1.21.11 MDK ships with.
- **Official names, not SRG.** ForgeGradle 7 performs no reobfuscation: the finished jar still calls
  `ServerPlayer.level()` and `Identifier`, not `m_...`/`f_...`. So there is no refmap and the mixins use
  `remap = false`, exactly as the 26.x project does — and unlike every older version in this family, whose
  jars ForgeGradle 6 rewrites into SRG.

The sources use the newer names 1.21.11 introduced: `Identifier` rather than `ResourceLocation`, and
`Commands.hasPermission(PermissionCheck)` rather than an int permission level. That makes them identical to
the 26.x Forge sources.

`scripts/verify_artifact.py` is the mirror image of the one in `farlands-reforged-forge-1.21`: it fails if
any SRG name appears in the jar, or if a refmap was generated, since either would mean the mixins are
hunting for members this runtime does not have.

## Build

Unlike the 1.21 project, this one runs Gradle on the default JDK, like the rest of the repository:

```bash
./gradlew build
python scripts/verify_artifact.py
```
