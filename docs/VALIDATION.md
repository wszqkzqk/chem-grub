# Validation guide

`make check` is a static validation step. It checks the theme structure,
resources, PF2 fonts, native localization placeholders, and representative text
widths. It does not prove that a particular GRUB build can render the theme.

`grub-script-check` checks GRUB scripts such as `grub.cfg`; it does not parse
`theme.txt`. The definitive test is to boot a disposable GRUB rescue image in a
virtual machine and exercise the menu.

## Build a disposable test image

Run these commands on a Linux test machine with `grub-mkrescue`, `xorriso`, and
QEMU installed. The test entries execute `true`; no operating system or disk is
booted.

```sh
work=$(mktemp -d)
mkdir -p "$work/boot/grub/themes"
cp -a dist/chem-grub "$work/boot/grub/themes/"
```

Create `$work/boot/grub/grub.cfg` with the following content:

```grub
set timeout=30
set default=0

insmod all_video
insmod gfxterm
insmod gfxmenu
insmod png

loadfont (cd0)/boot/grub/themes/chem-grub/NotoSansMonoCJKsc-Regular-20.pf2
loadfont (cd0)/boot/grub/themes/chem-grub/NotoSansMonoCJKsc-Regular-18.pf2

set gfxmode=1280x720
load_video
terminal_output gfxterm

set theme=(cd0)/boot/grub/themes/chem-grub/theme.txt
export theme

menuentry "English test" --class arch {
  true
}

submenu "Advanced options / 高级选项" {
  menuentry "中文启动项 / linux-hardened fallback" --class snapshots {
    true
  }
}
```

Then run:

```sh
grub-script-check "$work/boot/grub/grub.cfg"
grub-mkrescue -o /tmp/chem-grub.iso "$work"
qemu-system-x86_64 -m 512 -cdrom /tmp/chem-grub.iso -boot d -vga std
```

The script check validates the test configuration. The theme itself is
validated by what GRUB renders in QEMU. Repeat with an OVMF firmware image to
cover UEFI as well as BIOS.

## Check the rendered behavior

- The background and mascot load without missing-resource or font errors.
- Long entries, selection, icons, and the scrollbar render correctly.
- Enter opens a submenu and Esc returns to the parent menu.
- The `e` editor and `c` command line remain usable.
- The timeout bar appears and counts down.
- Localized title, help, and timeout text fit their regions.

## Test localization

GRUB translations are read from its locale files. Copy the appropriate
`grub.mo` into the test image, for example:

```sh
mkdir -p "$work/boot/grub/locale"
cp /usr/share/locale/zh_CN/LC_MESSAGES/grub.mo \
  "$work/boot/grub/locale/zh_CN.mo"
```

The source path can vary by distribution. Add these lines to the test
`grub.cfg`, then rebuild the image:

```grub
insmod gettext
set locale_dir=(cd0)/boot/grub/locale
set lang=zh_CN
```

Change the locale and rebuild for other languages. If a translation is missing,
GRUB may fall back to English; that is expected and is different from a missing
font glyph.
