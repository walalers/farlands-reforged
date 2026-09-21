#!/usr/bin/env python3
"""Read Minecraft region files directly, to compare generated terrain between two worlds.

The point of this mod is terrain, and the only honest way to check terrain is to look at the blocks a
real server wrote. This reads Anvil region files without Minecraft, so a generated world can be diffed
against a reference world block for block.

What experience says to compare: the **solid / fluid / air** shape, not exact block ids. Two servers on
the same seed and different Minecraft versions legitimately disagree about vegetation - seagrass, short
grass, sugar cane, the odd dirt-vs-grass_block - because vanilla changes feature placement between
versions. A difference in the stone and water shape is the mod's problem; a difference in flowers is not.

Two layout details that have cost time before:

  * Overworld regions live in `world/region/` in the 1.21 family, but in
    `world/dimensions/minecraft/overworld/region/` in 26.x. Both are checked.
  * Palette entries come in three shapes: a plain string, `{"": name}`, or
    `{"id": name, "properties": {...}}`.

Usage:
    region_slice.py <world-dir> --x 12550760 12550900 --z -8 8 --y 40 200 --json out.json
    region_slice.py --diff a.json b.json
"""

import argparse
import gzip
import json
import struct
import sys
import zlib
from pathlib import Path

SECTOR = 4096

TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG = 0, 1, 2, 3, 4
TAG_FLOAT, TAG_DOUBLE, TAG_BYTE_ARRAY, TAG_STRING = 5, 6, 7, 8
TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 9, 10, 11, 12

AIR = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}
FLUID = {"minecraft:water", "minecraft:lava", "minecraft:flowing_water", "minecraft:flowing_lava"}


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, count):
        chunk = self.data[self.pos:self.pos + count]
        self.pos += count
        return chunk

    def number(self, fmt):
        size = struct.calcsize(fmt)
        return struct.unpack(">" + fmt, self.take(size))[0]

    def string(self):
        return self.take(self.number("H")).decode("utf-8", "replace")

    def payload(self, kind):
        if kind == TAG_BYTE:
            return self.number("b")
        if kind == TAG_SHORT:
            return self.number("h")
        if kind == TAG_INT:
            return self.number("i")
        if kind == TAG_LONG:
            return self.number("q")
        if kind == TAG_FLOAT:
            return self.number("f")
        if kind == TAG_DOUBLE:
            return self.number("d")
        if kind == TAG_BYTE_ARRAY:
            return self.take(self.number("i"))
        if kind == TAG_STRING:
            return self.string()
        if kind == TAG_LIST:
            item_kind, count = self.number("b"), self.number("i")
            return [self.payload(item_kind) for _ in range(max(count, 0))]
        if kind == TAG_COMPOUND:
            out = {}
            while True:
                item_kind = self.number("b")
                if item_kind == TAG_END:
                    return out
                # The name comes before the payload on the wire, so it has to be read first -
                # writing `out[self.string()] = self.payload(...)` reads them the wrong way round,
                # because Python evaluates the right-hand side before the subscript.
                name = self.string()
                out[name] = self.payload(item_kind)
        if kind == TAG_INT_ARRAY:
            return [self.number("i") for _ in range(self.number("i"))]
        if kind == TAG_LONG_ARRAY:
            return [self.number("q") for _ in range(self.number("i"))]
        raise ValueError(f"unknown NBT tag {kind}")

    def root(self):
        kind = self.number("b")
        if kind != TAG_COMPOUND:
            raise ValueError(f"expected a root compound, got tag {kind}")
        self.string()  # the root name, always empty in practice
        return self.payload(TAG_COMPOUND)


def palette_name(entry):
    """Palette entries come in three shapes depending on version and whether they have properties."""
    if isinstance(entry, str):
        return entry
    return entry.get("Name") or entry.get("id") or entry.get("") or "minecraft:air"


def region_dirs(world):
    world = Path(world)
    return [world / "region", world / "dimensions/minecraft/overworld/region"]


def read_region(path):
    """Yield (chunk_x, chunk_z, nbt) for every chunk present in one .mca file."""
    raw = path.read_bytes()
    if len(raw) < 2 * SECTOR:
        return
    region_x, region_z = (int(part) for part in path.stem.split(".")[1:3])

    for index in range(1024):
        offset, sectors = struct.unpack(">I", b"\x00" + raw[index * 4:index * 4 + 3])[0], raw[index * 4 + 3]
        if offset == 0 or sectors == 0:
            continue
        start = offset * SECTOR
        if start + 5 > len(raw):
            continue
        length, compression = struct.unpack(">IB", raw[start:start + 5])
        blob = raw[start + 5:start + 4 + length]
        try:
            if compression == 1:
                blob = gzip.decompress(blob)
            elif compression == 2:
                blob = zlib.decompress(blob)
            elif compression != 3:
                continue
            nbt = Reader(blob).root()
        except (zlib.error, OSError, ValueError, struct.error):
            continue
        yield region_x * 32 + (index % 32), region_z * 32 + (index // 32), nbt


def chunk_blocks(nbt):
    """Return {(x, y, z): block_name} in world coordinates for one chunk."""
    blocks = {}
    chunk_x, chunk_z = nbt.get("xPos", 0) * 16, nbt.get("zPos", 0) * 16

    for section in nbt.get("sections", []):
        states = section.get("block_states")
        if not states:
            continue
        palette = [palette_name(entry) for entry in states.get("palette", [])]
        if not palette:
            continue
        base_y = section.get("Y", 0) * 16

        data = states.get("data")
        if not data:
            # A section with a one-entry palette stores no data at all: it is uniformly that block.
            if palette[0] not in AIR:
                for index in range(4096):
                    blocks[(chunk_x + (index & 15), base_y + (index >> 8), chunk_z + ((index >> 4) & 15))] = palette[0]
            continue

        bits = max(4, (len(palette) - 1).bit_length())
        per_long = 64 // bits
        mask = (1 << bits) - 1
        for index in range(4096):
            # Since 1.16 an entry never straddles two longs; the spare high bits are simply unused.
            long_index, offset = divmod(index, per_long)
            if long_index >= len(data):
                break
            value = (data[long_index] >> (offset * bits)) & mask
            if value < len(palette):
                blocks[(chunk_x + (index & 15), base_y + (index >> 8), chunk_z + ((index >> 4) & 15))] = palette[value]
    return blocks


def classify(name):
    if name in AIR:
        return "a"
    if name in FLUID:
        return "f"
    return "s"


def sample(world, x_range, z_range, y_range):
    """Collect {"x,y,z": block} for every block in the box that the world actually has."""
    x0, x1 = x_range
    z0, z1 = z_range
    y0, y1 = y_range
    wanted_chunks = {(cx, cz)
                     for cx in range(x0 >> 4, (x1 >> 4) + 1)
                     for cz in range(z0 >> 4, (z1 >> 4) + 1)}

    out = {}
    for directory in region_dirs(world):
        if not directory.is_dir():
            continue
        for region in sorted(directory.glob("r.*.mca")):
            for chunk_x, chunk_z, nbt in read_region(region):
                if (chunk_x, chunk_z) not in wanted_chunks:
                    continue
                for (x, y, z), name in chunk_blocks(nbt).items():
                    if x0 <= x <= x1 and z0 <= z <= z1 and y0 <= y <= y1:
                        out[f"{x},{y},{z}"] = name
    return out


def diff(left, right):
    """Compare two samples by solid/fluid/air shape, and separately by exact block id."""
    keys = set(left) & set(right)
    shape, exact, examples = 0, 0, []
    for key in sorted(keys):
        if left[key] != right[key]:
            exact += 1
            if classify(left[key]) != classify(right[key]):
                shape += 1
                if len(examples) < 10:
                    examples.append(f"{key}: {left[key]} vs {right[key]}")
    return {
        "compared": len(keys),
        "only_in_left": len(set(left) - set(right)),
        "only_in_right": len(set(right) - set(left)),
        "shape_differences": shape,
        "exact_differences": exact,
        "examples": examples,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("world", nargs="?")
    ap.add_argument("--x", nargs=2, type=int, default=[12550760, 12550900])
    ap.add_argument("--z", nargs=2, type=int, default=[-8, 8])
    ap.add_argument("--y", nargs=2, type=int, default=[40, 200])
    ap.add_argument("--json", type=Path, help="write the sample here")
    ap.add_argument("--diff", nargs=2, type=Path, help="compare two previously written samples")
    args = ap.parse_args()

    if args.diff:
        left = json.loads(args.diff[0].read_text())
        right = json.loads(args.diff[1].read_text())
        report = diff(left, right)
        print(json.dumps(report, indent=2))
        return 1 if report["shape_differences"] else 0

    if not args.world:
        ap.error("a world directory is required unless --diff is used")

    blocks = sample(args.world, args.x, args.z, args.y)
    print(f"{len(blocks)} blocks sampled from {args.world}")
    if args.json:
        args.json.write_text(json.dumps(blocks))
        print(f"written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
