#!/usr/bin/env python3
"""Automated Debian (.deb) package generator for MsmLogo."""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent
BUILD_DIR = PROJECT_ROOT / "build" / "deb"
DIST_DIR = PROJECT_ROOT / "dist"

PKG_NAME = "msmlogo"
PKG_VERSION = "1.0.1"
PKG_ARCH = "amd64"
DEB_NAME = f"{PKG_NAME}_{PKG_VERSION}_{PKG_ARCH}.deb"
STAGE_DIR = BUILD_DIR / f"{PKG_NAME}_{PKG_VERSION}_{PKG_ARCH}"


def clean():
    """Remove previous build staging and dist artifacts."""
    print("🧹 Cleaning previous build directories...")
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def copy_tree_filtered(src: Path, dst: Path):
    """Copy directory tree excluding caches and test files."""
    def ignore_patterns(path, names):
        ignored = []
        for name in names:
            if name in ("__pycache__", ".pytest_cache", ".vscode", ".git"):
                ignored.append(name)
            elif name.endswith((".pyc", ".pyo", ".log")):
                ignored.append(name)
        return ignored

    shutil.copytree(src, dst, ignore=ignore_patterns, dirs_exist_ok=True)


def generate_icons():
    """Generate multi-resolution icons from source app_icon.png."""
    print("🎨 Generating hicolor icon suite...")
    src_icon = PROJECT_ROOT / "assets" / "icons" / "app_icon.png"
    src_svg = PROJECT_ROOT / "assets" / "icons" / "app_icon.svg"

    if not src_icon.exists():
        raise FileNotFoundError(f"Source icon not found at {src_icon}")

    img = Image.open(src_icon)

    resolutions = [48, 64, 128, 256, 512]
    for res in resolutions:
        icon_dir = STAGE_DIR / "usr" / "share" / "icons" / "hicolor" / f"{res}x{res}" / "apps"
        icon_dir.mkdir(parents=True, exist_ok=True)
        dest_png = icon_dir / f"{PKG_NAME}.png"
        resized = img.resize((res, res), Image.Resampling.LANCZOS)
        resized.save(dest_png, format="PNG")

    # SVG scalable icon
    if src_svg.exists():
        scalable_dir = STAGE_DIR / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
        scalable_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(src_svg, scalable_dir / f"{PKG_NAME}.svg")

    # Pixmaps fallback
    pixmaps_dir = STAGE_DIR / "usr" / "share" / "pixmaps"
    pixmaps_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_icon, pixmaps_dir / f"{PKG_NAME}.png")
    if src_svg.exists():
        shutil.copy(src_svg, pixmaps_dir / f"{PKG_NAME}.svg")


def assemble_package():
    """Assemble the file system hierarchy for /opt/msmlogo and /usr."""
    print("📦 Assembling application files into /opt/msmlogo...")
    opt_dir = STAGE_DIR / "opt" / PKG_NAME
    opt_dir.mkdir(parents=True, exist_ok=True)

    # 1. Application code
    copy_tree_filtered(PROJECT_ROOT / "msmlogo", opt_dir / "msmlogo")
    # 2. Assets
    copy_tree_filtered(PROJECT_ROOT / "assets", opt_dir / "assets")
    # 3. Libs fallback (e.g. libxcb-cursor)
    if (PROJECT_ROOT / "libs").exists():
        copy_tree_filtered(PROJECT_ROOT / "libs", opt_dir / "libs")

    # 4. Launcher script in /usr/bin/msmlogo
    print("🚀 Creating launcher script in /usr/bin/msmlogo...")
    bin_dir = STAGE_DIR / "usr" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    launcher = bin_dir / PKG_NAME
    launcher_content = """#!/usr/bin/env bash
# MsmLogo Boot Manager Launcher
set -e

APP_DIR="/opt/msmlogo"
export LD_LIBRARY_PATH="$APP_DIR/libs:$LD_LIBRARY_PATH"
export PYTHONPATH="$APP_DIR:$PYTHONPATH"

# Prefer system python3
PYTHON_BIN="/usr/bin/python3"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="$(command -v python3 || true)"
fi

exec "$PYTHON_BIN" "$APP_DIR/msmlogo/main.py" "$@"
"""
    launcher.write_text(launcher_content, encoding="utf-8")
    launcher.chmod(0o755)

    # 5. Desktop entry
    print("🖥️  Creating desktop entry in /usr/share/applications...")
    apps_dir = STAGE_DIR / "usr" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = apps_dir / f"{PKG_NAME}.desktop"
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=MsmLogo
GenericName=Linux Boot Logo Manager & Creator
Comment=Create, customize and apply Plymouth Boot Logos and GRUB backgrounds
Exec=/usr/bin/{PKG_NAME}
Icon={PKG_NAME}
Terminal=false
Categories=System;Settings;Utility;
Keywords=plymouth;boot;logo;grub;splash;initramfs;
StartupNotify=true
"""
    desktop_file.write_text(desktop_content, encoding="utf-8")
    desktop_file.chmod(0o644)

    # 6. Polkit Policy
    print("🔒 Installing PolicyKit policy...")
    policy_dir = STAGE_DIR / "usr" / "share" / "polkit-1" / "actions"
    policy_dir.mkdir(parents=True, exist_ok=True)
    policy_src = PROJECT_ROOT / "msmlogo" / "data" / "org.msmlogo.policy"
    if policy_src.exists():
        shutil.copy(policy_src, policy_dir / "org.msmlogo.policy")
        (policy_dir / "org.msmlogo.policy").chmod(0o644)


def create_debian_control():
    """Generate DEBIAN/control, postinst, and postrm files."""
    print("📝 Generating DEBIAN metadata and maintenance scripts...")
    debian_dir = STAGE_DIR / "DEBIAN"
    debian_dir.mkdir(parents=True, exist_ok=True)

    # Calculate installed size in KB
    total_size = sum(f.stat().st_size for f in STAGE_DIR.rglob("*") if f.is_file())
    installed_size_kb = (total_size + 1023) // 1024

    control_content = f"""Package: {PKG_NAME}
Version: {PKG_VERSION}
Section: utils
Priority: optional
Architecture: {PKG_ARCH}
Maintainer: AttitudeTopHacker <aattitudetophacker@gmail.com>
Installed-Size: {installed_size_kb}
Depends: python3 (>= 3.8), python3-pyqt6, python3-pil, plymouth, policykit-1 | polkitd, libxcb-cursor0 | libc6
Recommends: grub2-common, initramfs-tools | dracut
Homepage: https://github.com/AttitudeTopHacker/msmdownloader
Description: Modern Plymouth Boot Logo & GRUB Background Creator and Manager
 MsmLogo is a lightweight and user-friendly GUI tool to create,
 customize and 1-Click apply Plymouth boot splash themes and GRUB
 backgrounds on Linux distributions with live preview and safe fallback.
"""
    (debian_dir / "control").write_text(control_content, encoding="utf-8")
    (debian_dir / "control").chmod(0o644)

    # postinst
    postinst_content = """#!/bin/sh
set -e

if [ "$1" = "configure" ]; then
    chmod 755 /usr/bin/msmlogo
    if [ -f /usr/share/applications/msmlogo.desktop ]; then
        chmod 644 /usr/share/applications/msmlogo.desktop
    fi
    if [ -f /usr/share/polkit-1/actions/org.msmlogo.policy ]; then
        chmod 644 /usr/share/polkit-1/actions/org.msmlogo.policy
    fi

    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database -q /usr/share/applications || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
    fi
fi

exit 0
"""
    postinst_file = debian_dir / "postinst"
    postinst_file.write_text(postinst_content, encoding="utf-8")
    postinst_file.chmod(0o755)

    # postrm
    postrm_content = """#!/bin/sh
set -e

if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    # Completely clean runtime python bytecode cache and app directory
    rm -rf /opt/msmlogo

    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database -q /usr/share/applications || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
    fi
fi

if [ "$1" = "purge" ]; then
    # Remove backup and grub config if user explicitly purged the package
    rm -f /etc/msmlogo_backup.json
    rm -f /etc/default/grub.d/99_msmlogo.cfg
fi

exit 0
"""
    postrm_file = debian_dir / "postrm"
    postrm_file.write_text(postrm_content, encoding="utf-8")
    postrm_file.chmod(0o755)


def set_permissions():
    """Set standard permissions across all staged files."""
    for root, dirs, files in os.walk(STAGE_DIR):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            path = os.path.join(root, f)
            if "DEBIAN/postinst" in path or "DEBIAN/postrm" in path or "/usr/bin/" in path:
                os.chmod(path, 0o755)
            else:
                os.chmod(path, 0o644)


def build_deb():
    """Execute dpkg-deb to package the directory."""
    target_deb = DIST_DIR / DEB_NAME
    print(f"🔨 Building {target_deb.name} with dpkg-deb...")

    cmd = ["dpkg-deb", "--build", "--root-owner-group", str(STAGE_DIR), str(target_deb)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ dpkg-deb failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)

    size_mb = target_deb.stat().st_size / (1024 * 1024)
    print(f"✅ Successfully built: {target_deb} ({size_mb:.2f} MB)")
    return target_deb


def verify_deb(deb_path: Path):
    """Verify and print contents of the newly built deb package."""
    print("\n🔍 Package Information:")
    subprocess.run(["dpkg-deb", "-I", str(deb_path)])
    print("\n📋 Package File Manifest:")
    subprocess.run(["dpkg-deb", "-c", str(deb_path)])


def main():
    clean()
    generate_icons()
    assemble_package()
    create_debian_control()
    set_permissions()
    deb_path = build_deb()
    verify_deb(deb_path)


if __name__ == "__main__":
    main()
