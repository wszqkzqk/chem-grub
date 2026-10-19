# Arch Linux packaging

`PKGBUILD` builds the theme from the parent source tree and installs the
complete theme under `/boot/grub/themes/chem-grub`. It does not change the
bootloader configuration during package installation.

## Build and install a package

Install the build tools, then run:

```sh
sudo pacman -S --needed base-devel git make librsvg python python-pillow python-fonttools grub
cd archlinux
makepkg --syncdeps --cleanbuild
sudo pacman -U ./chem-grub-*.pkg.tar.zst
```

`makepkg` runs `make` and `make check`, including the CJK font and localization
validation. `package()` uses `make install DESTDIR="${pkgdir}"` for a staged
installation; it never invokes the host configurator. The package is
architecture-independent (`any`). Its version is generated as
`r<commit-count>.<yyyymmdd>.<short-sha>`, so no release tags are required.

After installing the package, either enable the theme with the included
installer:

```sh
sudo /boot/grub/themes/chem-grub/install.sh
```

or set the following in `/etc/default/grub` and regenerate the configuration:

```sh
GRUB_THEME="/boot/grub/themes/chem-grub/theme.txt"
```

```sh
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

Review `/etc/default/grub` before rebooting. Existing Arch kernel entries and
grub-btrfs configuration are not replaced by the package.
