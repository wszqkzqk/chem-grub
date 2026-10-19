# Contributing to Chemistry GRUB

Thank you for helping improve the theme. Please keep changes focused and
preserve the ability to build the complete theme from source.

## Development setup

Install Python 3, `rsvg-convert` (from librsvg), GNU Make, and the Python
requirements:

```sh
python3 -m pip install -r requirements.txt
make check
```

The font files are included with their licenses; a build does not need to
download fonts.

## Making changes

1. Open an issue for a significant visual or compatibility change.
2. Create a topic branch from `main`.
3. Edit source files under `src/` or `artwork/`, not generated files in `dist/`.
4. Run `make check`. Run `make docs` when the rendered appearance changes.
   For changes under `archlinux/`, also run `makepkg --syncdeps --cleanbuild`
   from that directory on Arch Linux or in an Arch container.
5. Review the generated previews at 1280×720 and 1920×1080, then submit a pull
   request with a clear description and screenshots when appropriate.

The generated `dist/` directory and root-level preview PNGs are intentionally
ignored. The approved reference images live in `docs/images/` and are updated
with `make docs`.

## Compatibility guidelines

- Use GRUB's native translation placeholders for title, key help, and timeout
  text. Do not replace them with fixed bilingual labels.
- Keep the background free of untranslated slogans; brand names are allowed.
- Test long Latin and CJK entries, nested submenus, and scrolling. Do not change
  Arch or grub-btrfs generator scripts as part of a theme change.
- Preserve font names, glyph coverage, and license notices when updating fonts.
- Keep installation changes reversible and preserve the existing backup and
  dry-run behavior. Never require a user's real boot configuration for a test.
- Use `make install DESTDIR=...` for staged package installs; keep host
  enablement in `scripts/install.sh`.

## Bug reports

Include the distribution, GRUB version, firmware type (BIOS or UEFI), screen
resolution, GRUB language, and a screenshot or exact error text when available.
Do not attach private keys, credentials, or complete disk identifiers.

By contributing, you agree that your contributions may be distributed under the
project's GNU General Public License v2 or later (GPL-2.0-or-later), subject to third-party font licenses.
