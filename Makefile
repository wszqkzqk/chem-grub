# Copyright (C) 2026 Zhou Qiankang <wszqkzqk@qq.com>
# SPDX-License-Identifier: GPL-2.0-or-later

PYTHON ?= python3
INSTALL ?= install
GRUB_DIR ?= /boot/grub
PREFIX ?= /usr

.PHONY: all build check docs install clean

all: build

build:
	$(PYTHON) scripts/build.py

check: build
	$(PYTHON) scripts/build.py --verify

docs: build
	mkdir -p docs/images
	cp preview.png docs/images/preview.png
	cp preview-nested.png docs/images/preview-zh_CN.png
	cp preview-de.png docs/images/preview-de.png
	cp preview-arch.png docs/images/preview-arch.png
	cp artwork/chem-grub.png docs/images/mascot.png

install: build
	if [ -n "$(DESTDIR)" ]; then \
		$(INSTALL) -d "$(DESTDIR)$(GRUB_DIR)/themes/chem-grub" "$(DESTDIR)$(PREFIX)/share/licenses/chem-grub" "$(DESTDIR)$(PREFIX)/share/doc/chem-grub"; \
		cp -a dist/chem-grub/. "$(DESTDIR)$(GRUB_DIR)/themes/chem-grub/"; \
		$(INSTALL) -m 644 LICENSE NOTICE "$(DESTDIR)$(PREFIX)/share/licenses/chem-grub/"; \
		$(INSTALL) -m 644 README.md README.zh-CN.md "$(DESTDIR)$(PREFIX)/share/doc/chem-grub/"; \
		$(INSTALL) -m 644 docs/VALIDATION.md "$(DESTDIR)$(PREFIX)/share/doc/chem-grub/"; \
	else \
		sh scripts/install.sh; \
	fi

clean:
	$(RM) -r .build dist preview.png preview-nested.png preview-arch.png preview-de.png artwork/chem-grub.png
