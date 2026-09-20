# Porting tools

Five small scripts used to port Farlands Reforged to a new Minecraft version without guessing. They
answer the questions a compile cannot: *do my mixin targets still exist*, *is the injection point still
inside the method*, and *can one jar serve several Minecraft versions*.

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
