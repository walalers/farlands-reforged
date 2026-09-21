#!/usr/bin/env bash
# Launch a Minecraft client with the mod, wait for it to reach the title screen, and check the log.
#
#   tools/client_test.sh <project-dir> [seconds-to-wait]
#
# Everything this mod has ever been tested on is a dedicated server, which leaves one real gap: the
# Fabric data-pack fix adds its pack to *every* PackRepository, and on a client one of those is the
# resource-pack repository. That path has never run.
#
# Conveniently the client names every pack it loads, so the log answers the question directly:
#
#     Reloading ResourceManager: vanilla, farlandsreforged
#
# If `farlandsreforged` is in that list the mod's assets - the advancement's title and description - are
# reaching the client. If the list says only `vanilla`, they are not.
#
# This opens a real Minecraft window. It is killed once the title screen is up.
set -uo pipefail

PROJECT="${1:?usage: client_test.sh <project-dir> [seconds]}"
WAIT="${2:-240}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GRADLE_BIN="${GRADLE_BIN:-$(ls -d "$HOME"/.gradle/wrapper/dists/gradle-9.7.1-bin/*/gradle-9.7.1/bin/gradle 2>/dev/null | head -1)}"
LOG="${CLIENT_LOG:-/tmp/farlands-client-$(basename "$PROJECT").log}"

cd "$REPO/$PROJECT" || exit 1
if [ -x ./gradlew ]; then RUNNER=(./gradlew); else RUNNER=("$GRADLE_BIN"); fi

echo "launching client for $PROJECT (log: $LOG)"
"${RUNNER[@]}" --no-daemon --console=plain runClient > "$LOG" 2>&1 &
GRADLE_PID=$!

# "Sound engine started" and the LWJGL/OpenAL lines are the last things before the title screen; a
# client that dies during mixin application never reaches any of them.
READY=0
for _ in $(seq 1 "$WAIT"); do
  if grep -qE "Sound engine started|OpenAL initialized|Created: .*texture" "$LOG" 2>/dev/null; then READY=1; break; fi
  if grep -qE "Mixin apply failed|MixinApplyError|Critical injection failure|A problem occurred|BUILD FAILED" "$LOG" 2>/dev/null; then break; fi
  if ! kill -0 "$GRADLE_PID" 2>/dev/null; then break; fi
  sleep 1
done

echo
if [ "$READY" = 1 ]; then echo "RESULT: client reached the title screen"; else echo "RESULT: client did NOT reach the title screen"; fi

echo
echo "--- resource packs the client loaded ---"
grep -h "Reloading ResourceManager" "$LOG" | tail -3 | sed 's/^/  /'
if grep -q "Reloading ResourceManager:.*farlandsreforged" "$LOG"; then
  echo "  => farlandsreforged IS loaded as a client resource pack"
else
  echo "  => farlandsreforged is NOT in the client's pack list"
fi

echo
echo "--- mixin / load errors ---"
if grep -hE "Mixin apply failed|MixinApplyError|Critical injection failure|InvalidInjectionException|was not located in the target class" "$LOG" | head -5 | sed 's/^/  /' | grep .; then
  echo "  (errors above)"
else
  echo "  none"
fi

# Gradle keeps the JVM alive; kill the whole process group. A plain TERM is ignored while it is busy.
pkill -9 -f "net.fabricmc.devlaunchinjector" 2>/dev/null
pkill -9 -f "net.minecraft.client.main.Main" 2>/dev/null
kill -9 "$GRADLE_PID" 2>/dev/null
wait "$GRADLE_PID" 2>/dev/null
echo
echo "client stopped; full log at $LOG"
