# Copyright (C) 2026 Zhou Qiankang <wszqkzqk@qq.com>
# SPDX-License-Identifier: GPL-2.0-or-later

PYTHON ?= python3

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
	sh scripts/install.sh

clean:
	$(RM) -r .build dist preview.png preview-nested.png preview-arch.png preview-de.png artwork/chem-grub.png
