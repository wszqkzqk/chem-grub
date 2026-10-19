#!/usr/bin/env python3
# Copyright (C) 2026 Zhou Qiankang <wszqkzqk@qq.com>
# SPDX-License-Identifier: GPL-2.0-or-later
import argparse
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from functools import lru_cache
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src"
BUILD = ROOT / ".build"
OUT = ROOT / "dist" / "chem-grub"
ARCHIVE = ROOT / "dist" / "chem-grub.zip"
RESAMPLE = Image.Resampling.LANCZOS
FONT_SPECS = ((20, "NotoSansMonoCJKsc-Regular-20.pf2"), (18, "NotoSansMonoCJKsc-Regular-18.pf2"))

ROOT_ENTRIES = [
    ("Arch Linux", "arch"),
    ("Advanced options for Arch Linux", "submenu"),
    ("Arch Linux Btrfs snapshots", "snapshots"),
    ("Ubuntu 24.04 LTS", "ubuntu"),
    ("Debian GNU/Linux 13 (trixie)", "debian"),
    ("Windows 11 (on /dev/nvme0n1p1)", "windows"),
    ("UEFI Firmware Settings", "uefi"),
    ("Memory test", "memtest"),
    ("System recovery", "recovery"),
    ("Restart", "reboot"),
    ("Shutdown", "shutdown"),
]

BILINGUAL_ENTRIES = [
    ("Arch Linux / 启动 Arch Linux", "arch"),
    ("Advanced options for Arch Linux / 高级选项", "submenu"),
    ("Arch Linux snapshots / Btrfs 快照", "snapshots"),
    ("UEFI Firmware Settings / 固件设置", "uefi"),
]

SNAPSHOT_ENTRIES = [
    ("vmlinuz-linux & initramfs-linux.img", "snapshots"),
    ("vmlinuz-linux-lts & initramfs-linux-lts.img", "snapshots"),
    ("vmlinuz-linux-zen & initramfs-linux-zen.img", "snapshots"),
    ("vmlinuz-linux & initramfs-linux.img & intel-ucode.img", "snapshots"),
    ("快照 2026-10-19 · linux-lts · 自动备份", "snapshots"),
    ("Snapshot 2026-10-18 / 中文测试快照", "snapshots"),
    ("vmlinuz-linux-hardened & initramfs-linux-hardened.img", "snapshots"),
    ("vmlinuz-linux & initramfs-linux-fallback.img", "snapshots"),
    ("快照 2026-10-17 · linux-zen · 系统更新前", "snapshots"),
    ("vmlinuz-linux-lts & initramfs-linux-lts-fallback.img", "snapshots"),
    ("Snapshot 2026-10-16 / linux / read-only", "snapshots"),
    ("快照 2026-10-15 · linux · 手动备份", "snapshots"),
    ("vmlinuz-linux-zen & intel-ucode.img", "snapshots"),
    ("Snapshot 2026-10-14 / linux-lts", "snapshots"),
]

ARCH_ENTRIES = [
    ("Arch Linux, with Linux linux", "arch"),
    ("Arch Linux, with Linux linux (fallback initramfs)", "arch"),
    ("Arch Linux, with Linux linux-lts", "arch"),
    ("Arch Linux, with Linux linux-lts (fallback initramfs)", "arch"),
    ("Arch Linux, with Linux linux-zen", "arch"),
    ("Arch Linux, with Linux linux-zen (fallback initramfs)", "arch"),
    ("Arch Linux, with Linux linux-hardened", "arch"),
    ("Arch Linux, with Linux linux-hardened (fallback initramfs)", "arch"),
    ("Arch Linux 高级选项（多内核与回滚）", "submenu"),
]

ICON_ART = {
    "arch": '<path d="M16 4 4 27h7l5-12 5 12h7L16 4Zm0 10-2 4h4l-2-4Z" fill="#c8ecb6" fill-rule="evenodd" stroke="none"/>',
    "linux": '<ellipse cx="16" cy="16" rx="8" ry="10" fill="#c4e7b4" stroke="none"/><ellipse cx="16" cy="19" rx="5" ry="7" fill="#143832" stroke="none"/><circle cx="13" cy="12" r="1.3" fill="#143832" stroke="none"/><circle cx="19" cy="12" r="1.3" fill="#143832" stroke="none"/><path d="m14 15 2 2 2-2" stroke="#efad69"/><path d="m11 25-4 2m14-2 4 2"/>',
    "debian": '<path d="M23 9C16 3 7 8 9 16c2 8 14 9 16 2 2-6-6-10-10-6-4 4 1 9 5 6 3-2 0-6-3-4"/>',
    "ubuntu": '<circle cx="16" cy="16" r="8"/><circle cx="16" cy="5" r="3" fill="#c4e7b4"/><circle cx="6.5" cy="21.5" r="3" fill="#c4e7b4"/><circle cx="25.5" cy="21.5" r="3" fill="#c4e7b4"/><path d="M16 8v3M9 20l3-1m11 1 3 1"/>',
    "fedora": '<path d="M10 26V15c0-6 3-9 9-9h5M10 17h12M17 26v-9h8"/>',
    "manjaro": '<path d="M6 26V6h6v20zm9 0V11h6v15zm9 0V16h5v10z" fill="#c4e7b4" stroke="none"/>',
    "nixos": '<path d="M16 4v24M5.6 10l20.8 12M5.6 22 26.4 10"/><path d="m16 4 3 5-3 2-3-2zm0 24 3-5-3-2-3 2z" fill="#70ddbd"/>',
    "suse": '<path d="M6 23C5 12 14 5 26 6c1 12-6 20-17 19M9 23 23 9"/>',
    "void": '<path d="m16 4 12 12-12 12L4 16 16 4Zm0 6 6 6-6 6-6-6 6-6Z" fill="#c4e7b4" fill-rule="evenodd" stroke="none"/>',
    "windows": '<path d="m5 8 10-1v9H5V8Zm12-1 10-1v10h-10V7ZM5 18h10v9l-10-1v-8Zm12 0h10v10l-10-1v-9Z" fill="#c4e7b4" stroke="none"/>',
    "apple": '<path d="M20 13c-2-2-5-2-7 0-2-1-5-1-7 2-3 5 2 13 6 13 2 0 3-1 5-1s3 1 5 0c2-1 4-5 4-8-3-1-5-4-6-6Z" fill="#c4e7b4" stroke="none"/><path d="M16 10c0-4 3-7 7-7-1 4-3 6-7 7Z" fill="#70ddbd" stroke="none"/><path d="M23 14c2 1 3 3 3 5-2 0-4-1-5-3"/>',
    "bsd": '<path d="m11 12-5-8 9 5m6 3 5-8-9 5"/><circle cx="16" cy="18" r="9"/><circle cx="13" cy="17" r="1" fill="#c4e7b4"/><circle cx="20" cy="17" r="1" fill="#c4e7b4"/><path d="M13 22h6"/>',
    "snapshots": '<path d="m4 11 12-6 12 6-12 6-12-6Zm1 6 11 6 11-6M5 22l11 6 11-6"/>',
    "btrfs": '<ellipse cx="16" cy="8" rx="11" ry="4"/><path d="M5 8v8c0 5 22 5 22 0V8M5 16v8c0 5 22 5 22 0v-8M11 21h10"/>',
    "submenu": '<path d="M6 8h11M6 15h9M6 22h7m7-13 6 7-6 7"/>',
    "advanced": '<path d="M5 8h22M5 16h22M5 24h22"/><circle cx="12" cy="8" r="3" fill="#143832"/><circle cx="22" cy="16" r="3" fill="#143832"/><circle cx="15" cy="24" r="3" fill="#143832"/>',
    "recovery": '<path d="M9 11a9 9 0 1 1-1 11M9 5v6H3"/><path d="M16 12v10m-5-5h10"/>',
    "memtest": '<rect x="7" y="8" width="18" height="16" rx="2"/><rect x="11" y="12" width="10" height="8" rx="1"/><path d="M10 4v4m6-4v4m6-4v4M10 24v4m6-4v4m6-4v4M3 12h4m-4 5h4m-4 5h4m18-10h4m-4 5h4m-4 5h4"/>',
    "reboot": '<path d="M9 10a9 9 0 1 1-1 11M9 4v6H3"/>',
    "shutdown": '<path d="M16 4v12M10 8a11 11 0 1 0 12 0"/>',
    "uefi": '<rect x="6" y="6" width="20" height="20" rx="4"/><path d="M11 12v7c0 3 5 3 5 0v-7m3 0v9m0-9h5m-5 4h4m-4 5h5M3 11h3m-3 6h3m-3 6h3m20-12h3m-3 6h3m-3 6h3"/>',
    "android": '<path d="m11 9-3-5m13 5 3-5M8 13a8 8 0 0 1 16 0v10H8V13Zm0 2H5v8h3m16-10h3v8h-3M12 23v5m8-5v5"/><circle cx="12" cy="12" r="1" fill="#c4e7b4"/><circle cx="20" cy="12" r="1" fill="#c4e7b4"/>',
    "generic": '<path d="M12 4h8m-6 0v8L7 24c-1 2 0 4 3 4h13c3 0 4-2 2-4l-7-12V4M10 21h13"/><circle cx="16" cy="24" r="1.5" fill="#c4e7b4"/><circle cx="21" cy="18" r="1" fill="#c4e7b4"/>',
}

ICON_ALIASES = {
    "arch": ["arch", "archlinux", "linux-lts", "linux-zen", "linux-hardened"],
    "linux": ["linux", "gnu-linux", "gnu"],
    "debian": ["debian", "raspbian", "linuxmint", "mint"],
    "ubuntu": ["ubuntu", "kubuntu", "xubuntu", "lubuntu", "pop", "pop-os", "zorin", "elementary"],
    "fedora": ["fedora", "centos", "rhel", "rocky", "almalinux"],
    "manjaro": ["manjaro"],
    "nixos": ["nixos"],
    "suse": ["suse", "opensuse", "opensuse-tumbleweed", "sles"],
    "void": ["void"],
    "windows": ["windows", "windows7", "windows8", "windows10", "windows11", "win"],
    "apple": ["osx", "macos", "macosx", "darwin"],
    "bsd": ["freebsd", "netbsd", "openbsd"],
    "snapshots": ["snapshots", "snapshot", "grub-btrfs", "timeshift", "snapper"],
    "btrfs": ["btrfs"],
    "submenu": ["submenu"],
    "advanced": ["advanced", "options", "settings"],
    "recovery": ["recovery"],
    "memtest": ["memtest", "memtest86", "memtest86+"],
    "reboot": ["reboot", "restart"],
    "shutdown": ["shutdown", "poweroff", "halt"],
    "uefi": ["uefi", "efi", "firmware"],
    "android": ["android", "bliss", "lineageos"],
    "generic": ["os", "unknown", "fallback", "gentoo", "chromeos", "haiku"],
}


def run(command, **kwargs):
    result = subprocess.run(command, capture_output=True, **kwargs)
    if result.returncode:
        sys.stderr.write(result.stderr.decode("utf-8", "replace"))
        raise RuntimeError(f"Command failed: {' '.join(map(str, command))}")
    return result


def prepare_fontconfig():
    font_dir = BUILD / "fonts"
    cache_dir = BUILD / "font-cache"
    font_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    variable = TTFont(SOURCE / "fonts" / "SpaceGrotesk-variable.ttf")
    for weight, name in ((500, "Medium"), (700, "Bold")):
        instance = instantiateVariableFont(variable, {"wght": weight}, updateFontNames=True)
        instance.save(font_dir / f"SpaceGrotesk-{name}.ttf")
    variable.close()
    for name in ("IBMPlexMono-Regular.ttf", "NotoSansMonoCJKsc-Regular.otf"):
        shutil.copy2(SOURCE / "fonts" / name, font_dir / name)
    includes = "\n".join(
        f'<include ignore_missing="yes">{path}</include>'
        for path in ("/etc/fonts/fonts.conf", "/opt/homebrew/etc/fonts/fonts.conf", "/usr/local/etc/fonts/fonts.conf")
    )
    config = BUILD / "fonts.conf"
    config.write_text(
        f'<?xml version="1.0"?><fontconfig>{includes}<dir>{font_dir}</dir><cachedir>{cache_dir}</cachedir></fontconfig>',
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["FONTCONFIG_FILE"] = str(config)
    env["XDG_CACHE_HOME"] = str(BUILD / "cache")
    return env


def render_svg(source, output, width, height, env, svg=None):
    output.parent.mkdir(parents=True, exist_ok=True)
    command = ["rsvg-convert", "-w", str(width), "-h", str(height), "-o", str(output)]
    if source is not None:
        command.append(str(source))
    run(command, input=svg.encode("utf-8") if svg is not None else None, env=env)


def render_background(env):
    source = (SOURCE / "background.svg").read_text(encoding="utf-8")
    mascot = (ROOT / "artwork" / "chem-grub.svg").read_text(encoding="utf-8")
    match = re.search(r"(<defs>.*?</defs>)\s*(<g\b.*</g>)\s*</svg>", mascot, re.S)
    image_tag = '<image x="1195" y="165" width="650" height="736" xlink:href="../artwork/chem-grub.svg"/>'
    if not match or image_tag not in source:
        raise ValueError("Could not compose the mascot into the background")
    artwork = f'<g transform="translate(1195 165) scale(0.8552631579)">{match.group(1)}{match.group(2)}</g>'
    combined = BUILD / "background.svg"
    combined.write_text(source.replace(image_tag, artwork), encoding="utf-8")
    render_svg(combined, BUILD / "background.png", 1920, 1080, env)


def build_icons(env):
    icons_dir = OUT / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for art_name, classes in ICON_ALIASES.items():
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">'
            '<rect x="1" y="1" width="30" height="30" rx="8" fill="#143832" stroke="#355d50"/>'
            f'<g fill="none" stroke="#c4e7b4" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICON_ART[art_name]}</g></svg>'
        )
        raw = BUILD / f"icon-{art_name}.png"
        render_svg(None, raw, 112, 112, env, svg=svg)
        with Image.open(raw) as image:
            icon = image.convert("RGBA").resize((28, 28), RESAMPLE)
            for class_name in classes:
                icon.save(icons_dir / f"{class_name}.png", optimize=True)
                count += 1
    return count


def build_slices():
    specs = {
        "select": (96, 48, 12, 4, 12, 4, 8, "#c4efb4", "#e0f8ce"),
        "menu": (128, 96, 14, 12, 14, 12, 18, (8, 30, 33, 246), "#2c5047"),
        "terminal": (128, 96, 16, 16, 16, 16, 14, (6, 24, 28, 253), "#3d6b5b"),
        "scrollbar_frame": (24, 48, 3, 3, 3, 3, 3, "#193a34", None),
        "scrollbar_thumb": (24, 48, 3, 3, 3, 3, 3, "#9ccb9a", None),
    }
    for prefix, (width, height, left, top, right, bottom, radius, fill, outline) in specs.items():
        scale = 4
        image = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        box = (0, 0, width * scale - 1, height * scale - 1)
        draw.rounded_rectangle(box, radius=radius * scale, fill=fill, outline=outline, width=scale if outline else 1)
        if prefix == "select":
            draw.rounded_rectangle((3 * scale, 12 * scale, 6 * scale, 36 * scale), radius=2 * scale, fill="#428b73")
        regions = {
            "nw": (0, 0, left, top),
            "n": (left, 0, width - right, top),
            "ne": (width - right, 0, width, top),
            "w": (0, top, left, height - bottom),
            "c": (left, top, width - right, height - bottom),
            "e": (width - right, top, width, height - bottom),
            "sw": (0, height - bottom, left, height),
            "s": (left, height - bottom, width - right, height),
            "se": (width - right, height - bottom, width, height),
        }
        for suffix, (x0, y0, x1, y1) in regions.items():
            tile = image.crop((x0 * scale, y0 * scale, x1 * scale, y1 * scale))
            target_width = left if suffix in ("nw", "w", "sw") else right if suffix in ("ne", "e", "se") else 1
            target_height = top if suffix in ("nw", "n", "ne") else bottom if suffix in ("sw", "s", "se") else 1
            tile.resize((target_width, target_height), RESAMPLE).save(OUT / f"{prefix}_{suffix}.png", optimize=True)


def pack_bitmap(mask):
    output = bytearray()
    value = 0
    bits = 0
    for pixel in mask.tobytes():
        value = (value << 1) | int(pixel >= 112)
        bits += 1
        if bits == 8:
            output.append(value)
            value = 0
            bits = 0
    if bits:
        output.append(value << (8 - bits))
    return bytes(output)


def section(name, payload):
    return name.encode("ascii") + struct.pack(">I", len(payload)) + payload


def build_font(size, filename):
    source = SOURCE / "fonts" / "NotoSansMonoCJKsc-Regular.otf"
    tt = TTFont(source, lazy=True)
    codepoints = sorted(cp for cp in tt.getBestCmap() if cp >= 32 and not 0xD800 <= cp <= 0xDFFF)
    tt.close()
    font = ImageFont.truetype(str(source), size, layout_engine=ImageFont.Layout.BASIC)
    ascent, descent = font.getmetrics()
    glyphs = []
    max_width = 1
    max_height = 1
    for codepoint in codepoints:
        char = chr(codepoint)
        bbox = font.getbbox(char)
        advance = max(0, int(round(font.getlength(char))))
        if not bbox or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            data = struct.pack(">HHhhh", 0, 0, 0, 0, advance)
        else:
            x0, y0, x1, y1 = bbox
            width, height = x1 - x0, y1 - y0
            mask = Image.new("L", (width, height), 0)
            ImageDraw.Draw(mask).text((-x0, -y0), char, font=font, fill=255)
            data = struct.pack(">HHhhh", width, height, x0, ascent - y1, advance) + pack_bitmap(mask)
            max_width = max(max_width, width)
            max_height = max(max_height, height)
        glyphs.append((codepoint, data))
    name = f"Noto Sans Mono CJK SC {size}".encode("utf-8")
    prefix = b"".join(
        (
            section("FILE", b"PFF2"),
            section("NAME", name),
            section("PTSZ", struct.pack(">H", size)),
            section("WEIG", b"normal"),
            section("MAXW", struct.pack(">H", max_width)),
            section("MAXH", struct.pack(">H", max_height)),
            section("ASCE", struct.pack(">H", ascent)),
            section("DESC", struct.pack(">H", descent)),
        )
    )
    data_start = len(prefix) + 8 + len(glyphs) * 9 + 8
    index = bytearray()
    data = bytearray()
    for codepoint, glyph in glyphs:
        index.extend(struct.pack(">IBI", codepoint, 0, data_start + len(data)))
        data.extend(glyph)
    payload = prefix + section("CHIX", bytes(index)) + section("DATA", bytes(data))
    destination = Path(filename)
    destination.write_bytes(payload)
    return len(glyphs)


class PF2Font:
    def __init__(self, path):
        self.path = Path(path)
        self.blob = self.path.read_bytes()
        self.index = {}
        sections = {}
        position = 0
        data_start = None
        data_length = None
        while position + 8 <= len(self.blob):
            tag = self.blob[position:position + 4].decode("ascii")
            length = struct.unpack_from(">I", self.blob, position + 4)[0]
            position += 8
            if position + length > len(self.blob):
                raise ValueError(f"Truncated PF2 section: {self.path}")
            if tag == "DATA":
                data_start, data_length = position, length
                break
            sections[tag] = self.blob[position:position + length]
            position += length
        if sections.get("FILE") != b"PFF2" or data_start is None:
            raise ValueError(f"Not a PFF2 font: {self.path}")
        self.name = sections["NAME"].decode("utf-8")
        self.size = struct.unpack(">H", sections["PTSZ"])[0]
        self.max_width = struct.unpack(">H", sections["MAXW"])[0]
        self.max_height = struct.unpack(">H", sections["MAXH"])[0]
        self.ascent = struct.unpack(">H", sections["ASCE"])[0]
        self.descent = struct.unpack(">H", sections["DESC"])[0]
        index = sections["CHIX"]
        if len(index) % 9:
            raise ValueError(f"Invalid PF2 character index: {self.path}")
        previous = -1
        expected = data_start
        for offset in range(0, len(index), 9):
            codepoint, flags, glyph_offset = struct.unpack_from(">IBI", index, offset)
            if codepoint <= previous or flags != 0 or glyph_offset != expected:
                raise ValueError(f"Invalid PF2 glyph offset: {self.path}")
            width, height, x, y, advance = struct.unpack_from(">HHhhh", self.blob, glyph_offset)
            if width > self.max_width or height > self.max_height:
                raise ValueError(f"Invalid PF2 glyph dimensions: {self.path}")
            expected = glyph_offset + 10 + (width * height + 7) // 8
            self.index[codepoint] = (glyph_offset, width, height, x, y, advance)
            previous = codepoint
        if expected != data_start + data_length or data_start + data_length != len(self.blob):
            raise ValueError(f"Invalid PF2 data length: {self.path}")

    @lru_cache(maxsize=512)
    def glyph(self, codepoint):
        offset, width, height, x, y, advance = self.index[codepoint]
        length = (width * height + 7) // 8
        bitmap = self.blob[offset + 10:offset + 10 + length]
        pixels = bytearray(width * height)
        for bit in range(width * height):
            if bitmap[bit // 8] & (0x80 >> (bit % 8)):
                pixels[bit] = 255
        return width, height, x, y, advance, Image.frombytes("L", (width, height), bytes(pixels))

    def width(self, text):
        return sum(self.index[ord(char)][5] for char in text)

    def draw(self, image, text, x, baseline, color, max_width=None):
        start = x
        right = x + max_width if max_width is not None else math.inf
        for char in text:
            width, height, offset_x, offset_y, advance, mask = self.glyph(ord(char))
            left = x + offset_x
            top = baseline - offset_y - height
            visible = min(width, int(right - left))
            if visible > 0 and height > 0:
                image.paste(color, (left, top), mask.crop((0, 0, visible, height)))
            x += advance
        return x - start


def component_properties(theme, component, occurrence=0):
    blocks = re.findall(rf"\+\s*{re.escape(component)}\s*\{{(.*?)\}}", theme, re.S)
    block = blocks[occurrence]
    values = re.findall(r"(\w+)\s*=\s*(?:\"([^\"]*)\"|([^\s;]+))", block)
    return {key: quoted or plain for key, quoted, plain in values}


def dimension(value, total):
    return int(float(value[:-1]) * total / 100) if value.endswith("%") else int(value)


def box_metrics(prefix):
    with Image.open(OUT / f"{prefix}_nw.png") as image:
        left, top = image.size
    with Image.open(OUT / f"{prefix}_se.png") as image:
        right, bottom = image.size
    return left, top, right, bottom


def draw_box(image, prefix, x, y, width, height):
    left, top, right, bottom = box_metrics(prefix)
    for suffix, dx, dy, w, h in (
        ("nw", 0, 0, left, top),
        ("n", left, 0, width - left - right, top),
        ("ne", width - right, 0, right, top),
        ("w", 0, top, left, height - top - bottom),
        ("c", left, top, width - left - right, height - top - bottom),
        ("e", width - right, top, right, height - top - bottom),
        ("sw", 0, height - bottom, left, bottom),
        ("s", left, height - bottom, width - left - right, bottom),
        ("se", width - right, height - bottom, right, bottom),
    ):
        if w <= 0 or h <= 0:
            continue
        with Image.open(OUT / f"{prefix}_{suffix}.png") as tile:
            resized = tile.convert("RGBA").resize((w, h), Image.Resampling.NEAREST)
            image.alpha_composite(resized, (x + dx, y + dy))


def draw_label(image, properties, font, canvas_size):
    width, height = canvas_size
    x = dimension(properties["left"], width)
    y = dimension(properties["top"], height)
    w = dimension(properties["width"], width)
    h = dimension(properties["height"], height)
    baseline = y + (h - font.ascent - font.descent) // 2 + font.ascent
    text_width = font.width(properties["text"])
    if properties.get("align") == "right":
        x += w - text_width
    elif properties.get("align") == "center":
        x += (w - text_width) // 2
    font.draw(image, properties["text"], x, baseline, properties["color"], max_width=w)


def draw_progress(image, properties, font, canvas_size):
    width, height = canvas_size
    x = dimension(properties["left"], width)
    y = dimension(properties["top"], height)
    w = dimension(properties["width"], width)
    h = dimension(properties["height"], height)
    draw = ImageDraw.Draw(image)
    draw.rectangle((x, y, x + w - 1, y + h - 1), fill=properties["border_color"])
    filled = (w - 2) // 2
    draw.rectangle((x + 1, y + 1, x + filled, y + h - 2), fill=properties["fg_color"])
    draw.rectangle((x + filled + 1, y + 1, x + w - 2, y + h - 2), fill=properties["bg_color"])
    text = properties.get("preview_text", "5s remaining.")
    baseline = y + (h - font.descent) // 2 + font.ascent // 2
    font.draw(image, text, x + (w - font.width(text)) // 2, baseline, properties["text_color"], max_width=w)


def visible_rows(menu, screen_height, with_scrollbar=False):
    del with_scrollbar
    _, menu_top, _, menu_bottom = box_metrics("menu")
    _, select_top, _, select_bottom = box_metrics("select")
    height = dimension(menu["height"], screen_height)
    step = int(menu["item_height"]) + int(menu["item_spacing"])
    available = height + int(menu["item_spacing"]) - 2 * int(menu["item_padding"])
    available -= select_top + select_bottom + menu_top + menu_bottom
    return available // step


def text_viewport(menu, screen_width, scrolling=True):
    width = dimension(menu["width"], screen_width)
    menu_left, _, menu_right, _ = box_metrics("menu")
    select_left, _, select_right, _ = box_metrics("select")
    width -= menu_left + menu_right + 2 * int(menu["item_padding"])
    if scrolling:
        width -= int(menu["scrollbar_width"]) + int(menu["scrollbar_left_pad"]) + int(menu["scrollbar_right_pad"])
    width -= select_left + select_right + int(menu["icon_width"]) + int(menu["item_icon_space"])
    return width


def draw_menu(image, entries, selected, fonts, canvas_size):
    screen_width, screen_height = canvas_size
    menu = component_properties((OUT / "theme.txt").read_text(encoding="utf-8"), "boot_menu")
    x = dimension(menu["left"], screen_width)
    y = dimension(menu["top"], screen_height)
    width = dimension(menu["width"], screen_width)
    height = dimension(menu["height"], screen_height)
    draw_box(image, "menu", x, y, width, height)
    menu_left, menu_top, menu_right, menu_bottom = box_metrics("menu")
    select_left, select_top, select_right, select_bottom = box_metrics("select")
    shown = visible_rows(menu, screen_height)
    scrolling = len(entries) > shown
    content_x = x + menu_left
    content_y = y + menu_top
    content_width = width - menu_left - menu_right
    if scrolling:
        content_width -= int(menu["scrollbar_width"]) + int(menu["scrollbar_left_pad"]) + int(menu["scrollbar_right_pad"])
    padding = int(menu["item_padding"])
    row_width = content_width - 2 * padding
    item_height = int(menu["item_height"])
    step = item_height + int(menu["item_spacing"])
    font = fonts[20]
    first_shown = max(0, selected - shown + 1)
    for row, (title, icon_name) in enumerate(entries[first_shown:first_shown + shown]):
        index = first_shown + row
        row_x = content_x + padding
        row_y = content_y + row * step
        is_selected = index == selected
        if is_selected:
            draw_box(image, "select", row_x, row_y, row_width, item_height + select_top + select_bottom)
        icon_x = row_x + select_left
        top_pad = select_top if is_selected else 0
        icon_y = row_y + top_pad + (item_height - int(menu["icon_height"])) // 2
        icon_path = OUT / "icons" / f"{icon_name}.png"
        if not icon_path.exists():
            icon_path = OUT / "icons" / "os.png"
        with Image.open(icon_path) as icon:
            image.alpha_composite(icon.convert("RGBA"), (icon_x, icon_y))
        baseline = row_y + top_pad + (item_height - font.ascent - font.descent) // 2 + font.ascent
        text_x = row_x + select_left + int(menu["icon_width"]) + int(menu["item_icon_space"])
        available = row_width - select_left - select_right - int(menu["icon_width"]) - int(menu["item_icon_space"])
        font.draw(image, title, text_x, baseline, menu["selected_item_color" if is_selected else "item_color"], max_width=available)
    if scrolling:
        track_x = x + width - menu_right - int(menu["scrollbar_right_pad"]) - int(menu["scrollbar_width"])
        track_y = y + menu_top + int(menu["scrollbar_top_pad"])
        track_height = height - menu_top - menu_bottom - int(menu["scrollbar_top_pad"]) - int(menu["scrollbar_bottom_pad"])
        draw_box(image, "scrollbar_frame", track_x, track_y, int(menu["scrollbar_width"]), track_height)
        thumb_height = max(24, track_height * shown // len(entries))
        thumb_y = track_y + (track_height - thumb_height) * first_shown // max(1, len(entries) - shown)
        draw_box(image, "scrollbar_thumb", track_x, thumb_y, int(menu["scrollbar_width"]), thumb_height)


def render_preview(entries, selected, size, destination, background, fonts, locale="en_US"):
    locales = json.loads((SOURCE / "preview-locales.json").read_text(encoding="utf-8"))
    strings = locales.get(locale, locales["en_US"])
    canvas = ImageOps.fit(background, size, method=RESAMPLE).convert("RGBA")
    theme = (OUT / "theme.txt").read_text(encoding="utf-8")
    draw_menu(canvas, entries, selected, fonts, size)
    progress = component_properties(theme, "progress_bar")
    progress["preview_text"] = strings["timeout"] % 5
    draw_progress(canvas, progress, fonts[18], size)
    footer = component_properties(theme, "label", 0)
    footer["text"] = strings["keymap"]
    draw_label(canvas, footer, fonts[18], size)
    title = strings["title"]
    title_color = re.search(r"^title-color:\s*\"([^\"]+)\"", theme, re.M).group(1)
    title_font = fonts[20]
    title_x = (size[0] - title_font.width(title)) // 2
    title_font.draw(canvas, title, title_x, 40 + title_font.ascent, title_color, max_width=size[0])
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(destination, optimize=True)


def validate_theme():
    theme_path = OUT / "theme.txt"
    if not theme_path.exists():
        raise FileNotFoundError("Theme is not built; run make first")
    theme = theme_path.read_text(encoding="utf-8")
    depth = 0
    quoted = False
    for char in theme:
        if char == '"':
            quoted = not quoted
        elif not quoted and char == "{":
            depth += 1
        elif not quoted and char == "}":
            depth -= 1
            if depth < 0:
                raise ValueError("Unbalanced theme braces")
    if depth or quoted:
        raise ValueError("Unbalanced theme syntax")
    fonts = {font.name: font for font in (PF2Font(path) for path in OUT.glob("*.pf2"))}
    expected_fonts = {"Noto Sans Mono CJK SC 20", "Noto Sans Mono CJK SC 18"}
    if set(fonts) != expected_fonts:
        raise ValueError(f"Unexpected theme fonts: {sorted(fonts)}")
    for name in expected_fonts:
        if f'"{name}"' not in theme:
            raise ValueError(f"Font is not referenced by theme: {name}")
    resources = re.findall(r"(?:desktop-image|terminal-box|menu_pixmap_style|selected_item_pixmap_style|scrollbar_frame|scrollbar_thumb|bar_style|highlight_style)\s*[:=]\s*\"([^\"]+)\"", theme)
    for resource in resources:
        if resource.startswith(("/", "..")):
            raise ValueError(f"Unsafe resource path: {resource}")
        matches = list(OUT.glob(resource)) if "*" in resource else [OUT / resource]
        if not matches or not all(path.is_file() for path in matches):
            raise ValueError(f"Missing theme resource: {resource}")
    for path in OUT.rglob("*.png"):
        with Image.open(path) as image:
            image.verify()
    font = fonts["Noto Sans Mono CJK SC 20"]
    tt = TTFont(SOURCE / "fonts" / "NotoSansMonoCJKsc-Regular.otf", lazy=True)
    expected_codepoints = {cp for cp in tt.getBestCmap() if cp >= 32 and not 0xD800 <= cp <= 0xDFFF}
    tt.close()
    for candidate in fonts.values():
        if set(candidate.index) != expected_codepoints:
            raise ValueError(f"Font does not contain the complete source cmap: {candidate.name}")
        if candidate.width("A") * 2 != candidate.width("化") or candidate.width("Ａ") != candidate.width("化"):
            raise ValueError(f"CJK and Latin advances are not in a 2:1 ratio: {candidate.name}")
    for char in "简体中文繁體中文快照內核內核高級選項高级选项化学启动項↑↓":
        if ord(char) not in font.index:
            raise ValueError(f"Missing required glyph: {char}")
    menu = component_properties(theme, "boot_menu")
    viewport = text_viewport(menu, 1280, scrolling=True)
    samples = ROOT_ENTRIES + BILINGUAL_ENTRIES + SNAPSHOT_ENTRIES + ARCH_ENTRIES
    reference = ImageFont.truetype(str(SOURCE / "fonts" / "NotoSansMonoCJKsc-Regular.otf"), 20, layout_engine=ImageFont.Layout.BASIC)
    for text, _ in samples:
        if font.width(text) != int(round(reference.getlength(text))):
            raise ValueError(f"PF2 and FreeType widths differ for: {text}")
    oversized = [(text, font.width(text)) for text, _ in samples if font.width(text) > viewport]
    if oversized:
        raise ValueError(f"Representative entries exceed {viewport}px: {oversized}")
    if visible_rows(menu, 720) < 7 or visible_rows(menu, 1080) < 10:
        raise ValueError("Too few visible entries for nested menus")
    footer = component_properties(theme, "label", 0)
    progress = component_properties(theme, "progress_bar")
    if "title-text:" in theme or footer["text"] != "@KEYMAP_SHORT@" or progress["text"] != "@TIMEOUT_NOTIFICATION_MIDDLE@":
        raise ValueError("Theme must use GRUB's native translated title and notification templates")
    if len(re.findall(r"\+\s*label\s*\{", theme)) != 1:
        raise ValueError("Unexpected fixed-language label in theme")
    locales = json.loads((SOURCE / "preview-locales.json").read_text(encoding="utf-8"))
    small_font = fonts["Noto Sans Mono CJK SC 18"]
    for locale, strings in locales.items():
        title = strings["title"]
        keymap = strings["keymap"]
        timeout = strings["timeout"] % 5
        for text, current in ((title, font), (keymap, small_font), (timeout, small_font)):
            missing = sorted({char for char in text if ord(char) not in current.index})
            if missing:
                raise ValueError(f"Missing glyphs for {locale}: {missing}")
        if font.width(title) > 1280 * 0.6:
            raise ValueError(f"Localized title exceeds its viewport: {locale}")
        if small_font.width(keymap) > dimension(footer["width"], 1280):
            raise ValueError(f"Localized footer exceeds its viewport: {locale}")
        if small_font.width(timeout) > dimension(progress["width"], 1280):
            raise ValueError(f"Localized timeout exceeds its viewport: {locale}")
    static_text = re.findall(r"<text\b[^>]*>([^<]*)</text>", (SOURCE / "background.svg").read_text(encoding="utf-8"))
    unexpected_text = set(static_text) - {"CHEMISTRY", "GRUB", "CHEM GRUB", "H", "O", "N"}
    if unexpected_text:
        raise ValueError(f"Fixed-language text remains in background: {sorted(unexpected_text)}")
    return {
        "glyphs": len(font.index),
        "icons": len(list((OUT / "icons").glob("*.png"))),
        "locales": len(locales),
        "rows_720": visible_rows(menu, 720),
        "rows_1080": visible_rows(menu, 1080),
        "viewport_1280": viewport,
        "widest_sample": max(font.width(text) for text, _ in samples),
    }


def build(reuse_fonts=False):
    if not shutil.which("rsvg-convert"):
        raise RuntimeError("rsvg-convert is required")
    BUILD.mkdir(exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    env = prepare_fontconfig()
    render_background(env)
    with Image.open(BUILD / "background.png") as image:
        image.convert("RGBA").save(OUT / "background.png", optimize=True)
    render_svg(ROOT / "artwork" / "chem-grub.svg", ROOT / "artwork" / "chem-grub.png", 1140, 1290, env)
    shutil.copy2(SOURCE / "theme.txt", OUT / "theme.txt")
    shutil.copy2(ROOT / "scripts" / "install.sh", OUT / "install.sh")
    (OUT / "install.sh").chmod(0o755)
    licenses = OUT / "licenses"
    licenses.mkdir()
    for path in (SOURCE / "fonts").glob("*OFL.txt"):
        shutil.copy2(path, licenses / path.name)
    build_icons(env)
    build_slices()
    font_cache = BUILD / "pf2"
    font_cache.mkdir(exist_ok=True)
    for size, filename in FONT_SPECS:
        cached = font_cache / filename
        if reuse_fonts and cached.exists():
            shutil.copy2(cached, OUT / filename)
            continue
        count = build_font(size, cached)
        shutil.copy2(cached, OUT / filename)
        print(f"Built {filename}: {count:,} glyphs", flush=True)
    fonts = {20: PF2Font(OUT / FONT_SPECS[0][1]), 18: PF2Font(OUT / FONT_SPECS[1][1])}
    with Image.open(OUT / "background.png") as background:
        render_preview(ROOT_ENTRIES, 0, (1920, 1080), ROOT / "preview.png", background, fonts, "en_US")
        render_preview(SNAPSHOT_ENTRIES, 1, (1280, 720), ROOT / "preview-nested.png", background, fonts, "zh_CN")
        render_preview(ARCH_ENTRIES, 7, (1280, 720), ROOT / "preview-arch.png", background, fonts, "en_US")
        render_preview(ROOT_ENTRIES, 0, (1280, 720), ROOT / "preview-de.png", background, fonts, "de_DE")
        locales = json.loads((SOURCE / "preview-locales.json").read_text(encoding="utf-8"))
        for locale in locales:
            render_preview(ROOT_ENTRIES, 0, (1280, 720), BUILD / "locales" / f"{locale}.png", background, fonts, locale)
    stats = validate_theme()
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(OUT.rglob("*")):
            if path.is_file():
                archive.write(path, Path("chem-grub") / path.relative_to(OUT))
    with zipfile.ZipFile(ARCHIVE) as archive:
        if archive.testzip() is not None:
            raise ValueError("Theme archive failed its CRC check")
    print(
        f"Verified {stats['icons']} icons, {stats['glyphs']:,} font glyphs; "
        f"{stats['rows_720']} rows at 720p, {stats['rows_1080']} rows at 1080p; "
        f"widest sample {stats['widest_sample']}/{stats['viewport_1280']}px at 1280px",
        flush=True,
    )
    print(f"Created {ARCHIVE.relative_to(ROOT)} ({ARCHIVE.stat().st_size / 1024 / 1024:.1f} MiB)", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Build and validate the Chemistry GRUB theme")
    parser.add_argument("--verify", action="store_true", help="validate the existing deliverable without rebuilding")
    parser.add_argument("--reuse-fonts", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.verify:
        stats = validate_theme()
        print(f"Theme validation passed: {stats}")
        return
    build(args.reuse_fonts)


if __name__ == "__main__":
    main()
