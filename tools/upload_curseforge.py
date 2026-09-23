#!/usr/bin/env python3
"""Upload a release's jars to CurseForge.

Reads the API token from ~/.curseforge-token and never prints it. Defaults to a dry run: it resolves
every jar to its game-version ids and shows exactly what it would send, and uploads nothing until you
pass --go. A CurseForge upload cannot be undone from the API - a file can only be deprecated - so the
dry run is the default on purpose.

Each jar's Minecraft version and loader come from its filename, which the build guarantees is accurate:
tools/audit_release.py fails the release if a jar's filename and its internal metadata disagree.

Usage:
    upload_curseforge.py build-release --version 0.4.0 --changelog notes.md
    upload_curseforge.py build-release --version 0.4.0 --changelog notes.md --go
"""

import argparse
import json
import mimetypes
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

API = "https://minecraft.curseforge.com/api"
PROJECT_ID = 1583745
TOKEN_FILE = Path.home() / ".curseforge-token"

# The modloader tags live in the same "game versions" list as the Minecraft versions, under a separate
# type id. These are stable, and are checked against the live list before anything is uploaded.
LOADER_IDS = {"fabric": 7499, "neoforge": 10150, "forge": 7498}

# CurseForge also tags a file with the Java it needs, under its own type id, and people filter on it.
# Java 17 before 1.20.5, Java 21 through 1.21.11, Java 25 for 26.x - the same rule as server_test.java_for.
JAVA_TYPE_ID = 2

# CurseForge requires at least one tag from the "environment" group on every upload, and rejects the
# whole file with errorCode 1021 without it. This mod is worldgen plus a command, so it belongs on both
# sides: the terrain mixins run on the server, and the Fabric pack fix also registers the mod's assets
# as a client resource pack, which is what makes the advancement's title and description display.
ENVIRONMENT_TYPE_ID = 75208
ENVIRONMENTS = ("Client", "Server")


def java_for(mc):
    # This used to be "1.21 or else 25", which would have tagged every 1.18.2 - 1.20.6 jar as Java 25.
    parts = tuple(int(p) for p in mc.split("."))
    if parts[0] != 1:
        return "Java 25"
    return "Java 17" if parts < (1, 20, 5) else "Java 21"


def token():
    if not TOKEN_FILE.exists():
        sys.exit(f"no API token at {TOKEN_FILE}")
    return TOKEN_FILE.read_text().strip()


def api_get(path, api_token):
    request = urllib.request.Request(f"{API}{path}", headers={"X-Api-Token": api_token})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def multipart(fields, file_field, file_path):
    """Build a multipart/form-data body by hand.

    Worth doing rather than shelling out to curl: the metadata is JSON containing semicolons and quotes,
    and `curl -F` splits a value at the first `;`, which silently truncates it. (`--form-string` is the
    curl equivalent of getting this right.)
    """
    boundary = f"----farlands{uuid.uuid4().hex}"
    body = bytearray()
    for name, value in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += f"{value}\r\n".encode()

    content_type = mimetypes.guess_type(file_path.name)[0] or "application/java-archive"
    body += f"--{boundary}\r\n".encode()
    body += (f'Content-Disposition: form-data; name="{file_field}"; '
             f'filename="{file_path.name}"\r\n').encode()
    body += f"Content-Type: {content_type}\r\n\r\n".encode()
    body += file_path.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode()
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def parse_name(name, version):
    """farlandsreforged-<version>+mc<mc>-<loader>.jar -> (mc, loader)"""
    match = re.fullmatch(rf"farlandsreforged-{re.escape(version)}\+mc(.+)-(fabric|neoforge|forge)\.jar", name)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--version", required=True)
    ap.add_argument("--changelog", type=Path, required=True)
    ap.add_argument("--release-type", default="release", choices=["release", "beta", "alpha"])
    ap.add_argument("--exclude", nargs="*", default=[], help="filenames to skip")
    ap.add_argument("--go", action="store_true", help="actually upload (default is a dry run)")
    args = ap.parse_args()

    api_token = token()
    changelog = args.changelog.read_text()

    versions = api_get("/game/versions", api_token)
    # A Minecraft version name is not unique: "1.20" exists as a Minecraft version, as an "Addons" version
    # (type 615) and under a hidden type 1. Only types whose slug is minecraft-<family> ("Minecraft 1.20",
    # or "26.2" with slug minecraft-26-2) are Minecraft versions. Taking the first match instead would have
    # filed the 1.20 jars under Addons 1.20, because that is the entry CurseForge happens to list first.
    minecraft_types = {t["id"] for t in api_get("/game/version-types", api_token)
                       if t["slug"].startswith("minecraft-") and "snapshot" not in t["slug"]}
    by_name = {}
    for entry in versions:
        by_name.setdefault(entry["name"], []).append(entry)

    # Confirm the hard-coded loader ids still say what we think they do.
    by_id = {entry["id"]: entry for entry in versions}
    for loader, ident in LOADER_IDS.items():
        found = by_id.get(ident)
        if not found or found["name"].lower() != loader:
            sys.exit(f"loader id {ident} is {found['name'] if found else 'missing'}, expected {loader}")

    jars = sorted(Path(args.directory).glob("*.jar"))
    plan, problems = [], []
    for jar in jars:
        if jar.name in args.exclude:
            continue
        mc, loader = parse_name(jar.name, args.version)
        if mc is None:
            problems.append(f"{jar.name}: cannot parse a Minecraft version and loader from the name")
            continue
        candidates = [e for e in by_name.get(mc, []) if e["gameVersionTypeID"] in minecraft_types]
        if not candidates:
            problems.append(f"{jar.name}: CurseForge has no game version called {mc!r} yet")
            continue
        if len(candidates) > 1:
            # Never guess: a wrong game-version tag is public and puts the file under the wrong version.
            problems.append(f"{jar.name}: {mc!r} is ambiguous on CurseForge: "
                            f"{[(e['id'], e['gameVersionTypeID']) for e in candidates]}")
            continue

        java_name = java_for(mc)
        java = [e for e in by_name.get(java_name, []) if e["gameVersionTypeID"] == JAVA_TYPE_ID]
        if not java:
            problems.append(f"{jar.name}: CurseForge has no {java_name} tag")
            continue

        environment = [e["id"] for name in ENVIRONMENTS
                       for e in by_name.get(name, [])
                       if e["gameVersionTypeID"] == ENVIRONMENT_TYPE_ID]
        if len(environment) != len(ENVIRONMENTS):
            problems.append(f"{jar.name}: could not resolve the environment tags "
                            f"{', '.join(ENVIRONMENTS)}")
            continue

        plan.append({
            "jar": jar,
            "displayName": f"Farlands Reforged {args.version} — Minecraft {mc} ({loader.capitalize()})",
            "gameVersions": sorted({candidates[0]["id"], LOADER_IDS[loader], java[0]["id"],
                                    *environment}),
            "mc": mc, "loader": loader, "java": java_name,
        })

    for problem in problems:
        print(f"  ! {problem}")
    print(f"\n{len(plan)} jars ready, {len(problems)} problems\n")
    for item in plan:
        print(f"  {item['jar'].name:52} mc={item['mc']:8} {item['loader']:9} "
              f"{item['java']:8} ids={item['gameVersions']}")

    if problems:
        sys.exit("\nrefusing to upload while any jar is unresolved")
    if not args.go:
        print("\nDry run. Re-run with --go to upload.")
        return 0

    uploaded, failed = [], []
    for index, item in enumerate(plan, 1):
        metadata = {
            "changelog": changelog,
            "changelogType": "markdown",
            "displayName": item["displayName"],
            "gameVersions": item["gameVersions"],
            "releaseType": args.release_type,
        }
        body, content_type = multipart({"metadata": json.dumps(metadata)}, "file", item["jar"])
        request = urllib.request.Request(
            f"{API}/projects/{PROJECT_ID}/upload-file", data=body,
            headers={"X-Api-Token": api_token, "Content-Type": content_type},
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                result = json.load(response)
            file_id = result.get("id")
            uploaded.append((item["jar"].name, file_id))
            print(f"[{index}/{len(plan)}] {item['jar'].name} -> file id {file_id}")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            failed.append((item["jar"].name, f"{exc.code} {detail}"))
            print(f"[{index}/{len(plan)}] {item['jar'].name} FAILED: {exc.code} {detail}")
        except urllib.error.URLError as exc:
            failed.append((item["jar"].name, str(exc)))
            print(f"[{index}/{len(plan)}] {item['jar'].name} FAILED: {exc}")
        time.sleep(2)  # be gentle; the upload API rate-limits

    print(f"\nuploaded {len(uploaded)}, failed {len(failed)}")
    if uploaded:
        ids = [str(file_id) for _, file_id in uploaded if file_id]
        print(f"file ids: {', '.join(ids)}")
    for name, why in failed:
        print(f"  FAILED {name}: {why}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
