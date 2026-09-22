#!/usr/bin/env bash
# Build every jar in a Farlands Reforged release, from every project, into one staging directory.
#
#   tools/build_release.sh 0.4.0 [outdir]
#
# The repository ships no Gradle wrapper for the Fabric and NeoForge projects, so they use a cached
# distribution; the Forge projects have their own wrappers. Forge 1.21-1.21.10 is the odd one out: it
# is ForgeGradle 6, which means Gradle 8, which cannot run on Java 25, so that project alone gets
# JAVA_HOME pointed at the JDK 21.
#
# 26.1 and 26.1.1 are not built. Every compiled class in the 26.1, 26.1.1, 26.1.2 and 26.2 jars is
# byte-identical, so those two are retargeted copies of the 26.1.2 build - see tools/retarget_jar.py.
#
# Every build is `clean build`. The repository sits under ~/Desktop, which iCloud Drive syncs, and iCloud
# resolves a conflict by leaving a copy such as "farlandsreforged 2/" beside the original - inside build/
# too. A build that reuses build/ sweeps those copies into the jar without any error.
set -uo pipefail

VERSION="${1:?usage: build_release.sh <version> [outdir]}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${2:-$REPO/build-release}"
LOGS="$OUT/logs"

GRADLE_BIN="${GRADLE_BIN:-$(ls -d "$HOME"/.gradle/wrapper/dists/gradle-9.7.1-bin/*/gradle-9.7.1/bin/gradle 2>/dev/null | head -1)}"
JDK21="${JDK21:-$HOME/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home}"

mkdir -p "$OUT" "$LOGS"
FAILED=()
BUILT=0

# run <tag> <project-dir> <gradle-cmd...>
run() {
  local tag="$1" dir="$2"; shift 2
  local loader="${tag%%:*}" mc="${tag#*:}"
  printf '%-28s ' "$tag"
  if (cd "$REPO/$dir" && "$@" > "$LOGS/$tag.log" 2>&1); then
    # Every project names its output the same way, and build/libs also holds jars from older
    # releases - so name the expected file exactly rather than globbing and picking a stale one.
    local jar="$REPO/$dir/build/libs/farlandsreforged-$VERSION+mc$mc-$loader.jar"
    if [ -f "$jar" ]; then
      cp "$jar" "$OUT/"; BUILT=$((BUILT+1)); echo "ok"
    else
      echo "BUILT BUT NO JAR"; FAILED+=("$tag (no jar)")
    fi
  else
    echo "FAILED  (see $LOGS/$tag.log)"; FAILED+=("$tag")
  fi
}

gradle_nc() { "$GRADLE_BIN" --no-daemon --console=plain "$@"; }

echo "=== Fabric 1.21 - 1.21.10 ==="
for v in 1.21 1.21.1 1.21.2 1.21.3 1.21.4 1.21.5 1.21.6 1.21.7 1.21.8 1.21.9 1.21.10; do
  run "fabric:$v" farlands-reforged-fabric-1.21 \
    bash -c "'$GRADLE_BIN' --no-daemon --console=plain clean build -x test \
      -Pminecraft_version=$v '-Pminecraft_version_range=$v' -Pmod_version=$VERSION+mc$v-fabric"
done

echo "=== Fabric 1.21.11 ==="
run "fabric:1.21.11" farlands-reforged-fabric-1.21.11 \
  bash -c "'$GRADLE_BIN' --no-daemon --console=plain clean build -x test -Pmod_version=$VERSION+mc1.21.11-fabric"

echo "=== NeoForge 1.21 - 1.21.10 ==="
nf_for() { case "$1" in
  1.21) echo "21.0.167 [21.0.0,21.1)";; 1.21.1) echo "21.1.251 [21.1.0,21.2)";;
  1.21.2) echo "21.2.1-beta [21.2.0-beta,21.3)";; 1.21.3) echo "21.3.97 [21.3.0,21.4)";;
  1.21.4) echo "21.4.157 [21.4.0,21.5)";; 1.21.5) echo "21.5.98 [21.5.0,21.6)";;
  1.21.6) echo "21.6.20-beta [21.6.0-beta,21.7)";; 1.21.7) echo "21.7.25-beta [21.7.0-beta,21.8)";;
  1.21.8) echo "21.8.54 [21.8.0,21.9)";; 1.21.9) echo "21.9.16-beta [21.9.0-beta,21.10)";;
  1.21.10) echo "21.10.64 [21.10.0,21.11)";; esac; }
for v in 1.21 1.21.1 1.21.2 1.21.3 1.21.4 1.21.5 1.21.6 1.21.7 1.21.8 1.21.9 1.21.10; do
  read -r nfv nfr <<< "$(nf_for "$v")"
  run "neoforge:$v" farlands-reforged-neoforge-1.21 \
    bash -c "'$GRADLE_BIN' --no-daemon --console=plain clean build -x test \
      -Pminecraft_version=$v '-Pminecraft_version_range=[$v]' \
      -Pneoforge_version=$nfv '-Pneoforge_version_range=$nfr' -Pmod_version=$VERSION+mc$v-neoforge"
done

echo "=== NeoForge 1.21.11 ==="
run "neoforge:1.21.11" farlands-reforged-neoforge-1.21.11 \
  bash -c "'$GRADLE_BIN' --no-daemon --console=plain clean build -x test -Pmod_version=$VERSION+mc1.21.11-neoforge"

echo "=== Forge 1.21 - 1.21.10 (no 1.21.2; Forge never shipped one) ==="
# Third field is the minimum Forge the jar declares. It is normally just the major, but Minecraft
# 1.21 is special: Forge builds before 51.0.23 bundle Mixin 0.8.5, which does not recognise the
# JAVA_21 compatibility level in farlandsreforged.mixins.json and dies during bootstrap. Declaring
# "[51,)" there would promise something that crashes on arrival.
fg_for() { case "$1" in
  1.21) echo "51.0.23 51 51.0.23";; 1.21.1) echo "52.1.16 52 52";; 1.21.3) echo "53.1.12 53 53";;
  1.21.4) echo "54.1.18 54 54";; 1.21.5) echo "55.1.13 55 55";; 1.21.6) echo "56.0.0 56 56";;
  1.21.7) echo "57.0.0 57 57";; 1.21.8) echo "58.1.22 58 58";; 1.21.9) echo "59.0.5 59 59";;
  1.21.10) echo "60.1.15 60 60";; esac; }
for v in 1.21 1.21.1 1.21.3 1.21.4 1.21.5 1.21.6 1.21.7 1.21.8 1.21.9 1.21.10; do
  read -r fv fm fmin <<< "$(fg_for "$v")"
  run "forge:$v" farlands-reforged-forge-1.21 \
    env JAVA_HOME="$JDK21" ./gradlew --no-daemon --console=plain clean build -x test \
      -Pminecraft_version="$v" "-Pminecraft_version_range=[$v]" \
      -Pforge_version="$fv" -Pforge_loader_major="$fm" -Pforge_version_min="$fmin" \
      -Pmod_version="$VERSION+mc$v-forge"
done

echo "=== Forge 1.21.11 ==="
run "forge:1.21.11" farlands-reforged-forge-1.21.11 \
  ./gradlew --no-daemon --console=plain clean build -x test -Pmod_version="$VERSION+mc1.21.11-forge"

echo "=== Fabric 26.x ==="
run "fabric:26.1.2" farlands-reforged-fabric-26.1.2 \
  bash -c "'$GRADLE_BIN' --no-daemon --console=plain clean build -x test -Pmod_version=$VERSION+mc26.1.2-fabric"
run "fabric:26.2" farlands-reforged-fabric-26.2 \
  bash -c "'$GRADLE_BIN' --no-daemon --console=plain clean build -x test -Pmod_version=$VERSION+mc26.2-fabric"
run "fabric:26.3" farlands-reforged-fabric-26.3 \
  bash -c "'$GRADLE_BIN' --no-daemon --console=plain clean build -x test -Pmod_version=$VERSION+mc26.3-fabric"

echo "=== NeoForge 26.x ==="
run "neoforge:26.1.2" farlands-reforged-neoforge-26.1.2 \
  bash -c "'$GRADLE_BIN' --no-daemon --console=plain clean build -x test -Pmod_version=$VERSION+mc26.1.2-neoforge"
run "neoforge:26.2" farlands-reforged-26.2 \
  bash -c "'$GRADLE_BIN' --no-daemon --console=plain clean build -x test -Pmod_version=$VERSION+mc26.2-neoforge"

echo "=== Forge 26.x ==="
# Forge numbers its major per Minecraft version, and mods.toml is built from the major alone, so each
# of these needs its own forge_version *and* forge_loader_major - 26.1 is Forge 62, not 65.
fx_for() { case "$1" in
  26.1)   echo "62.0.9 62 [26.1,26.1.1)";;
  26.1.1) echo "63.0.2 63 [26.1.1,26.1.2)";;
  26.1.2) echo "64.1.3 64 [26.1.2,26.2)";;
  26.2)   echo "65.0.0 65 [26.2,26.3)";; esac; }
for v in 26.1 26.1.1 26.1.2 26.2; do
  read -r fv fm fr <<< "$(fx_for "$v")"
  run "forge:$v" farlands-reforged-forge-26.2 \
    ./gradlew --no-daemon --console=plain clean build -x test \
      -Pminecraft_version="$v" "-Pminecraft_version_range=$fr" \
      -Pforge_version="$fv" -Pforge_loader_major="$fm" -Pmod_version="$VERSION+mc$v-forge"
done

echo
echo "=== Retarget 26.1 / 26.1.1 from the 26.1.2 builds ==="
python3 "$REPO/tools/retarget_jar.py" --fabric \
  "$OUT/farlandsreforged-$VERSION+mc26.1.2-fabric.jar" "$OUT/farlandsreforged-$VERSION+mc26.1-fabric.jar" \
  --mod-version "$VERSION+mc26.1-fabric" --minecraft '>=26.1 <26.1.1' && BUILT=$((BUILT+1))
python3 "$REPO/tools/retarget_jar.py" --fabric \
  "$OUT/farlandsreforged-$VERSION+mc26.1.2-fabric.jar" "$OUT/farlandsreforged-$VERSION+mc26.1.1-fabric.jar" \
  --mod-version "$VERSION+mc26.1.1-fabric" --minecraft '>=26.1.1 <26.1.2' && BUILT=$((BUILT+1))
python3 "$REPO/tools/retarget_jar.py" --neoforge \
  "$OUT/farlandsreforged-$VERSION+mc26.1.2-neoforge.jar" "$OUT/farlandsreforged-$VERSION+mc26.1-neoforge.jar" \
  --mod-version "$VERSION+mc26.1-neoforge" --minecraft '[26.1,26.1.1)' --loader '[26.1,26.1.1)' && BUILT=$((BUILT+1))
python3 "$REPO/tools/retarget_jar.py" --neoforge \
  "$OUT/farlandsreforged-$VERSION+mc26.1.2-neoforge.jar" "$OUT/farlandsreforged-$VERSION+mc26.1.1-neoforge.jar" \
  --mod-version "$VERSION+mc26.1.1-neoforge" --minecraft '[26.1.1,26.1.2)' --loader '[26.1.1,26.1.2)' && BUILT=$((BUILT+1))

echo
echo "=== $BUILT jars in $OUT ==="
if [ ${#FAILED[@]} -gt 0 ]; then
  printf 'FAILED: %s\n' "${FAILED[@]}"
  exit 1
fi
