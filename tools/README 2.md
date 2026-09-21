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

Builds all 48 jars — three loaders across Minecraft 1.21 … 1.21.11 and 26.1 … 26.3 — into one staging
directory. Each project's quirks are baked in: the Fabric and NeoForge projects have no wrapper and use
a cached Gradle, Forge 1.21–1.21.10 is ForgeGradle 6 and so needs Gradle 8 on Java 21, and Forge numbers
its major per Minecraft version (26.1 is Forge 62, not 65).

### `retarget_jar.py` — one build, several Minecraft versions

Every compiled class in the 26.1, 26.1.1, 26.1.2 and 26.2 jars is byte-identical, so the 26.1 and 26.1.1
Fabric and NeoForge jars are copies of the 26.1.2 build with two lines of metadata rewritten. Only sound
while the classes really do match — check with `compare_jars.py` first.

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
name, disassembled out of each version's Minecraft jar.

### `server_test.py --mc V --jar J` — does it work on a real server?

Downloads a verified vanilla server jar and a Fabric launcher, boots them with the jar in `mods/`, and
checks three things over RCON: the mod loaded with no mixin error, `/farlands` answers, and
`/datapack list` names `farlandsreforged`.

That last one is the point. Loom's `runServer` runs development classes, not the jar that ships, so it
cannot see this class of bug at all. `--corrupt-advancement` rebuilds the jar with deliberately invalid
advancement JSON: a server that really reads the pack logs a parse error, and one that does not stays
silent. That is the only loader-independent proof, because the pack's name in `/datapack list` differs
per loader.

### `modded_server_test.py --loader forge|neoforge ...` — the same, for the other two loaders

Forge and NeoForge servers are installed rather than launched, so they get their own script. This matters
more than it sounds: ForgeGradle 6's `runServer` does not work in this repository at all, and would not
be a valid test if it did, because the development run and the shipped jar use different naming. Three
separate bugs that left the Forge jars completely unloadable were each found only this way.

The data pack's name differs per loader — Forge lists `mod:farlandsreforged`, NeoForge merges everything
into one pack called `mod_data` — so a missing name is not always a failure. `--corrupt-advancement` is
the check that does not care which loader it is talking to.

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
