#!/usr/bin/env python3
"""Check that every loader method and field a mod jar calls exists in a given loader version.

`verify_injections.py` and `verify_pack_api.py` check the Minecraft side. This checks the other side:
the NeoForge / FancyModLoader / event-bus API the mod's own code calls. It matters most for a jar that
is built once and retargeted to other loader versions, because the compiler only ever saw one of them.

It was written after exactly that went wrong. The NeoForge 1.20.4 jar was retargeted to 20.2 and 20.3
after checking that every NeoForge *class* it uses exists there - and they all do. But
`ModConfigSpec.BooleanValue.getAsBoolean()` only arrives in 20.4, so on 20.2 and 20.3 the server died
during mod loading with a NoSuchMethodError. Classes are not enough; this resolves every member
reference, with its exact descriptor, through the class hierarchy.

Usage:
    verify_loader_api.py <mod.jar> --neoforge 20.2.86 [--neoforge 20.3.1-beta ...]
    verify_loader_api.py <mod.jar> --classpath a.jar b.jar ...

With --neoforge, the loader's jars are downloaded (and cached) from maven.neoforged.net: the
universal jar plus every net.neoforged dependency its POM names (FancyModLoader, the event bus...).
"""

import argparse
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

MAVEN = "https://maven.neoforged.net/releases"
CACHE = Path.home() / ".cache/farlands-server-test/loader-api"
# Only these packages are the loader's; java.* and net.minecraft.* are someone else's problem.
PREFIXES = ("net/neoforged/",)
REF = re.compile(r"// (Method|InterfaceMethod|Field) ([\w/$]+)\.([\w<>$]+):(\S+)")


def fetch(url, dest):
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=120) as response:
            dest.write_bytes(response.read())
    return dest


def neoforge_classpath(version):
    base = f"{MAVEN}/net/neoforged/neoforge/{version}/neoforge-{version}"
    jars = [fetch(f"{base}-universal.jar", CACHE / f"neoforge-{version}-universal.jar")]
    pom = ET.fromstring(fetch(f"{base}.pom", CACHE / f"neoforge-{version}.pom").read_bytes())
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    for dep in pom.iterfind(".//m:dependency", ns):
        group = dep.findtext("m:groupId", "", ns)
        artifact, ver = dep.findtext("m:artifactId", "", ns), dep.findtext("m:version", "", ns)
        if not group.startswith("net.neoforged") or not ver or "$" in ver:
            continue
        path = f"{group.replace('.', '/')}/{artifact}/{ver}/{artifact}-{ver}.jar"
        try:
            jars.append(fetch(f"{MAVEN}/{path}", CACHE / f"{artifact}-{ver}.jar"))
        except OSError:
            pass  # test-only or platform artifacts that were never published as plain jars
    return jars


def references(mod_jar):
    """Every loader member the mod's classes reference: {(owner, name, descriptor, kind)}."""
    names = subprocess.run(["unzip", "-Z1", str(mod_jar)], capture_output=True, text=True).stdout
    classes = [n[:-6].replace("/", ".") for n in names.split() if n.endswith(".class")]
    out = subprocess.run(["javap", "-c", "-p", "-cp", str(mod_jar)] + classes,
                         capture_output=True, text=True).stdout
    return {(owner, name, desc, kind) for kind, owner, name, desc in REF.findall(out)
            if owner.startswith(PREFIXES)}


class Hierarchy:
    """Members and supertypes of loader classes, read with javap from the given classpath."""

    def __init__(self, classpath):
        self.cp = ":".join(str(j) for j in classpath)
        self.cache = {}

    def load(self, owner):
        if owner not in self.cache:
            result = subprocess.run(["javap", "-p", "-s", "-cp", self.cp, owner.replace("/", ".")],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                self.cache[owner] = None
            else:
                lines = result.stdout.splitlines()
                header = next((l for l in lines if re.search(r"\b(class|interface)\b", l)), "")
                supers = re.findall(r"(?:extends|implements)\s+([\w.$<>, ?]+?)(?=\s+implements|\s*\{|$)", header)
                parents = [re.sub(r"<.*", "", p).strip().replace(".", "/")
                           for group in supers for p in re.split(r",\s*(?![^<]*>)", group)]
                simple = owner.split("/")[-1]
                members = set()
                for decl, desc in zip(lines, lines[1:]):
                    if not desc.strip().startswith("descriptor:"):
                        continue
                    method = re.search(r"([\w$]+)\(", decl)
                    field = re.search(r"([\w$]+);$", decl.strip())
                    name = (("<init>" if method.group(1) == simple else method.group(1)) if method
                            else field.group(1) if field else None)
                    if name:
                        members.add((name, desc.split("descriptor:")[1].strip()))
                self.cache[owner] = (members, [p for p in parents if p])
        return self.cache[owner]

    def has(self, owner, name, desc, seen=None):
        """Whether owner, or anything it extends or implements, declares name+desc.

        Supertypes outside the loader - JDK interfaces such as BooleanSupplier - are read too, rather
        than assumed to supply whatever is being looked for. Assuming it once let
        `BooleanValue.getAsBoolean()` pass on NeoForge 20.2, where BooleanValue implements Supplier but
        not BooleanSupplier and the method does not exist.
        """
        seen = set() if seen is None else seen
        if owner in seen:
            return False
        seen.add(owner)
        info = self.load(owner)
        if info is None:
            return False
        members, parents = info
        if (name, desc) in members:
            return True
        return any(self.has(p, name, desc, seen) for p in parents)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jar", type=Path)
    ap.add_argument("--neoforge", action="append", default=[], metavar="VERSION")
    ap.add_argument("--classpath", nargs="+", type=Path)
    args = ap.parse_args()

    refs = references(args.jar)
    targets = [(f"NeoForge {v}", neoforge_classpath(v)) for v in args.neoforge]
    if args.classpath:
        targets.append(("classpath", args.classpath))
    if not targets:
        sys.exit("give --neoforge VERSION or --classpath JARS")

    worst = 0
    for label, classpath in targets:
        hierarchy = Hierarchy(classpath)
        missing = sorted(r for r in refs if not hierarchy.has(*r[:3]))
        if missing:
            worst = 1
            print(f"FAIL {label}: {len(missing)} of {len(refs)} loader references missing")
            for owner, name, desc, kind in missing:
                print(f"       {kind} {owner.replace('/', '.')}.{name}{desc}")
        else:
            print(f"ok   {label}: all {len(refs)} loader references resolve")
    return worst


if __name__ == "__main__":
    sys.exit(main())
