# Farlands Reforged — Forge 1.20.2 … 1.20.4

Forge build for **Minecraft 1.20.2 (Forge 48), 1.20.3 and 1.20.4 (both Forge 49)**. One real build per
version: SRG names are baked into the jar, and `tools/compare_jars.py` shows the 1.20.4 jar differs from
the 1.20.2/1.20.3 ones.

## Forge before 1.20.6 runs on SRG names

This is the opposite of `farlands-reforged-forge-1.20.6` and everything after it. The Forge 1.20 – 1.20.4
installers rename Minecraft with `{MERGED_MAPPINGS}` (obfuscated → SRG), where 1.20.6 and later use
`{MOJMAPS} --reverse` (→ Mojang's names). A real install settles it: on Forge 47.0.0 the server's
`DensityFunctions$Noise` has `f_208787_`, not `noise`.

So this project does what the Forge 1.21 project once did by mistake, which is correct here:

- the `org.spongepowered.mixin` Gradle plugin writes `farlandsreforged.refmap.json`, and the mixin
  config names it;
- `reobf { jar {} }` plus `finalizedBy 'reobfJar'` rewrite the mod's own calls and `@Shadow` fields to
  SRG (`CommandsMixin`'s `dispatcher` becomes `f_82090_`);
- the `@Mixin` annotations have no `remap = false`.

`scripts/verify_artifact.py` checks the refmap has SRG targets for every injecting mixin and that
`reobfJar` really ran.

## Carried over from Forge 1.20.6

Every Forge 1.20.x build bundles **Mixin 0.8.5**, so the mixin config says `JAVA_17` and the two
`@Redirect` handlers are not `static`. The jar is Java 17 bytecode, the advancement lives in the plural
`advancements/` folder with an `{"item": ...}` icon, and the mod class keeps its no-arg constructor.

`pack.mcmeta` is `pack_format` 18 with `supported_formats` 18–26: 1.20.2 is resource/data 18, and
1.20.3/1.20.4 are resource 22 and data 26.

```bash
JAVA_HOME=/path/to/jdk-21 ./gradlew build -Pminecraft_version=1.20.2 -Pminecraft_version_range='[1.20.2]' \
  -Pforge_version=48.1.0 -Pforge_loader_major=48 -Pforge_version_min=48 -Pmod_version=0.5.0+mc1.20.2-forge
python scripts/verify_artifact.py
```

Gradle itself needs Java 21 (ForgeGradle 6 is Gradle 8). The code compiles for Java 17 through the
toolchain, which Gradle finds at `~/Library/Java/JavaVirtualMachines/temurin-17.jdk`.
