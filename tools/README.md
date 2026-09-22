# Tools

Two sets of scripts. The **porting** ones answer the questions a compile cannot — *do my mixin targets
still exist*, *is the injection point still inside the method*, *can one jar serve several Minecraft
versions*. The **release** ones build, check and publish a release across every loader and version at
once.

They live here rather than in a scratchpad because every one of them had been written from scratch more
than once before it was kept.

## Porting

They work off two public sources. `fetch_mappings.py` downloads and caches both next to the scripts
(`tools/mappings/`, `tools/intermediary/`, neither is committed):

```bash
python tools/fetch_mappings.py 1.21 1.21.1 1.21.2 1.21.3 1.21.4 1.21.5 1.21.6 1.21.7 1.21.8 1.21.9 1.21.10 1.21.11
```

It pulls Mojang's official mappings (named -> obfuscated) from the version manifest and Fabric's
intermediary (obfuscated -> intermediary) from `maven.fabricmc.net`.

## `check_targets.py` — do the targets exist, and did their signatures move?

Reads the Mojang mappings for a list of versions and prints, for every class, method and field the mod
mixes into, whether it exists and whether its signature changed anywhere in the range. This is the first
thing to run against a new version family: it turns "will this port work?" into a table.

## `verify_injections.py <named-minecraft.jar>` — is the injection point really there?

The Java compiler never checks mixin targets, so a project can build cleanly and then fail at load with
*"@Redirect target not found"*. This disassembles the real classes out of a Mojang-mapped Minecraft jar
(Loom leaves one in `~/.gradle/caches/fabric-loom/minecraftMaven/.../minecraft-merged-*.jar` after a
build) and checks each target method, each `@Shadow` field, and — for the two `@Redirect`s — that the
redirected call is actually inside the method being redirected.

## `check_intermediary.py` — can one jar cover several versions?

Fabric remaps a finished jar to intermediary, so a jar built for one version only runs on another if
every class, method and field it touches carries the same intermediary name there. This chains the two
mapping sets and groups the versions that share an identical set of names.

Two things it deliberately does not hide: a member Mojang leaves unobfuscated, and a member intermediary
leaves unmapped (overrides inherit the declaring interface's name), are both printed with `(unmapped)`
rather than silently falling back to a name that looks stable.

## `compare_jars.py <jars...>` — which built jars are actually interchangeable?

The last word on whether one jar can cover several Minecraft versions, and the one to trust when it
disagrees with `check_intermediary.py`. It hashes the compiled classes and groups the jars that match.

Mapping tables only see the names a mod mentions; they do not see what the compiler emitted. A covariant
override is the trap: `ServerPlayer.level()` returns `Level` on 1.21 and `ServerLevel` on 1.21.10, so the
two builds call different methods while every name in the source stays the same. Only the bytecode shows
it, which is why the 1.21 family gets a real build per version rather than one jar with a wide range.

## Release

### `build_release.sh <version>` — build everything

Builds every jar — Fabric and Forge for Minecraft 1.18.2 and 1.19 … 1.19.4, three loaders across 1.20 … 1.20.6,
1.21 … 1.21.11 and 26.1 … 26.3 —
into one staging directory. Each project's quirks are baked in: the Fabric and NeoForge projects have no
wrapper and use a cached Gradle, Forge 1.20.6 and 1.21–1.21.10 are ForgeGradle 6 and so need Gradle 8 on
Java 21, Forge numbers its major per Minecraft version (26.1 is Forge 62, not 65), and NeoForge 1.20.5 is
retargeted from the 1.20.6 build because ModDevGradle cannot build against NeoForge's 20.5 betas.

### `retarget_jar.py` — one build, several Minecraft versions

Every compiled class in the 26.1, 26.1.1, 26.1.2 and 26.2 jars is byte-identical, so the 26.1 and 26.1.1
Fabric and NeoForge jars are copies of the 26.1.2 build with two lines of metadata rewritten. Only sound
while the classes really do match — check with `compare_jars.py` first.

That covers the Minecraft side only. When the loader versions differ too — the NeoForge 1.20.2, 1.20.3 and
1.20.5 jars are retargets of builds against a newer NeoForge — also run `verify_loader_api.py`.

### `verify_loader_api.py <jar> --neoforge V...` — does every loader call exist in that version?

Resolves every NeoForge / FancyModLoader / event-bus method and field the jar references, with its exact
descriptor and through the class hierarchy, against the jars of each NeoForge version given (fetched from
Maven and cached). Checking that the *classes* exist is not enough: the NeoForge 1.20.4 build retargeted
to 20.2 and 20.3 had every class it needed, but `ModConfigSpec.BooleanValue.getAsBoolean()` only arrives
in 20.4, and those servers died during mod loading. Run it against every build in a jar's declared range;
the 1.20.2 – 1.20.4 check covered all 330 NeoForge 20.2 – 20.4 builds.

### `audit_release.py <dir> --version V` — check the release as a whole

Each project's `scripts/verify_artifact.py` checks one jar in detail; this checks the set. Filename
against declared version (build/libs keeps old releases, and a glob will happily pick a stale one), the
Fabric data-pack fix present on every Fabric jar and absent from the others, `pack.mcmeta` on Forge with
the right schema for its version, every mixin in the config actually present as a class.

Every rule is there because that mistake has shipped. Nine of twelve Fabric jars once went out without
the data-pack fix, and nothing failed loudly — the advancement simply never registered.

### `verify_pack_api.py <minecraft.jar>...` — the pack fix's version check

`verify_injections.py` covers the worldgen mixins and predates the Fabric data-pack fix. This does the
same job for that code: every constructor, field and method `FarlandsModPack` and `PackRepositoryMixin`
name, disassembled out of each version's Minecraft jar. The API changed shape five times since 1.18.2 —
1.18.2 – 1.19.2 (packs read from a `java.io.File`), 1.19.3 – 1.19.4, 1.20 / 1.20.1, 1.20.2 – 1.20.4, and
1.20.5 on — and the script picks the check list for each jar's version.

### `server_test.py --mc V --jar J` — does it work on a real server?

Downloads a verified vanilla server jar and a Fabric launcher, boots them with the jar in `mods/`, and
checks three things over RCON: the mod loaded with no mixin error, `/farlands` answers, and
`/datapack list` names `farlandsreforged`.

That last one is the point. Loom's `runServer` runs development classes, not the jar that ships, so it
cannot see this class of bug at all. `--corrupt-advancement` rebuilds the jar with deliberately invalid
advancement JSON: a server that really reads the pack logs a parse error, and one that does not stays
silent. That is the only loader-independent proof, because the pack's name in `/datapack list` differs
per loader.

`--probe X Z` adds the terrain half: it forceloads that column and reads it block by block over RCON
(`execute if block`), as air, fluid, plant or solid. A worldgen mixin that silently fails to apply leaves
a server that passes every other check, so this is what proves the shipped jar actually makes Far Lands.
At `--probe 12550850 0` on seed 1234, vanilla is ocean (water from y=62 to 48, then seabed); with the mod
the column holds solid layers up to y=222, flooded between them. `/farlands` must also answer with the
mod's own text - a bare "Unknown or incomplete command" is a reply too, and used to count as one.

The probe uses only commands every supported version has, and two of the obvious ones are newer than
they look: `execute if loaded` arrives in 1.19.4 (before it, the probe waits for a block test to stop
answering "That position is not loaded"), and `#minecraft:replaceable` in 1.20 (before it, the tag's
members are tested by name). Either one missing used to fail every 1.19 probe on terrain that was fine.

### `modded_server_test.py --loader forge|neoforge ...` — the same, for the other two loaders

Forge and NeoForge servers are installed rather than launched, so they get their own script. This matters
more than it sounds: ForgeGradle 6's `runServer` does not work in this repository at all, and would not
be a valid test if it did, because the development run and the shipped jar use different naming. Three
separate bugs that left the Forge jars completely unloadable were each found only this way.

The data pack's name differs per loader — Forge lists `mod:farlandsreforged`, NeoForge merges everything
into one pack called `mod_data` — so a missing name is not always a failure. `--corrupt-advancement` is
the check that does not care which loader it is talking to.

Old installers need help, and the script gives it automatically:

- **`authserver.mojang.com` no longer resolves**, and installers from before Mojang retired it (NeoForge
  20.4.0-beta, for one) look it up for a diagnostic and crash. On that failure the install is retried with
  `-Djdk.net.hosts.file` pointing at the installer's download hosts, resolved beforehand.
- **Forge 49.0.x writes a shim jar** (`forge-<ver>-shim.jar`, started with `-jar`) instead of
  `unix_args.txt`; the launcher uses whichever the install produced.
- **An installer's embedded library can fail its own checksum** (NeoForge 20.4.0-beta's universal jar),
  and the installer then gives up rather than downloading it. The Maven copy is seeded first, only if it
  matches the profile's SHA-1.
- **NeoForge for Minecraft 1.20.1** is published as `net.neoforged:forge` (a fork of Forge 47) and runs
  the Forge 1.20.1 jar; `--loader neoforge --mc 1.20.1` installs it.

Each server runs on the Java its Minecraft version ships with: 17 before 1.20.5, 21 up to 1.21.11, 25
for 26.x (`server_test.java_for`, which refuses rather than fall back to whatever `java` is on the PATH).

### `release_server_test.py <dir> --version V` — every jar, on a real server

Runs the two scripts above over a whole release: three lanes, one per loader, side by side. Every jar
gets the mixin-error scan, `/farlands`, `/datapack list` and `--probe 12550850 0`; every NeoForge jar
also gets the corrupted-advancement boot. At the end it prints a pass/fail per jar and checks that all
the Far Lands columns match. All 48 jars of 0.4.0 took about 2.5 hours and came back identical.

`--only neoforge` or `--only forge:1.21 fabric:26.2` reruns a subset. Vanilla server jars are
downloaded first, one at a time, and seeded into each Forge/NeoForge install so no two installers fetch
one at once; each install is deleted after its test, keeping only its logs; and a download that fails on
a network error is retried instead of being reported as a broken jar.

### `client_test.sh <project>` — the client side

Everything else here tests dedicated servers. The Fabric pack fix also adds its pack to the client's
resource-pack repository, and the client helpfully names every pack it loads:
`Reloading ResourceManager: vanilla, farlandsreforged`.

### `region_slice.py` — diff generated terrain

Reads Anvil region files without Minecraft, so two worlds can be compared block for block. Compare the
**solid/fluid/air shape**, not exact block ids: two versions on the same seed legitimately disagree about
seagrass and flowers, but not about where the walls are.

### `upload_curseforge.py <dir> --version V --changelog F` — publish

Resolves each jar to its CurseForge game-version ids from the filename, and refuses to upload anything if
a single one does not resolve. Dry run unless `--go`. Builds the multipart body itself, because `curl -F`
truncates a value at the first `;` and the metadata is JSON full of them.
