# Chemistry GRUB

[![CI](https://github.com/wszqkzqk/chem-grub/actions/workflows/ci.yml/badge.svg)](https://github.com/wszqkzqk/chem-grub/actions/workflows/ci.yml)
[![许可证：GPLv2+](https://img.shields.io/badge/license-GPLv2%2B-blue.svg)](LICENSE)

一套以化学实验室为主题的 GRUB2 主题。吉祥物 **Chem Grub** 是一只戴护目镜、
穿实验服、抱着冒泡锥形瓶的幼虫。

![Chemistry GRUB 预览](docs/images/preview.png)

[English README](README.md) · [贡献指南](CONTRIBUTING.md) ·
[验证指南](docs/VALIDATION.md)

## 特性

- **原创矢量吉祥物**：可编辑的 SVG 原稿与午夜实验室背景。
- **GRUB 原生多语言**：默认菜单标题、`@KEYMAP_SHORT@` 和
  `@TIMEOUT_NOTIFICATION_MIDDLE@` 使用 GRUB 自己的翻译，随 `$lang` 和语言
  文件切换；没有翻译时回退英文。启动项名称仍由系统和生成脚本决定。
- **中英文字体**：两种尺寸的 Noto Sans Mono CJK SC PF2，每种包含 44,810 个
  字形，构建时检查英文半宽、中文全宽及混排宽度，也覆盖日文、韩文等字符。
- **复杂菜单**：支持 Arch 多内核高级选项和 grub-btrfs 嵌套快照目录；
  720p 显示 7 行、1080p 显示 11 行，更多条目通过滚动查看。
- **完整资源**：76 个分类图标、菜单与选中框九宫格、倒计时样式和终端字体。

主题不会修改 Arch 或 grub-btrfs 的生成脚本。

## 安装

### 使用主题压缩包

下载自动更新的 [最新开发构建](https://github.com/wszqkzqk/chem-grub/releases/tag/latest)，解压后运行：

```sh
sudo ./chem-grub/install.sh
```

安装器会检测 `/boot/grub` 或 `/boot/grub2`，复制主题，备份
`/etc/default/grub` 和已有的生成配置，启用主题并重新生成 GRUB 配置，
不会改动已有启动项。

常用选项：

```sh
./chem-grub/install.sh --dry-run
./chem-grub/install.sh --copy-only
./chem-grub/install.sh --help
```

### 从源码构建

安装 Python 3、GNU Make、`rsvg-convert`（librsvg）和 Python 依赖：

```sh
python3 -m pip install -r requirements.txt
make
sudo sh scripts/install.sh
```

`make` 会生成 `dist/chem-grub/` 和 `dist/chem-grub.zip`。

### Arch Linux 软件包

项目提供 Arch `PKGBUILD` 和 Arch Linux CI。本地构建软件包：

```sh
cd archlinux
makepkg --syncdeps --cleanbuild
sudo pacman -U ./chem-grub-*.pkg.tar.zst
sudo /boot/grub/themes/chem-grub/install.sh
```

软件包只安装文件，是否启用主题由你明确执行安装器或修改配置决定。
详见 [archlinux/README.md](archlinux/README.md)。

手动配置已复制的主题时，在 `/etc/default/grub` 中设置：

```sh
GRUB_THEME="/boot/grub/themes/chem-grub/theme.txt"
```

然后使用发行版的命令重新生成配置，例如 Arch Linux：

```sh
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

不要强制设置 `GRUB_TERMINAL_OUTPUT=console`，主题需要图形终端。

## 开发与检查

```sh
make          # 构建主题、预览和压缩包
make check    # 构建并运行全部静态检查
make docs     # 更新 docs/images/ 中的参考图
make clean    # 删除生成文件
```

`make check` 会检查资源、PF2 数据、字体宽度、多语言占位符和长条目，但
**不等于实际启动验证**。不需要真实操作系统的 QEMU 验证方法见
[验证指南](docs/VALIDATION.md)。

## 目录

```text
artwork/             吉祥物 SVG 原稿
src/                 背景、主题、字体和预览翻译
scripts/             构建与安装脚本
archlinux/           Arch Linux PKGBUILD 与打包说明
docs/                社区文档与参考图片
.github/             CI 和贡献模板
dist/                构建产物，不提交到 Git
```

## 社区与许可证

欢迎提交 Issue 和 Pull Request，请先阅读
[贡献指南](CONTRIBUTING.md) 和 [行为准则](CODE_OF_CONDUCT.md)。

项目代码和原创图形采用 [GNU General Public License v2 或更高版本（GPL-2.0-or-later）](LICENSE)。
版权署名：Copyright (C) 2026 Zhou Qiankang <wszqkzqk@qq.com>。
随附字体使用 SIL Open Font License，详见 [NOTICE](NOTICE) 和 `src/fonts/` 中的许可证文件。
