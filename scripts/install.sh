#!/bin/sh
# Copyright (C) 2026 Zhou Qiankang <wszqkzqk@qq.com>
# SPDX-License-Identifier: GPL-2.0-or-later
set -eu

PROGRAM=${0##*/}
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -f "$SCRIPT_DIR/theme.txt" ]; then
  SOURCE_DIR=$SCRIPT_DIR
elif [ -f "$SCRIPT_DIR/../dist/chem-grub/theme.txt" ]; then
  SOURCE_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../dist/chem-grub" && pwd)
else
  printf '%s: built theme not found; run make first\n' "$PROGRAM" >&2
  exit 1
fi

if [ -d /boot/grub ] || [ -f /boot/grub/grub.cfg ]; then
  GRUB_ROOT=/boot/grub
elif [ -d /boot/grub2 ] || [ -f /boot/grub2/grub.cfg ]; then
  GRUB_ROOT=/boot/grub2
else
  GRUB_ROOT=/boot/grub
fi
TARGET_DIR=$GRUB_ROOT/themes/chem-grub
DEFAULTS_FILE=/etc/default/grub
GRUB_CONFIG=$GRUB_ROOT/grub.cfg
COPY_ONLY=0
DRY_RUN=0

usage() {
  cat <<EOF
Usage: $PROGRAM [options]

Install Chemistry GRUB, enable it, and regenerate the GRUB configuration.

Options:
  --target DIR       Theme directory (default: $TARGET_DIR)
  --defaults FILE    GRUB defaults file (default: /etc/default/grub)
  --grub-config FILE Generated GRUB configuration (default: $GRUB_CONFIG)
  --copy-only        Copy files without changing GRUB configuration
  --dry-run          Show the installation plan without changing files
  -h, --help         Show this help
EOF
}

fail() {
  printf '%s: %s\n' "$PROGRAM" "$*" >&2
  exit 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target|--defaults|--grub-config)
      [ "$#" -ge 2 ] || fail "$1 requires a path"
      case "$1" in
        --target) TARGET_DIR=$2 ;;
        --defaults) DEFAULTS_FILE=$2 ;;
        --grub-config) GRUB_CONFIG=$2 ;;
      esac
      shift 2
      ;;
    --copy-only)
      COPY_ONLY=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown option: $1"
      ;;
  esac
done

case "$TARGET_DIR" in
  /*) ;;
  *) fail "target must be an absolute path" ;;
esac
case "$TARGET_DIR" in
  *[!A-Za-z0-9_./-]*) fail "target may contain only letters, digits, dots, slashes, underscores, and hyphens" ;;
esac
case "$TARGET_DIR" in
  "$SOURCE_DIR"/*) fail "target cannot be inside the source theme" ;;
esac

for required in theme.txt background.png NotoSansMonoCJKsc-Regular-20.pf2 NotoSansMonoCJKsc-Regular-18.pf2 icons/snapshots.png; do
  [ -f "$SOURCE_DIR/$required" ] || fail "incomplete theme: missing $required"
done

if [ "$COPY_ONLY" -eq 0 ] && [ "$DRY_RUN" -eq 0 ]; then
  [ -f "$DEFAULTS_FILE" ] || fail "GRUB defaults file not found: $DEFAULTS_FILE"
  [ -w "$DEFAULTS_FILE" ] || fail "permission denied; rerun with sudo"
  if [ -z "${CHEM_GRUB_MKCONFIG:-}" ] && ! command -v grub-mkconfig >/dev/null 2>&1 \
    && ! command -v grub2-mkconfig >/dev/null 2>&1 && ! command -v update-grub >/dev/null 2>&1; then
    fail "grub-mkconfig, grub2-mkconfig, or update-grub is required"
  fi
fi

printf 'Source:  %s\nTarget:  %s\n' "$SOURCE_DIR" "$TARGET_DIR"
if [ "$DRY_RUN" -eq 1 ]; then
  printf 'Would copy the complete theme.\n'
  if [ "$COPY_ONLY" -eq 0 ]; then
    printf 'Would back up and update %s with GRUB_THEME="%s/theme.txt".\n' "$DEFAULTS_FILE" "$TARGET_DIR"
    printf 'Would back up %s if present and regenerate it.\n' "$GRUB_CONFIG"
  fi
  exit 0
fi

if [ "$SOURCE_DIR" != "$TARGET_DIR" ]; then
  mkdir -p "$TARGET_DIR" || fail "cannot create target; rerun with sudo"
  cp -R "$SOURCE_DIR/." "$TARGET_DIR/" || fail "could not copy theme files"
  printf 'Copied Chemistry GRUB to %s\n' "$TARGET_DIR"
else
  printf 'Theme is already installed at %s\n' "$TARGET_DIR"
fi

if [ "$COPY_ONLY" -eq 1 ]; then
  printf 'Set GRUB_THEME="%s/theme.txt" in %s, then regenerate your GRUB configuration.\n' "$TARGET_DIR" "$DEFAULTS_FILE"
  exit 0
fi

TIMESTAMP=$(date +%Y%m%d%H%M%S)-$$
DEFAULTS_BACKUP=$DEFAULTS_FILE.chem-grub.$TIMESTAMP.bak
TEMP_DEFAULTS=$DEFAULTS_FILE.chem-grub.$TIMESTAMP.tmp
cp -p "$DEFAULTS_FILE" "$DEFAULTS_BACKUP"
cp -p "$DEFAULTS_FILE" "$TEMP_DEFAULTS"
awk -v theme="$TARGET_DIR/theme.txt" '
  BEGIN { replaced = 0 }
  /^[[:space:]]*#?[[:space:]]*GRUB_THEME[[:space:]]*=/ {
    if (!replaced) print "GRUB_THEME=\"" theme "\""
    replaced = 1
    next
  }
  { print }
  END { if (!replaced) print "GRUB_THEME=\"" theme "\"" }
' "$DEFAULTS_FILE" > "$TEMP_DEFAULTS"
mv "$TEMP_DEFAULTS" "$DEFAULTS_FILE"
printf 'Updated %s (backup: %s)\n' "$DEFAULTS_FILE" "$DEFAULTS_BACKUP"

if awk '/^[[:space:]]*GRUB_TERMINAL(_OUTPUT)?[[:space:]]*=[[:space:]]*"?console/ { found = 1 } END { exit !found }' "$DEFAULTS_FILE"; then
  printf 'Warning: GRUB terminal output is forced to console; set GRUB_TERMINAL_OUTPUT=gfxterm to display the theme.\n' >&2
fi

if [ -f "$GRUB_CONFIG" ]; then
  CONFIG_BACKUP=$GRUB_CONFIG.chem-grub.$TIMESTAMP.bak
  cp -p "$GRUB_CONFIG" "$CONFIG_BACKUP"
  printf 'Backed up %s to %s\n' "$GRUB_CONFIG" "$CONFIG_BACKUP"
fi

if [ -n "${CHEM_GRUB_MKCONFIG:-}" ]; then
  "$CHEM_GRUB_MKCONFIG" -o "$GRUB_CONFIG"
elif command -v grub-mkconfig >/dev/null 2>&1; then
  grub-mkconfig -o "$GRUB_CONFIG"
elif command -v grub2-mkconfig >/dev/null 2>&1; then
  grub2-mkconfig -o "$GRUB_CONFIG"
else
  update-grub
fi

printf 'Chemistry GRUB is enabled. Your existing boot entries, Arch kernel submenus, and grub-btrfs snapshots were left unchanged.\n'
