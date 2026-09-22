# Farlands Reforged — Forge 1.20 / 1.20.1

Forge build for **Minecraft 1.20 (Forge 46) and 1.20.1 (Forge 47)**. It is `farlands-reforged-forge-1.20.4`
(SRG at runtime, refmap and reobf, Mixin 0.8.5, Java 17) with two differences:

- **No `AdvancementHolder`.** Before 1.20.2 the lookup is `getAdvancement(id)`, returning a plain
  `Advancement`.
- **`pack.mcmeta` is just `pack_format: 15`.** `supported_formats` arrived in 1.20.2; 1.20 and 1.20.1 are
  resource and data format 15.

```bash
JAVA_HOME=/path/to/jdk-21 ./gradlew build -Pminecraft_version=1.20 -Pminecraft_version_range='[1.20]' \
  -Pforge_version=46.0.14 -Pforge_loader_major=46 -Pforge_version_min=46 -Pmod_version=0.4.0+mc1.20-forge
python scripts/verify_artifact.py
```

Tested on real servers at both ends of each line, Forge 46.0.1 … 46.0.14 and 47.0.0 … 47.4.23. On
47.0.0 the installed server's classes are SRG-named (`DensityFunctions$Noise.f_208787_`), which is what
this project's refmap and reobf target.

## NeoForge 1.20.1 runs this jar

NeoForge's Minecraft 1.20.1 builds are a fork of Forge 47 (published as `net.neoforged:forge` 47.1.x):
same `net.minecraftforge` API, same SRG runtime, and they answer to the mod id `forge`, so the Forge jar's
dependency is satisfied. Tested on NeoForge 47.1.60 and 47.1.106, including the terrain probe and the
corrupted-advancement probe. The earliest builds (47.1.5, 47.1.8, 47.1.11) crash in their own launcher
(`Duplicate key ... loader-47.1.37.jar`) before loading any mod, 47.1.5 even with no mods at all, and
47.1.12 – 47.1.59 have no installer on Maven.
